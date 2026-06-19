"""competitor_assortment connector — local vs reference shelf gap.

Each row records that a retailer STOCKS a given opportunity (with brand/rank/url).
score.py derives ``local_coverage_gap`` = fraction of the scenario's
local_competitors NOT stocking it, and ``commercial_proof`` from reference
retailers that do. This is the connector that defines the buy opportunity.

Live path is Claude-web-search-assisted offline (fragile to scrape across
retailers), so it ships as a committed seed snapshot — the most robust option for
the cached demo. ``collect()`` returns [] → seed is used.
"""

from __future__ import annotations

from src.connectors.base import Connector
from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile


class CompetitorAssortmentConnector(Connector):
    source_type = SourceType.competitor_assortment
    name = "competitor_assortment"

    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        # Live assortment collection is Claude-research-assisted offline; the
        # curated snapshot in data/seed/<scenario>/competitor_assortment.json is
        # the source of truth for the demo. Return [] to use it.
        return []
