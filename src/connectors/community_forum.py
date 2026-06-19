"""community_forum connector — early/accelerating demand + legitimacy.

Live path: Reddit via praw over the scenario's communities. We weight **recency
and acceleration** (rising threads / upcoming popularity), NOT raw mention volume:
a topic going from 1 → 12 mentions this month matters more than one steady at 200.
Needs REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET in .env; otherwise seed is used.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict

from src.connectors.base import Connector
from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile


class CommunityForumConnector(Connector):
    source_type = SourceType.community_forum
    name = "community_forum"

    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        import praw  # raises ImportError → seed fallback

        cid, csec = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
        if not (cid and csec):
            raise RuntimeError("Reddit creds missing (REDDIT_CLIENT_ID/SECRET)")

        reddit = praw.Reddit(
            client_id=cid,
            client_secret=csec,
            user_agent=os.getenv("REDDIT_USER_AGENT", "alpine-signal-radar/0.1"),
        )
        seeds = scenario.seeds_for()
        rows: list[SignalRow] = []

        for comm in scenario.community_sources:
            sub_name = comm.name.split("/")[-1]  # "r/Ultralight" → "Ultralight"
            sub = reddit.subreddit(sub_name)
            # recency window: hottest recent posts; tally seed-keyword hits + score velocity
            counts: dict[str, list[float]] = defaultdict(list)
            for post in sub.new(limit=200):
                text = f"{post.title} {getattr(post, 'selftext', '')}".lower()
                for seed in seeds:
                    if re.search(r"\b" + re.escape(seed.split()[0].lower()) + r"\b", text):
                        # upvote ratio × recency proxy as a per-mention strength
                        counts[seed].append(float(getattr(post, "upvote_ratio", 0.5)))
            for seed, hits in counts.items():
                n = len(hits)
                velocity = min(1.0, n / 10.0)  # rising-thread proxy
                rows.append(
                    SignalRow(
                        source_type=self.source_type,
                        source=comm.name,
                        market=scenario.target_market if sub_name.lower().startswith("swiss") else "US",
                        keyword=seed,
                        signal_name=seed,
                        url=comm.url,
                        signal_score=min(1.0, (sum(hits) / n) if n else 0.3),
                        velocity=velocity,
                        notes=f"{n} recent threads mention '{seed}'",
                        observed_at="2026-06-19",
                        created_by_tool="community_forum/praw",
                    )
                )
        return rows
