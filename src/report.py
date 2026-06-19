"""Dashboard helpers — plots + tables consumed by notebooks/dashboard.ipynb.

Reads the pipeline artifacts in outputs/<scenario>/ and renders the demo visuals.
Pure presentation: no collection or scoring here. Pitch labels come from the
loaded scenario profile, so the same notebook renders any scenario.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.scenario import ScenarioProfile, load_scenario

CONF_COLORS = {"high": "#2a9d8f", "medium": "#e9c46a", "low": "#e76f51"}
_DIMS = [
    "market_context_fit",
    "legitimacy_threshold",
    "buyer_risk_tolerance",
    "commercial_readiness",
    "durability_expectation",
]


# ─── loading ─────────────────────────────────────────────────────────────────
def load_results(scenario_id: str = "swiss_outdoor", out_root: str = "outputs"):
    base = Path(out_root) / scenario_id
    opps = json.loads((base / "opportunities.json").read_text())
    summary = (base / "summary.md").read_text() if (base / "summary.md").exists() else ""
    return opps, summary


def live(opps: list[dict]) -> list[dict]:
    return [o for o in opps if not o.get("discarded")]


def dead(opps: list[dict]) -> list[dict]:
    return [o for o in opps if o.get("discarded")]


def _filter(opps: list[dict], category: str | None) -> list[dict]:
    return [o for o in opps if (category is None or o.get("category") == category)]


# ─── 1. ranked opportunities ─────────────────────────────────────────────────
def plot_ranked(opps: list[dict], scenario: ScenarioProfile, category: str | None = None, top: int = 10):
    rows = sorted(_filter(live(opps), category), key=lambda o: o["final_score"], reverse=True)[:top][::-1]
    if not rows:
        print("No surfaced opportunities for this filter.")
        return
    names = [o["name"] for o in rows]
    scores = [o["final_score"] for o in rows]
    colors = [CONF_COLORS.get(o["confidence"], "#999") for o in rows]
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(rows) + 1.5))
    ax.barh(names, scores, color=colors)
    for y, o in enumerate(rows):
        ax.text(o["final_score"] + 0.005, y, f"{o['final_score']:.2f}", va="center", fontsize=9)
    title = f"{scenario.display_name} — Ranked opportunities"
    if category:
        title += f"  ·  {category}"
    ax.set_xlabel("Opportunity score (final)")
    ax.set_title(title)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in CONF_COLORS.values()]
    ax.legend(handles, [f"{k} confidence" for k in CONF_COLORS], loc="lower right", fontsize=8)
    ax.margins(x=0.12)
    plt.tight_layout()
    return ax


# ─── 2. whitespace scatter (the money chart) ─────────────────────────────────
def plot_whitespace(opps: list[dict], scenario: ScenarioProfile, category: str | None = None):
    rows = _filter(live(opps), category)
    fig, ax = plt.subplots(figsize=(8.5, 6))
    gap_label = scenario.label("local_coverage_gap", "Local assortment gap")
    # stagger labels of points sharing a y band to reduce overlap
    rows_sorted = sorted(rows, key=lambda o: (round(o["local_coverage_gap"], 2), o["velocity"]))
    for i, o in enumerate(rows_sorted):
        x, y = o["velocity"], o["local_coverage_gap"]
        ax.scatter(x, y, s=120 + 600 * o["final_score"], color=CONF_COLORS.get(o["confidence"], "#999"), alpha=0.7, edgecolors="k", linewidths=0.5)
        dy = 9 if i % 2 == 0 else -14
        ax.annotate(o["name"], (x, y), fontsize=7, xytext=(7, dy), textcoords="offset points",
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="grey"))
    ax.axhline(0.5, color="grey", ls="--", lw=0.8)
    ax.axvline(0.5, color="grey", ls="--", lw=0.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Velocity (recency / acceleration) →")
    ax.set_ylabel(f"{gap_label} →")
    ax.set_title("Whitespace map — top-right = rising AND uncovered locally = best buys")
    ax.text(0.97, 1.02, "BUY ZONE", ha="right", color="#2a9d8f", fontweight="bold", fontsize=11)
    plt.tight_layout()
    return ax


# ─── 3. transfer radar for one opportunity ───────────────────────────────────
def transfer_radar(opp: dict, scenario: ScenarioProfile):
    dims = opp.get("transfer_dimensions") or {}
    vals = [dims.get(d, 0.0) for d in _DIMS]
    labels = [d.replace("_", "\n") for d in _DIMS]
    angles = np.linspace(0, 2 * np.pi, len(_DIMS), endpoint=False).tolist()
    vals_c, angles_c = vals + vals[:1], angles + angles[:1]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"polar": True})
    ax.plot(angles_c, vals_c, color="#264653", lw=2)
    ax.fill(angles_c, vals_c, color="#2a9d8f", alpha=0.25)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title(f"{opp['name']}\n{scenario.label('transfer_score', 'Transfer score')}: {opp['transfer_score']:.0f}/100", fontsize=10)
    plt.tight_layout()
    return ax


# ─── 4. blank-shelf coverage table ───────────────────────────────────────────
def blank_shelf_table(opps: list[dict], scenario: ScenarioProfile, category: str | None = None, top: int = 6) -> pd.DataFrame:
    locals_ = [c.name for c in scenario.local_competitors]
    refs = [r.name for r in scenario.reference_retailers]
    rows = sorted(_filter(live(opps), category), key=lambda o: o["final_score"], reverse=True)[:top]
    records = []
    for o in rows:
        stockers = {s["source"] for s in o["signals"] if s["source_type"] == "competitor_assortment"}
        rec = {"opportunity": o["name"]}
        for r in refs:
            rec[f"{r} (ref)"] = "✓" if r in stockers else "·"
        for lc in locals_:
            rec[f"{lc} (CH)"] = "✓" if lc in stockers else "—"
        records.append(rec)
    return pd.DataFrame(records).set_index("opportunity")


# ─── 5. graveyard ────────────────────────────────────────────────────────────
def graveyard_table(opps: list[dict]) -> pd.DataFrame:
    rows = [{"discarded signal": o["name"], "why filtered out": o.get("discard_reason", "")} for o in dead(opps)]
    return pd.DataFrame(rows).set_index("discarded signal") if rows else pd.DataFrame()


# ─── 6. hero card (text) ─────────────────────────────────────────────────────
def hero_markdown(opp: dict, scenario: ScenarioProfile) -> str:
    by_type: dict[str, list[str]] = {}
    for s in opp["signals"]:
        if s.get("url"):
            by_type.setdefault(s["source_type"], []).append(f"[{s['source']}]({s['url']})")
    ev = "\n".join(f"- **{t.replace('_', ' ')}**: " + ", ".join(sorted(set(v))) for t, v in by_type.items())
    return (
        f"### 🥇 {opp['name']}\n\n"
        f"**{scenario.label('transfer_score', 'Transfer score')}:** {opp['transfer_score']:.0f}/100 · "
        f"**Confidence:** {opp['confidence']} · **Coverage:** {opp['coverage_status'].replace('_', ' ')} · "
        f"**Final score:** {opp['final_score']:.2f}\n\n"
        f"**Why now:** {opp.get('why_now', '')}\n\n"
        f"**Transferability:** {opp.get('transferability', '')}\n\n"
        f"**Recommended action:** {opp.get('recommended_action', '')}\n\n"
        f"**Risks:** {opp.get('risks', '')}\n\n"
        f"**Evidence:**\n{ev}"
    )


def get_scenario(scenario_id: str = "swiss_outdoor") -> ScenarioProfile:
    return load_scenario(f"config/scenarios/{scenario_id}.yaml")
