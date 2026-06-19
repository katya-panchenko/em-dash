"""Scenario profiles — the reusability mechanism.

A scenario YAML holds every market/retailer/community/transfer specific. Python
code reads these; it never hardcodes a retailer or subreddit name. Swap the
profile → retarget the whole engine to a new market, category, or industry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class Competitor(BaseModel):
    name: str
    url: Optional[str] = None
    role: Optional[str] = None
    category_path: Optional[str] = None


class ReferenceRetailer(BaseModel):
    name: str
    market: str
    url: Optional[str] = None
    role: Optional[str] = None


class CommunitySource(BaseModel):
    type: str = "community_forum"
    name: str
    url: Optional[str] = None


class Category(BaseModel):
    id: str
    seeds: list[str] = Field(default_factory=list)


class TransferProfile(BaseModel):
    discard_threshold: float = 40.0
    dimensions: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_weights(self) -> "TransferProfile":
        if self.dimensions:
            total = sum(self.dimensions.values())
            # weights should sum to ~1; warn-by-normalize rather than hard-fail
            if abs(total - 1.0) > 1e-6 and total > 0:
                self.dimensions = {k: v / total for k, v in self.dimensions.items()}
        return self


class ScenarioProfile(BaseModel):
    scenario_id: str
    display_name: str
    target_market: str
    reference_markets: list[str] = Field(default_factory=list)

    local_competitors: list[Competitor] = Field(default_factory=list)
    reference_retailers: list[ReferenceRetailer] = Field(default_factory=list)
    community_sources: list[CommunitySource] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)

    legitimacy_markers: list[str] = Field(default_factory=list)
    transfer_profile: TransferProfile = Field(default_factory=TransferProfile)

    # which connectors to run for this scenario
    enabled_sources: list[str] = Field(
        default_factory=lambda: [
            "search_trends",
            "community_forum",
            "competitor_assortment",
            "culture_context",
        ]
    )

    # pitch labels rendered in the dashboard when this profile is loaded
    ui_labels: dict[str, str] = Field(default_factory=dict)

    def seeds_for(self, category_id: Optional[str] = None) -> list[str]:
        cats = self.categories
        if category_id:
            cats = [c for c in cats if c.id == category_id]
        return [s for c in cats for s in c.seeds]

    def label(self, key: str, default: str) -> str:
        return self.ui_labels.get(key, default)


def load_scenario(path: str | Path) -> ScenarioProfile:
    """Load and validate a scenario profile from YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Scenario profile not found: {p}")
    data = yaml.safe_load(p.read_text())
    if not data:
        raise ValueError(f"Scenario profile is empty: {p}")
    return ScenarioProfile.model_validate(data)


if __name__ == "__main__":
    import sys

    profile = load_scenario(sys.argv[1] if len(sys.argv) > 1 else "config/scenarios/swiss_outdoor.yaml")
    print(f"Loaded: {profile.display_name} ({profile.scenario_id})")
    print(f"  target={profile.target_market} reference={profile.reference_markets}")
    print(f"  competitors={[c.name for c in profile.local_competitors]}")
    print(f"  communities={[c.name for c in profile.community_sources]}")
    print(f"  categories={[c.id for c in profile.categories]}")
    print(f"  transfer weights={profile.transfer_profile.dimensions}")
