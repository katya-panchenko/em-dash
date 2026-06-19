"""Normalized data contract for Alpine Signal Radar.

Every connector emits ``SignalRow``s regardless of source. The pipeline clusters
them into ``Opportunity`` objects, scores them deterministically, and exports
``RecommendationRow``s. Field names mirror ``docs/data-contract.md`` so the jury
can inspect/rerun the CSVs.

``source_type`` is a closed enum (NOT a retailer name) — that is what keeps the
engine generic and the scenarios swappable.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Enums ───────────────────────────────────────────────────────────────────
class SourceType(str, Enum):
    """The universal signal source types. Instances (Transa, r/Ultralight, …)
    live in scenario YAML, never here."""

    competitor_assortment = "competitor_assortment"  # local vs reference shelf gap
    community_forum = "community_forum"  # early/accelerating demand + legitimacy
    search_trends = "search_trends"  # cross-market transfer window
    culture_context = "culture_context"  # leading indicators before search/sales
    trade_publication = "trade_publication"  # documented future connector (ISPO, …)


class SignalFlavor(str, Enum):
    """Sub-types carried by ``culture_context`` signals (the "spicy" leading
    indicators). Only meaningful when source_type == culture_context."""

    viewership = "viewership"  # e.g. women's cycling viewership momentum
    emerging_business = "emerging_business"  # e.g. protein-bar startup surge
    event_anticipation = "event_anticipation"  # upcoming events (UTMB, Olympics) that spike demand
    cross_category_spillover = "cross_category_spillover"  # adjacent-category trend with outdoor implication
    geo_style_diffusion = "geo_style_diffusion"  # style popular in KR/CN/US likely to diffuse to CH
    segment_trend = "segment_trend"  # children's / new-demographic growth


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class CoverageStatus(str, Enum):
    covered = "covered"
    partially_covered = "partially_covered"
    absent = "absent"
    unknown = "unknown"
    not_relevant = "not_relevant"


# data-contract `signal_type` values, derived from source_type for CSV compatibility
_SIGNAL_TYPE_BY_SOURCE = {
    SourceType.search_trends: "search",
    SourceType.community_forum: "social",
    SourceType.competitor_assortment: "competitor",
    SourceType.culture_context: "web",
    SourceType.trade_publication: "web",
}


# ─── Signal row ──────────────────────────────────────────────────────────────
class SignalRow(BaseModel):
    """One observed signal from one source. Mirrors the data-contract Signal Row."""

    # provenance
    source_type: SourceType
    source: str  # human-readable source name, e.g. "REI" or "r/Ultralight"
    market: str  # CH, DACH, US, UK, JP, KR, CN, ...
    created_by_tool: str = "alpine-signal-radar"

    # what the signal is about
    keyword: str  # query/hashtag/product phrase/category label
    signal_name: str  # human-readable opportunity name
    category: Optional[str] = None  # scenario category id (trail_running, ...)
    product_name: Optional[str] = None
    brand: Optional[str] = None
    signal_flavor: Optional[SignalFlavor] = None  # culture_context only

    # evidence
    url: Optional[str] = None
    price: Optional[float] = None
    rank: Optional[int] = None
    notes: Optional[str] = None
    observed_at: Optional[str] = None  # ISO date string

    # per-signal strength (0..1); how the connector rated this individual signal
    signal_score: float = Field(default=0.5, ge=0.0, le=1.0)
    velocity: Optional[float] = Field(default=None, ge=0.0, le=1.0)  # recency/acceleration
    confidence: Optional[Confidence] = None

    # set during clustering
    opportunity_id: Optional[str] = None

    @field_validator("market")
    @classmethod
    def _upper_market(cls, v: str) -> str:
        return v.strip().upper()

    @property
    def signal_type(self) -> str:
        """data-contract `signal_type` (search/social/web/...)."""
        return _SIGNAL_TYPE_BY_SOURCE.get(self.source_type, "web")


# ─── Transfer scoring ────────────────────────────────────────────────────────
class TransferDimensions(BaseModel):
    """Each dimension is a 0..1 score (assigned by Claude in enrich.py, or by a
    deterministic fallback). Weighted by the scenario's transfer_profile."""

    market_context_fit: float = Field(default=0.5, ge=0.0, le=1.0)
    legitimacy_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    buyer_risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    commercial_readiness: float = Field(default=0.5, ge=0.0, le=1.0)
    durability_expectation: float = Field(default=0.5, ge=0.0, le=1.0)

    def weighted_score(self, weights: dict[str, float]) -> float:
        """transfer_score on a 0..100 scale = 100 * Σ(weight_d * dimension_d)."""
        total = sum(
            weights.get(dim, 0.0) * getattr(self, dim) for dim in self.model_fields
        )
        return round(100.0 * total, 1)


# ─── Opportunity (post-dedup cluster) ────────────────────────────────────────
class Opportunity(BaseModel):
    """A deduplicated candidate built from one or more SignalRows."""

    opportunity_id: str
    name: str
    category: Optional[str] = None
    signals: list[SignalRow] = Field(default_factory=list)

    # deterministic features (0..1), computed in score.py
    local_coverage_gap: float = 0.0
    corroboration: float = 0.0
    velocity: float = 0.0
    commercial_proof: float = 0.0

    # transfer (enrich.py)
    transfer_dimensions: Optional[TransferDimensions] = None
    transfer_score: float = 0.0  # 0..100
    coverage_status: CoverageStatus = CoverageStatus.unknown

    # composite (score.py)
    raw_score: float = 0.0
    final_score: float = 0.0
    confidence: Confidence = Confidence.low
    discarded: bool = False
    discard_reason: Optional[str] = None

    # narrative enrichment (enrich.py)
    why_now: Optional[str] = None
    transferability: Optional[str] = None
    recommended_action: Optional[str] = None
    risks: Optional[str] = None

    @property
    def source_types(self) -> set[SourceType]:
        return {s.source_type for s in self.signals}

    @property
    def markets(self) -> list[str]:
        return sorted({s.market for s in self.signals})

    @property
    def evidence_urls(self) -> list[str]:
        return sorted({s.url for s in self.signals if s.url})


# ─── Recommendation row (export) ─────────────────────────────────────────────
class RecommendationRow(BaseModel):
    """Mirrors the data-contract Recommendation Row for recommendations.csv."""

    rank: int
    opportunity: str
    first_observed_market: str
    evidence_summary: str
    evidence_urls: str  # ; joined
    transferability: str
    coverage_status: str
    recommended_action: str
    confidence: str
    risks: str
    final_score: float
    transfer_score: float

    @classmethod
    def from_opportunity(
        cls, opp: Opportunity, rank: int, first_observed_market: Optional[str] = None
    ) -> "RecommendationRow":
        first_market = first_observed_market or (opp.markets[0] if opp.markets else "unknown")
        return cls(
            rank=rank,
            opportunity=opp.name,
            first_observed_market=first_market,
            evidence_summary=opp.why_now or "",
            evidence_urls="; ".join(opp.evidence_urls),
            transferability=opp.transferability or "",
            coverage_status=opp.coverage_status.value,
            recommended_action=opp.recommended_action or "",
            confidence=opp.confidence.value,
            risks=opp.risks or "",
            final_score=round(opp.final_score, 3),
            transfer_score=opp.transfer_score,
        )
