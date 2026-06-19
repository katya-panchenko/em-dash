"""search_trends connector — cross-market transfer window.

Live path: Google Trends via pytrends, comparing origin/reference markets
(US/UK/JP/KR/CN…) against the target market (CH/DE). A keyword rising in origin
markets but flat in the target = an open transfer window. pytrends is rate-limited
and flaky, so seed is the reliable demo path.
"""

from __future__ import annotations

from src.connectors.base import Connector
from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile

# pytrends geo codes for the markets we model
_GEO = {"US": "US", "UK": "GB", "DE": "DE", "CH": "CH", "JP": "JP", "KR": "KR", "CN": "CN"}


class SearchTrendsConnector(Connector):
    source_type = SourceType.search_trends
    name = "search_trends"

    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        from pytrends.request import TrendReq  # raises ImportError → seed fallback

        pytrends = TrendReq(hl="en-US", tz=60)
        markets = [scenario.target_market, *scenario.reference_markets]
        geos = [m for m in markets if m in _GEO]
        rows: list[SignalRow] = []

        for cat in scenario.categories:
            for seed in cat.seeds:
                interest = {}
                for m in geos:
                    pytrends.build_payload([seed], timeframe="today 12-m", geo=_GEO[m])
                    df = pytrends.interest_over_time()
                    if df.empty:
                        continue
                    series = df[seed]
                    recent = series.tail(4).mean()
                    earlier = series.head(8).mean() or 1.0
                    interest[m] = {"level": float(recent), "accel": float(recent / earlier)}
                for m, vals in interest.items():
                    momentum = max(-1.0, min(1.0, vals["accel"] - 1.0))  # SIGNED: <0 means cooling
                    rows.append(
                        SignalRow(
                            source_type=self.source_type,
                            source="Google Trends",
                            market=m,
                            category=cat.id,
                            keyword=seed,
                            signal_name=seed,
                            url=f"https://trends.google.com/trends/explore?q={seed.replace(' ', '%20')}&geo={_GEO[m]}",
                            signal_score=min(1.0, vals["level"] / 100.0),
                            velocity=min(1.0, abs(momentum)),
                            momentum=momentum,
                            notes=f"12-mo interest level {vals['level']:.0f}, accel {vals['accel']:.2f}x",
                            observed_at="2026-06-19",
                            created_by_tool="search_trends/pytrends",
                        )
                    )
        return rows
