"""Deduplicate signals into Opportunity clusters.

The same opportunity often appears across sources/markets (search + community +
competitor gap). Merging them is what turns many weak signals into one
corroborated answer — and corroboration across source *types* is the confidence
signal. Clustering is by normalized signal name with a fuzzy fallback.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from src.schema import Opportunity, SignalRow


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cluster_signals(signals: list[SignalRow], threshold: int = 88) -> list[Opportunity]:
    """Group signals into opportunities by normalized name + fuzzy match."""
    groups: list[dict] = []
    for sig in signals:
        key = _norm(sig.signal_name)
        match = next(
            (g for g in groups if fuzz.token_sort_ratio(key, g["key"]) >= threshold),
            None,
        )
        if match is None:
            groups.append({"key": key, "name": sig.signal_name, "signals": [sig]})
        else:
            match["signals"].append(sig)

    opportunities: list[Opportunity] = []
    for g in groups:
        sigs: list[SignalRow] = g["signals"]
        # representative category = most common non-null
        cats = [s.category for s in sigs if s.category]
        category = max(set(cats), key=cats.count) if cats else None
        oid = _slug(g["name"])
        for s in sigs:
            s.opportunity_id = oid
        opportunities.append(
            Opportunity(opportunity_id=oid, name=g["name"], category=category, signals=sigs)
        )
    return opportunities
