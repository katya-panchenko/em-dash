"""Export a single web-friendly JSON for the dashboard website (e.g. Lovable).

Reads the pipeline artifacts in outputs/<scenario>/ and writes web/<scenario>.json
with clean, UI-ready sections: summary, buys, cooling (downward trends),
early_watch, graveyard, trendsetters. The website fetches/embeds this one file —
decoupled from our internal schema.

    python scripts/export_web.py [scenario_id]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

from src.scenario import load_scenario  # noqa: E402


def _evidence(o: dict) -> list[dict]:
    return [
        {"source_type": s["source_type"], "source": s["source"], "market": s.get("market"),
         "url": s.get("url"), "note": s.get("note") or s.get("notes")}
        for s in o["signals"] if s.get("url")
    ]


def _n_types(o: dict) -> int:
    return len({s["source_type"] for s in o["signals"]})


def _markets(o: dict) -> list[str]:
    return sorted({s["market"] for s in o["signals"] if s.get("market")})


def build(scenario_id: str) -> dict:
    base = Path("outputs") / scenario_id
    opps = json.loads((base / "opportunities.json").read_text())
    brands = json.loads((base / "brand_influence.json").read_text()) if (base / "brand_influence.json").exists() else []
    summary = (base / "summary.md").read_text().split("\n", 2)[-1].strip() if (base / "summary.md").exists() else ""
    scn = load_scenario(f"config/scenarios/{scenario_id}.yaml")

    buys = sorted(
        [o for o in opps if not o["discarded"] and not o.get("early_watch") and o.get("direction") != "declining"],
        key=lambda o: o["final_score"], reverse=True,
    )
    cooling = sorted(
        [o for o in opps if o.get("direction") == "declining" and _n_types(o) >= 2],
        key=lambda o: o["cooling_score"], reverse=True,
    )

    def buy_card(o, rank):
        return {
            "rank": rank, "name": o["name"], "category": o.get("category"),
            "final_score": o["final_score"], "transfer_score": o["transfer_score"],
            "confidence": o["confidence"], "coverage_status": o["coverage_status"],
            "momentum": o["momentum"], "direction": o["direction"],
            "trendsetter_backed": o.get("trendsetter_backed", False), "top_brand": o.get("top_brand"),
            "luxury_trickle": o.get("luxury_trickle", False), "trickle_note": o.get("trickle_note"),
            "why_now": o.get("why_now"), "transferability": o.get("transferability"),
            "recommended_action": o.get("recommended_action"), "risks": o.get("risks"),
            "evidence": _evidence(o),
        }

    return {
        "scenario_id": scenario_id,
        "display_name": scn.display_name,
        "target_market": scn.target_market,
        "summary": summary,
        "buys": [buy_card(o, i + 1) for i, o in enumerate(buys)],
        "cooling": [
            {"rank": i + 1, "name": o["name"], "momentum": o["momentum"], "cooling_score": o["cooling_score"],
             "markets": _markets(o), "why_cooling": o.get("why_now"),
             "recommended_action": o.get("recommended_action"), "evidence": _evidence(o)}
            for i, o in enumerate(cooling)
        ],
        "early_watch": [
            {"name": o["name"], "trickle_note": o.get("trickle_note"), "why": o.get("why_now")}
            for o in opps if o.get("early_watch")
        ],
        "graveyard": [
            {"name": o["name"], "reason": o.get("discard_reason")}
            for o in opps if o["discarded"]
        ],
        "trendsetters": [
            {"rank": i + 1, "name": b["name"], "tier": b["tier"], "influence_score": b["influence_score"],
             "components": b["components"], "markets": b["markets"], "note": b.get("note"),
             "evidence_urls": b.get("evidence_urls", [])}
            for i, b in enumerate(brands)
        ],
    }


def main(scenario_id: str = "swiss_outdoor") -> None:
    data = build(scenario_id)
    out = Path("web") / f"{scenario_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(
        f"Wrote {out} — {len(data['buys'])} buys, {len(data['cooling'])} cooling, "
        f"{len(data['early_watch'])} early-watch, {len(data['trendsetters'])} trendsetters"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "swiss_outdoor")
