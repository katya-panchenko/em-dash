"""Signal connectors. Each emits normalized SignalRows for a source_type.

Add a source = add a connector class + register it in CONNECTORS. Nothing
downstream (dedup, score, dashboard) changes.
"""

from src.connectors.base import Connector
from src.connectors.search_trends import SearchTrendsConnector
from src.connectors.community_forum import CommunityForumConnector
from src.connectors.competitor_assortment import CompetitorAssortmentConnector
from src.connectors.culture_context import CultureContextConnector

# registry keyed by source_type string (matches scenario.enabled_sources)
CONNECTORS: dict[str, type[Connector]] = {
    "search_trends": SearchTrendsConnector,
    "community_forum": CommunityForumConnector,
    "competitor_assortment": CompetitorAssortmentConnector,
    "culture_context": CultureContextConnector,
}

__all__ = ["Connector", "CONNECTORS"]
