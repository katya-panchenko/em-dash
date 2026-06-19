"""luxury_runway connector — high-fashion → mass trickle-down.

Captures premium/luxury origin signals: runway coverage, luxury×technical
**collab bridges** (Salomon×MM6, Arc'teryx×Jil Sander, On×Loewe), and resale
velocity. A luxury signal alone is noise/too-early; the corroboration gate in
score.py only promotes it to a buy when a mass signal (search/community) is also
moving. Feeds the Brand Influence layer (collab_gravity component).

Sourced via Claude-research-assisted offline collection and shipped as a seed
snapshot — ``collect()`` returns [] → seed is used.
"""

from __future__ import annotations

from src.connectors.base import Connector
from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile


class LuxuryRunwayConnector(Connector):
    source_type = SourceType.luxury_runway
    name = "luxury_runway"

    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        # Curated offline into data/seed/<scenario>/luxury_runway.json. Return [].
        return []
