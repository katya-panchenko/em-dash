"""Deterministic scoring + discard rules.

    raw   = 0.35*local_coverage_gap + 0.30*corroboration + 0.20*velocity + 0.15*commercial_proof
    final = raw * (transfer_score / 100)          # transfer_score set by enrich.py
    confidence = high (>=3 source types + gap) | medium (2) | low (trend-only)

Transparent and tunable — the rankings are defensible to a jury, while Claude
supplies the transfer judgment (enrich.py). Two-phase: compute_features() runs
before enrichment; finalize() applies transfer_score + discard rules after.
"""

from __future__ import annotations

from src.schema import Confidence, CoverageStatus, Opportunity, SourceType
from src.scenario import ScenarioProfile

WEIGHTS = {"local_coverage_gap": 0.35, "corroboration": 0.30, "velocity": 0.20, "commercial_proof": 0.15}


def compute_features(opp: Opportunity, scenario: ScenarioProfile) -> None:
    """Set deterministic features, coverage_status, raw_score, confidence."""
    local_names = {c.name.lower() for c in scenario.local_competitors}
    ref_names = {r.name.lower() for r in scenario.reference_retailers}
    comp = [s for s in opp.signals if s.source_type == SourceType.competitor_assortment]
    local_stock = {s.source.lower() for s in comp if s.source.lower() in local_names}
    ref_stock = [s for s in comp if s.source.lower() in ref_names]
    n_local = len(scenario.local_competitors) or 1

    # local coverage gap + status
    if comp:
        opp.local_coverage_gap = round(1.0 - len(local_stock) / n_local, 3)
        if not local_stock:
            opp.coverage_status = CoverageStatus.absent
        elif len(local_stock) >= n_local:
            opp.coverage_status = CoverageStatus.covered
        else:
            opp.coverage_status = CoverageStatus.partially_covered
    else:
        opp.local_coverage_gap = 0.5  # no shelf evidence yet → unknown, lean to "check it"
        opp.coverage_status = CoverageStatus.unknown

    # commercial proof from reference retailers (stocking + bestseller ranks)
    rank_bonus = 0.4 if any((s.rank or 99) <= 10 for s in ref_stock) else 0.0
    opp.commercial_proof = round(min(1.0, 0.5 * len(ref_stock) + rank_bonus), 3)

    # corroboration across source TYPES (1 type→0, 2→0.5, 3+→1.0)
    n_types = len(opp.source_types)
    opp.corroboration = round(min(1.0, (n_types - 1) / 2.0), 3)

    # velocity = strongest recency/acceleration across signals
    opp.velocity = round(max((s.velocity if s.velocity is not None else s.signal_score) for s in opp.signals), 3)

    opp.raw_score = round(
        WEIGHTS["local_coverage_gap"] * opp.local_coverage_gap
        + WEIGHTS["corroboration"] * opp.corroboration
        + WEIGHTS["velocity"] * opp.velocity
        + WEIGHTS["commercial_proof"] * opp.commercial_proof,
        3,
    )

    # confidence
    if n_types >= 3 and opp.local_coverage_gap >= 0.5:
        opp.confidence = Confidence.high
    elif n_types == 2:
        opp.confidence = Confidence.medium
    else:
        opp.confidence = Confidence.low


def finalize(opp: Opportunity, scenario: ScenarioProfile) -> None:
    """Apply transfer_score (from enrich) → final_score, then discard rules."""
    opp.final_score = round(opp.raw_score * (opp.transfer_score / 100.0), 3)

    threshold = scenario.transfer_profile.discard_threshold
    reasons: list[str] = []
    if len(opp.source_types) < 2:
        reasons.append("single source type — not corroborated")
    if opp.coverage_status == CoverageStatus.covered:
        reasons.append("already covered across all local competitors")
    if opp.transfer_score and opp.transfer_score < threshold:
        weakest = _weakest_dimension(opp, scenario)
        reasons.append(f"transfer score {opp.transfer_score:.0f} < {threshold:.0f}" + (f" (weak {weakest})" if weakest else ""))

    if reasons:
        opp.discarded = True
        opp.discard_reason = "; ".join(reasons)


def _weakest_dimension(opp: Opportunity, scenario: ScenarioProfile) -> str | None:
    if not opp.transfer_dimensions:
        return None
    dims = opp.transfer_dimensions
    return min(dims.model_fields, key=lambda d: getattr(dims, d))


def rank_opportunities(opps: list[Opportunity]) -> list[Opportunity]:
    """Surviving opportunities sorted by final_score desc."""
    live = [o for o in opps if not o.discarded]
    return sorted(live, key=lambda o: o.final_score, reverse=True)
