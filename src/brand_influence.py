"""Brand Influence — rank the scenario's trendsetter brands from signal behaviour.

A brand is a trendsetter to the degree its products *lead*. We score each tracked
brand (from scenario.trendsetter_brands) 0..1 from five components:
  collab_gravity      luxury×brand collabs (being chosen for a collab = validated)
  community_authority enthusiast mention velocity (legitimacy, not hype)
  lead_time           shows up in origin/reference markets before the local market
  cross_market_spread appears across multiple origin markets (US+KR+JP...)
  reference_rank      bestseller rank at reference (trend-leader) retailers

Output: a ranked list of BrandInfluence → the "Trendsetter Brands to Watch" table.
"""

from __future__ import annotations

import re

from src.schema import BrandInfluence, SignalRow, SourceType
from src.scenario import ScenarioProfile

WEIGHTS = {
    "collab_gravity": 0.30,
    "community_authority": 0.25,
    "lead_time": 0.20,
    "cross_market_spread": 0.15,
    "reference_rank": 0.10,
}


def _mentions(s: SignalRow, name: str) -> bool:
    """Word-boundary match so short brands ('On') don't match 'carbON'/'hydratiON'."""
    pat = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
    return any(field and pat.search(field) for field in (s.brand, s.collab_partner, s.source, s.notes))


def compute(signals: list[SignalRow], scenario: ScenarioProfile) -> list[BrandInfluence]:
    ref_names = {r.name.lower() for r in scenario.reference_retailers}
    origin_markets = set(scenario.reference_markets)
    target = scenario.target_market
    out: list[BrandInfluence] = []

    for brand in scenario.trendsetter_brands:
        nl = brand.name.lower()
        attr = [s for s in signals if _mentions(s, nl)]
        if not attr:
            continue  # no evidence → omit from the watch table

        collabs = [s for s in attr if s.source_type == SourceType.luxury_runway and s.collab_partner]
        collab_gravity = min(1.0, 0.5 * len(collabs))

        comm_vel = [s.velocity or s.signal_score for s in attr if s.source_type == SourceType.community_forum]
        community_authority = min(1.0, max(comm_vel) if comm_vel else 0.0)

        markets = {s.market for s in attr}
        origin_hits = markets & origin_markets
        if origin_hits and target not in markets:
            lead_time = 1.0
        elif origin_hits:
            lead_time = 0.5
        else:
            lead_time = 0.2

        cross_market_spread = min(1.0, len(origin_hits) / 3.0)

        ref_ranks = [s.rank for s in attr if s.rank and s.source.lower() in ref_names]
        reference_rank = max(0.0, 1.0 - (min(ref_ranks) - 1) / 15.0) if ref_ranks else 0.0

        comps = {
            "collab_gravity": round(collab_gravity, 3),
            "community_authority": round(community_authority, 3),
            "lead_time": round(lead_time, 3),
            "cross_market_spread": round(cross_market_spread, 3),
            "reference_rank": round(reference_rank, 3),
        }
        influence = round(sum(WEIGHTS[k] * v for k, v in comps.items()), 3)
        reasons = []
        if collabs:
            reasons.append(f"{len(collabs)} luxury collab(s) ({', '.join(sorted({c.collab_partner for c in collabs}))})")
        if community_authority >= 0.5:
            reasons.append("strong enthusiast community authority")
        if cross_market_spread >= 0.5:
            reasons.append(f"present across {len(origin_hits)} origin markets")
        if reference_rank > 0:
            reasons.append("bestseller rank at a reference retailer")
        note = ("Trendsetter via " + "; ".join(reasons) + ".") if reasons else None
        out.append(
            BrandInfluence(
                name=brand.name,
                tier=brand.tier,
                influence_score=influence,
                components=comps,
                markets=sorted(markets),
                evidence_urls=sorted({s.url for s in attr if s.url}),
                note=note,
            )
        )

    out.sort(key=lambda b: b.influence_score, reverse=True)
    return out


def influence_map(brands: list[BrandInfluence]) -> dict[str, float]:
    """name(lower) → influence_score, for opportunity attribution in score.py."""
    return {b.name.lower(): b.influence_score for b in brands}
