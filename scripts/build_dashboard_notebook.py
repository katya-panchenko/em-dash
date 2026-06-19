"""Generate notebooks/dashboard.ipynb (reproducible).

Run from repo root:  python scripts/build_dashboard_notebook.py
Keeps the notebook in version-friendly sync with src/report.py.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md(
        "# 🏔️ Alpine Signal Radar — Opportunity Dashboard\n\n"
        "A **scenario-driven** retail opportunity radar. Pitched on Swiss outdoor, but the engine is "
        "generic — every retailer/community/market specific lives in `config/scenarios/*.yaml`, not in code.\n\n"
        "**Pipeline:** signals → normalize → dedup → score → transfer (CH/DACH) → action.  \n"
        "Run `python -m src.collect_offline` then `python -m src.pipeline` to refresh the artifacts this "
        "notebook reads. *(Claude enrichment is used if `ANTHROPIC_API_KEY` is set; otherwise a deterministic "
        "fallback runs.)*"
    ),
    code(
        "# Setup — switch SCENARIO to render any profile\n"
        "import os, sys\n"
        "# run from repo root so `src` imports and relative artifact paths resolve\n"
        "while not os.path.isdir('src'):\n"
        "    parent = os.path.dirname(os.getcwd())\n"
        "    if parent == os.getcwd():\n"
        "        break\n"
        "    os.chdir(parent)\n"
        "sys.path.insert(0, os.getcwd())\n\n"
        "import matplotlib.pyplot as plt\n"
        "from IPython.display import Markdown, display\n"
        "from src import report\n\n"
        "SCENARIO = 'swiss_outdoor'\n"
        "opps, summary = report.load_results(SCENARIO)\n"
        "scn = report.get_scenario(SCENARIO)\n"
        "ranked = sorted(report.live(opps), key=lambda o: o['final_score'], reverse=True)\n"
        "f\"{len(opps)} opportunities — {len(ranked)} surfaced, {len(report.dead(opps))} discarded\""
    ),
    md("## 1. Executive summary"),
    code("display(Markdown(summary))"),
    md("## 2. Ranked opportunities\nColoured by confidence (multi-source + local gap → high)."),
    code("report.plot_ranked(opps, scn); plt.show()"),
    md("## 3. Hero opportunity\nThe #1 signal-to-shelf gap, with its 5-dimension transfer profile."),
    code(
        "hero = ranked[0]\n"
        "display(Markdown(report.hero_markdown(hero, scn)))\n"
        "report.transfer_radar(hero, scn); plt.show()"
    ),
    md(
        "## 4. Blank shelf — who stocks it?\n"
        "Reference retailers (origin markets) vs local CH competitors. `✓` stocked · `—` absent locally "
        "(= the gap) · `·` not observed."
    ),
    code("display(report.blank_shelf_table(opps, scn))"),
    md(
        "## 5. Whitespace map\n"
        "Velocity (rising) vs local assortment gap. **Top-right = rising AND uncovered locally = best buys.** "
        "Bubble size = opportunity score."
    ),
    code("report.plot_whitespace(opps, scn); plt.show()"),
    md(
        "## 6. Noise graveyard\n"
        "What the system **rejected**, and why — proof it has judgment, not just hype amplification."
    ),
    code("display(report.graveyard_table(opps))"),
    md(
        "## 7. Within-scenario reuse — category toggle\n"
        "Change `CATEGORY` to `'day_hiking'` and re-run: same engine, different category."
    ),
    code("CATEGORY = 'trail_running'  # try 'day_hiking'\nreport.plot_ranked(opps, scn, category=CATEGORY); plt.show()"),
    md(
        "## 8. Cross-scenario reuse — *config, not code*\n"
        "The whole product retargets to a new market/vertical by editing one YAML. Below: the live Swiss "
        "profile vs the empty template an analyst fills in."
    ),
    code(
        "from pathlib import Path\n"
        "print('── swiss_outdoor.yaml (first 28 lines) ──')\n"
        "print('\\n'.join(Path('config/scenarios/swiss_outdoor.yaml').read_text().splitlines()[:28]))\n"
        "print('\\n── _template.yaml blocks an analyst fills in ──')\n"
        "print('\\n'.join(l for l in Path('config/scenarios/_template.yaml').read_text().splitlines() if l.strip().endswith(':') or l.startswith('# '))[:1200])\n\n"
        "# If a second scenario has been run, show it surfaces too (cross-industry proof):\n"
        "stub = Path('outputs/uk_beauty_stub/opportunities.json')\n"
        "if stub.exists():\n"
        "    o2, s2 = report.load_results('uk_beauty_stub')\n"
        "    print(f'\\nuk_beauty_stub → {len(report.live(o2))} opportunities surfaced from the SAME pipeline')\n"
        "else:\n"
        "    print('\\n(Run: python -m src.pipeline --scenario config/scenarios/uk_beauty_stub.yaml to populate the cross-industry beat)')"
    ),
]

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}

out = Path("notebooks/dashboard.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, str(out))
print(f"Wrote {out} ({len(cells)} cells)")
