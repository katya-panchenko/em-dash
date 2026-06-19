"""Export dashboard figures to outputs/<scenario>/figures/ for the submission.

    python scripts/export_figures.py [scenario_id]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src import report  # noqa: E402


def main(scenario_id: str = "swiss_outdoor") -> None:
    opps, _ = report.load_results(scenario_id)
    scn = report.get_scenario(scenario_id)
    ranked = sorted(report.live(opps), key=lambda o: o["final_score"], reverse=True)
    out = Path("outputs") / scenario_id / "figures"
    out.mkdir(parents=True, exist_ok=True)

    report.plot_ranked(opps, scn)
    plt.savefig(out / "ranked.png", dpi=130, bbox_inches="tight")
    plt.close()

    report.plot_whitespace(opps, scn)
    plt.savefig(out / "whitespace.png", dpi=130, bbox_inches="tight")
    plt.close()

    if ranked:
        report.transfer_radar(ranked[0], scn)
        plt.savefig(out / "hero_radar.png", dpi=130, bbox_inches="tight")
        plt.close()

    print(f"Wrote figures → {out}/ (ranked.png, whitespace.png, hero_radar.png)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "swiss_outdoor")
