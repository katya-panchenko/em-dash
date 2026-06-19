"""Connector base class.

Hybrid collection: ``run()`` tries a live ``collect()`` (offline, before the
demo); on any failure or empty result it falls back to a committed seed snapshot
so the cached demo is always reproducible. Output is cached to
``outputs/<scenario_id>/<name>.json`` and read back on stage — NEVER collected live
during the demo.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from src.schema import SignalRow, SourceType
from src.scenario import ScenarioProfile


class Connector(ABC):
    source_type: SourceType
    name: str  # short id used for seed + cache filenames

    # ── live collection (implemented per connector; may be a no-op for
    #    Claude-research-assisted sources that ship as seed) ──
    @abstractmethod
    def collect(self, scenario: ScenarioProfile) -> list[SignalRow]:
        ...

    # ── seed fallback ──
    def seed_path(self, scenario: ScenarioProfile, seed_root: str = "data/seed") -> Path:
        return Path(seed_root) / scenario.scenario_id / f"{self.name}.json"

    def load_seed(self, scenario: ScenarioProfile) -> list[SignalRow]:
        path = self.seed_path(scenario)
        if not path.exists():
            return []
        raw = json.loads(path.read_text())
        return [SignalRow.model_validate(r) for r in raw]

    # ── orchestration ──
    def run(self, scenario: ScenarioProfile, prefer_live: bool = True) -> list[SignalRow]:
        rows: list[SignalRow] = []
        live_ok = False
        if prefer_live:
            try:
                rows = self.collect(scenario)
                live_ok = bool(rows)
            except Exception as e:  # noqa: BLE001 — connectors must degrade gracefully
                print(f"[{self.name}] live collect failed ({type(e).__name__}: {e}); using seed")
        if not rows:
            rows = self.load_seed(scenario)
        src = "live" if live_ok else "seed"
        print(f"[{self.name}] {len(rows)} signals ({src})")
        return rows

    def cache_path(self, scenario: ScenarioProfile, out_root: str = "outputs") -> Path:
        return Path(out_root) / scenario.scenario_id / f"{self.name}.json"

    def write_cache(self, scenario: ScenarioProfile, rows: list[SignalRow], out_root: str = "outputs") -> Path:
        path = self.cache_path(scenario, out_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([r.model_dump(mode="json", exclude_none=True) for r in rows], indent=2))
        return path
