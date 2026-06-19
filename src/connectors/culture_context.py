"""culture_context connector — leading indicators before search/sales.

Carries the "spicy" weak signals via ``signal_flavor``:
  viewership · emerging_business · event_anticipation ·
  cross_category_spillover · geo_style_diffusion · segment_trend

These precede search/sales movement (e.g. women's-cycling viewership up →
women's gravel gear; a style hot in KR/CN/US → likely DACH diffusion). Sourced
via Claude-research-assisted offline collection and shipped as a seed snapshot.
``collect()`` returns [] → seed is used.
"""

from __future__ import annotations

from src.connectors.base import Connector
from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile


class CultureContextConnector(Connector):
    source_type = SourceType.culture_context
    name = "culture_context"

    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        # Leading-indicator signals are curated offline (Claude-research-assisted)
        # into data/seed/<scenario>/culture_context.json. Return [] to use it.
        return []
