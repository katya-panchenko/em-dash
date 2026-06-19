"""Offline collection — run enabled connectors for a scenario and cache results.

Run this BEFORE the demo. It tries each connector live and falls back to the
committed seed snapshot, writing outputs/<scenario_id>/<source>.json. The demo
(and pipeline.py) read only the cache — never collect live on stage.

    python -m src.collect_offline --scenario config/scenarios/swiss_outdoor.yaml
"""

from __future__ import annotations

import argparse

from src.connectors import CONNECTORS
from src.scenario import load_scenario


def collect(scenario_path: str, prefer_live: bool = True) -> None:
    scenario = load_scenario(scenario_path)
    print(f"Collecting for: {scenario.display_name} ({scenario.scenario_id})")
    total = 0
    for source in scenario.enabled_sources:
        cls = CONNECTORS.get(source)
        if cls is None:
            print(f"[{source}] no connector registered — skipping")
            continue
        connector = cls()
        rows = connector.run(scenario, prefer_live=prefer_live)
        path = connector.write_cache(scenario, rows)
        total += len(rows)
        print(f"[{source}] cached {len(rows)} → {path}")
    print(f"Done: {total} signals cached under outputs/{scenario.scenario_id}/")


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline signal collection")
    ap.add_argument("--scenario", default="config/scenarios/swiss_outdoor.yaml")
    ap.add_argument("--no-live", action="store_true", help="seed only; skip live connectors")
    args = ap.parse_args()
    collect(args.scenario, prefer_live=not args.no_live)


if __name__ == "__main__":
    main()
