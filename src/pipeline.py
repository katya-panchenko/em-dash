"""End-to-end pipeline: cached signals → dedup → score → enrich → finalize → export.

Reads the offline cache (never collects live), runs the 7-step flow, and writes:
  outputs/<scenario>/signals.csv          — every normalized signal (inspectable)
  outputs/<scenario>/recommendations.csv  — ranked opportunities + actions
  outputs/<scenario>/opportunities.json   — full objects for the dashboard
  outputs/<scenario>/summary.md           — exec narrative

    python -m src.pipeline --scenario config/scenarios/swiss_outdoor.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.dedup import cluster_signals
from src.enrich import enrich, exec_summary
from src.schema import RecommendationRow, SignalRow
from src.scenario import load_scenario
from src.score import compute_features, finalize, rank_opportunities


def _load_cached_signals(scenario_id: str, out_root: str = "outputs") -> list[SignalRow]:
    folder = Path(out_root) / scenario_id
    rows: list[SignalRow] = []
    for f in sorted(folder.glob("*.json")):
        if f.name in {"opportunities.json"}:
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict) and "source_type" in data[0]:
            rows += [SignalRow.model_validate(r) for r in data]
    return rows


def _origin_market(opp, scenario) -> str:
    """Strongest reference/origin market where the signal was observed (not the
    target market). Falls back to the first market."""
    origins = [(s.market, s.signal_score) for s in opp.signals if s.market in scenario.reference_markets]
    if origins:
        return max(origins, key=lambda t: t[1])[0]
    return opp.markets[0] if opp.markets else "unknown"


def run(scenario_path: str, use_llm: bool = True) -> dict:
    scenario = load_scenario(scenario_path)
    out_dir = Path("outputs") / scenario.scenario_id
    out_dir.mkdir(parents=True, exist_ok=True)

    signals = _load_cached_signals(scenario.scenario_id)
    if not signals:
        raise SystemExit(
            f"No cached signals for {scenario.scenario_id}. Run: "
            f"python -m src.collect_offline --scenario {scenario_path}"
        )

    opps = cluster_signals(signals)
    for o in opps:
        compute_features(o, scenario)
    llm_summary = enrich(opps, scenario, use_llm=use_llm)
    for o in opps:
        finalize(o, scenario)
    ranked = rank_opportunities(opps)
    summary = exec_summary(opps, scenario, llm_summary)

    # ── exports ──
    signal_records = []
    for s in signals:
        d = s.model_dump(mode="json", exclude_none=True)
        d["signal_type"] = s.signal_type
        signal_records.append(d)
    pd.DataFrame(signal_records).to_csv(out_dir / "signals.csv", index=False)

    recs = [
        RecommendationRow.from_opportunity(o, i + 1, _origin_market(o, scenario)).model_dump()
        for i, o in enumerate(ranked)
    ]
    pd.DataFrame(recs).to_csv(out_dir / "recommendations.csv", index=False)

    (out_dir / "opportunities.json").write_text(
        json.dumps([o.model_dump(mode="json") for o in opps], indent=2, ensure_ascii=False)
    )
    (out_dir / "summary.md").write_text(f"# {scenario.display_name} — Opportunity Summary\n\n{summary}\n")

    discarded = [o for o in opps if o.discarded]
    print(f"\n{len(signals)} signals → {len(opps)} opportunities → {len(ranked)} surfaced, {len(discarded)} discarded")
    print(f"Artifacts in {out_dir}/ : signals.csv, recommendations.csv, opportunities.json, summary.md")
    print("\nTop opportunities:")
    for i, o in enumerate(ranked[:5], 1):
        print(f"  {i}. {o.name}  final={o.final_score}  transfer={o.transfer_score:.0f}/100  conf={o.confidence.value}")
    if discarded:
        print("\nGraveyard (discarded):")
        for o in discarded:
            print(f"  ✗ {o.name} — {o.discard_reason}")

    return {"scenario": scenario, "opportunities": opps, "ranked": ranked, "summary": summary}


def main() -> None:
    ap = argparse.ArgumentParser(description="Alpine Signal Radar pipeline")
    ap.add_argument("--scenario", default="config/scenarios/swiss_outdoor.yaml")
    ap.add_argument("--no-llm", action="store_true", help="skip Claude; deterministic enrichment only")
    args = ap.parse_args()
    run(args.scenario, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
