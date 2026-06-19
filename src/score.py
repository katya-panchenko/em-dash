"""Deterministic scoring + discard rules.

    raw   = 0.35*local_coverage_gap + 0.30*corroboration + 0.20*velocity + 0.15*commercial_proof
    final = raw * (transfer_score / 100)          # transfer_score set by enrich.py
    confidence = high (>=3 source types + gap) | medium (2) | low (trend-only)

Transparent and tunable — the rankings are defensible to a jury, while Claude
supplies the transfer judgment (enrich.py). Two-phase: compute_features() runs
before enrichment; finalize() applies transfer_score + discard rules after.
"""

from __future__ import annotations

import re

from src.schema import BrandInfluence, Confidence, CoverageStatus, Direction, Opportunity, SourceType
from src.scenario import ScenarioProfile

WEIGHTS = {"local_coverage_gap": 0.35, "corroboration": 0.30, "velocity": 0.20, "commercial_proof": 0.15}
_MASS = {SourceType.search_trends, SourceType.community_forum}


def _sig_mentions(s, name: str) -> bool:
    """Word-boundary brand match (so 'On' doesn't match 'carbON')."""
    pat = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
    return any(field and pat.search(field) for field in (s.brand, s.collab_partner, s.source, s.notes))


def compute_features(
    opp: Opportunity, scenario: ScenarioProfile, brands: list[BrandInfluence] | None = None
) -> None:
    """Set deterministic features, direction, brand/trickle flags, raw_score, confidence."""
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

    # ── direction (signed momentum) ──
    weighted = [(s.momentum if s.momentum is not None else (s.velocity or 0.0), s.signal_score) for s in opp.signals]
    wsum = sum(w for _, w in weighted) or 1.0
    opp.momentum = round(sum(m * w for m, w in weighted) / wsum, 3)
    if opp.momentum > 0.10:
        opp.direction = Direction.rising
    elif opp.momentum < -0.10:
        opp.direction = Direction.declining
    else:
        opp.direction = Direction.flat

    # cooling score (early-warning for declining opps; stronger if lead markets cool)
    if opp.direction == Direction.declining:
        origin_cooling = any(
            s.market in scenario.reference_markets and (s.momentum or 0.0) < 0 for s in opp.signals
        )
        opp.cooling_score = round(abs(opp.momentum) * max(opp.corroboration, 0.3) * (1.0 if origin_cooling else 0.6), 3)

    # ── luxury trickle-down corroboration gate ──
    has_luxury = any(s.source_type == SourceType.luxury_runway for s in opp.signals)
    has_mass_rising = any(
        s.source_type in _MASS and ((s.momentum if s.momentum is not None else s.velocity) or 0.0) > 0
        for s in opp.signals
    )
    if has_luxury and has_mass_rising:
        opp.luxury_trickle = True
    elif has_luxury and opp.source_types == {SourceType.luxury_runway}:
        opp.early_watch = True  # runway-only → too soon to call (the noise filter)

    # ── trendsetter brand backing (+ small lead boost) ──
    if brands:
        cands = [b for b in brands if b.influence_score >= 0.5 and any(_sig_mentions(s, b.name.lower()) for s in opp.signals)]
        if cands:
            top = max(cands, key=lambda b: b.influence_score)
            opp.trendsetter_backed = True
            opp.top_brand = top.name
            opp.raw_score = round(min(1.0, opp.raw_score + 0.05), 3)

    # confidence
    if n_types >= 3 and opp.local_coverage_gap >= 0.5:
        opp.confidence = Confidence.high
    elif n_types == 2:
        opp.confidence = Confidence.medium
    else:
        opp.confidence = Confidence.low


def finalize(opp: Opportunity, scenario: ScenarioProfile) -> None:
    """Apply transfer_score (from enrich) → final_score, then discard rules.

    Declining + early-watch opps are routed to their own buckets and skip the
    buy-discard rules (they are not buy candidates)."""
    opp.final_score = round(opp.raw_score * (opp.transfer_score / 100.0), 3)

    if opp.early_watch or opp.direction == Direction.declining:
        return

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
    """Surviving RISING buy candidates, sorted by final_score desc."""
    live = [
        o for o in opps
        if not o.discarded and not o.early_watch and o.direction != Direction.declining
    ]
    return sorted(live, key=lambda o: o.final_score, reverse=True)


def cooling_watch(opps: list[Opportunity]) -> list[Opportunity]:
    """Declining opps (≥2 source types) for the early-warning watchlist."""
    cooling = [o for o in opps if o.direction == Direction.declining and len(o.source_types) >= 2]
    return sorted(cooling, key=lambda o: o.cooling_score, reverse=True)


def early_watch_list(opps: list[Opportunity]) -> list[Opportunity]:
    """Luxury-only 'too soon to call' opps (runway signal, no mass corroboration yet)."""
    return [o for o in opps if o.early_watch]
