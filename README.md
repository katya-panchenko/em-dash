# TellTale — a scenario-driven retail opportunity radar

> **HerCode × Zenline AI — B2B challenge submission.**
> Turn noisy market signals into one clear answer: *what should the retailer stock, test, or monitor next?*
> The engine is generic — Swiss outdoor is just the loaded scenario. Swap the YAML, retarget any
> market or category.

**🔗 Live dashboard:** https://melodious-kashata-b0700b.netlify.app

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python -m src.collect_offline --scenario config/scenarios/swiss_outdoor.yaml
python -m src.pipeline        --scenario config/scenarios/swiss_outdoor.yaml
jupyter notebook notebooks/dashboard.ipynb
```

> The team write-up, approach summary, inputs, known limitations, and architecture notes live in
> **[`SUBMISSION.md`](SUBMISSION.md)**. This README covers the rest of the required deliverables and
> where to find each one.

---

## Required deliverables — where to find them

| Deliverable | Location |
| --- | --- |
| Code, scripts, notebooks, app | [`src/`](src/), [`scripts/`](scripts/), [`notebooks/dashboard.ipynb`](notebooks/dashboard.ipynb), [`site/`](site/) |
| Setup & run instructions | [Quickstart](#setup--run) below |
| Evidence sources (with URLs) | [Evidence sources](#evidence-sources) below · per-opportunity `evidence_urls` in [`outputs/swiss_outdoor/recommendations.csv`](outputs/swiss_outdoor/recommendations.csv) · raw snapshots in [`data/seed/`](data/seed/) |
| Ranked opportunities (confidence, risks, next actions) | [Ranked opportunities](#ranked-opportunities) below · full detail in [`recommendations.csv`](outputs/swiss_outdoor/recommendations.csv) |
| Dashboard / visualization | [Live site](https://melodious-kashata-b0700b.netlify.app) · [`notebooks/dashboard.ipynb`](notebooks/dashboard.ipynb) · [`outputs/swiss_outdoor/figures/`](outputs/swiss_outdoor/figures/) |
| Completed `SUBMISSION.md` | [`SUBMISSION.md`](SUBMISSION.md) |
| Video walkthrough (optional) | _add link in [`SUBMISSION.md`](SUBMISSION.md) if recorded_ |
| No committed secrets | `.env` is gitignored; see [Secrets](#secrets) |

Challenge brief and judging rubric (unchanged from the organizers): [`docs/challenge.md`](docs/challenge.md),
[`docs/evaluation.md`](docs/evaluation.md), [`docs/data-contract.md`](docs/data-contract.md).

---

## Setup & run

**Requirements:** Python 3.11+ (built on 3.13). All dependencies are in
[`requirements.txt`](requirements.txt).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional: live data + Claude reasoning. Runs fully offline without them
# (committed seed snapshots + deterministic fallback).
cp .env.example .env   # add ANTHROPIC_API_KEY and/or Reddit API creds

# 1) collect signals → outputs/<scenario>/<source>.json cache
python -m src.collect_offline --scenario config/scenarios/swiss_outdoor.yaml
# 2) run the pipeline → signals.csv, recommendations.csv, opportunities.json, summary.md
python -m src.pipeline        --scenario config/scenarios/swiss_outdoor.yaml
# 3) open the dashboard notebook
jupyter notebook notebooks/dashboard.ipynb
```

**Web dashboard (local):**

```bash
cd site && bun install && bun dev     # fetches the web/<scenario>.json feed
```

**Run it for a different vertical (same commands, different profile):**

```bash
python -m src.collect_offline --scenario config/scenarios/uk_beauty_stub.yaml
python -m src.pipeline        --scenario config/scenarios/uk_beauty_stub.yaml
```

---

## What's in the repo

```
config/scenarios/   scenario profiles — swiss_outdoor, uk_beauty_stub, _template (every field commented)
data/seed/          committed source snapshots → reproducible offline demo
src/
  schema.py         pydantic SignalRow / Opportunity / RecommendationRow + source-type enum
  scenario.py       load + validate a profile
  connectors/       search_trends · community_forum · competitor_assortment · culture_context · luxury_runway
  collect_offline.py  run connectors → cache
  dedup.py          cluster signals into opportunities (corroboration = confidence)
  score.py          transparent composite + discard rules
  enrich.py         Claude transfer scoring + narrative (+ deterministic fallback)
  brand_influence.py  rank trendsetter brands
  pipeline.py       orchestrate → CSV / JSON / summary
  report.py         dashboard plots + tables
notebooks/dashboard.ipynb   the demo notebook
scripts/            export figures, build notebook, export web feed
site/               React / TanStack web dashboard (deployed to Netlify)
outputs/<scenario>/ generated artifacts (CSV, JSON, figures, summary.md)
```

Data flow: **connectors → normalize (schema) → dedup → score → enrich (transfer + narrative) →
finalize (final score + discard) → rank → export → dashboard.**

---

## Dashboard / visualization

- **Live web dashboard:** https://melodious-kashata-b0700b.netlify.app — buy signals, downward
  (cooling) trends, trendsetter brands, early-watch, whitespace map, and the discarded-noise graveyard.
- **Notebook:** [`notebooks/dashboard.ipynb`](notebooks/dashboard.ipynb) — ranked chart, hero card +
  transfer radar, blank-shelf table, whitespace map, graveyard, category toggle, cross-scenario view.
- **Static figures:** [`outputs/swiss_outdoor/figures/`](outputs/swiss_outdoor/figures/) — `ranked.png`,
  `whitespace.png`, `hero_radar.png`.

### Updating the live website (for now)

The deployed site does **not** rebuild from the pipeline automatically. At runtime it fetches a single
JSON feed straight from GitHub:

```
https://raw.githubusercontent.com/katya-panchenko/em-dash/main/web/swiss_outdoor.json
```

(hardcoded as `DATA_URL` in [`site/src/routes/index.tsx`](site/src/routes/index.tsx)). So to push new
numbers to the live dashboard, regenerate that feed and commit it to `main`:

```bash
# 1) regenerate the pipeline outputs
python -m src.collect_offline --scenario config/scenarios/swiss_outdoor.yaml
python -m src.pipeline        --scenario config/scenarios/swiss_outdoor.yaml

# 2) rebuild the web feed from outputs/ → web/swiss_outdoor.json
python scripts/export_web.py swiss_outdoor

# 3) commit + push the updated feed to main (the site reads it live — no Netlify rebuild needed)
git add web/swiss_outdoor.json
git commit -m "Update web feed"
git push origin main
```

The site picks up the change on the next page load (allow a minute or two for the raw-GitHub CDN cache).
No `bun build` or redeploy is required for a data-only update — only a code/UI change in `site/` needs a
redeploy.

---

## Ranked opportunities

Composite score: `raw = 0.35·gap + 0.30·corroboration + 0.20·velocity + 0.15·commercial_proof`,
then `final = raw · transfer_score/100`. Confidence = high (≥3 source types + local gap) / medium / low.
Full evidence URLs and per-row detail are in
[`recommendations.csv`](outputs/swiss_outdoor/recommendations.csv).

| # | Opportunity | First market | Transfer | Conf. | Next action | Main risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Integrated filter-flask hydration | US | 80/100 | high | Initial buy of Salomon filter-flask SKUs for trail-running + hut hikers ahead of the CH curve | Filter efficacy/regulatory + consumable-replacement logistics |
| 2 | Single-vessel water filtration | US | 71/100 | high | Trial a focused single-vessel bottle range tied to day-hiking / hut routes | No clear anchor brand; rides the filter-flask macro |
| 3 | Challenger trail-running brands | US | 72/100 | high | Secure EU distribution for one race-proven challenger ahead of UTMB 2026 | Supply timing could miss the event spike |
| 4 | PFAS-free repairable shells | DE | 77/100 | high | Build PFAS-free repairable shell range (Arc'teryx-led) + repair-service offer | Premium price needs substantiated durability claims |
| 5 | Smarter-light minimal-frame packs | US | 72/100 | high | Expand sub-1kg framed packs to close the partial Transa gap | Partial coverage → incremental demand may be thin |

Opportunities #6–#10 (carbon-plate shoes, gorpcore technical-aesthetic apparel, women's gravel/trail,
kids' trail footwear, trail nutrition) and the full risk/action/evidence detail are in
[`recommendations.csv`](outputs/swiss_outdoor/recommendations.csv).

**Beyond rising buys, the system also surfaces:**
- **Cooling watchlist** (hold reorders): hydration bladder packs, maximalist stack-height shoes,
  legacy PFAS membrane hardshells — [`cooling_watchlist.csv`](outputs/swiss_outdoor/cooling_watchlist.csv).
- **Trendsetter brands** by computed influence: Salomon, Arc'teryx, On, then luxury houses —
  [`brand_influence.csv`](outputs/swiss_outdoor/brand_influence.csv).
- **Graveyard** of signals discarded as noise (single-source / failed transfer / runway-only) — in
  [`opportunities.json`](outputs/swiss_outdoor/opportunities.json).

---

## Evidence sources

Signals are fused across five source types; each signal row carries its own `url`, market, and notes
(schema in [`docs/data-contract.md`](docs/data-contract.md), raw snapshots in
[`data/seed/swiss_outdoor/`](data/seed/swiss_outdoor/)).

| Source type | What it provides | Examples |
| --- | --- | --- |
| `search_trends` | Cross-market momentum (origin rising, CH flat = open transfer window) | Google Trends (US/UK/DE/JP/KR/CN vs CH) |
| `community_forum` | Legitimacy + weak signals, local CH vocabulary | r/trailrunning, r/Ultralight, r/SwissHiking |
| `competitor_assortment` | Local-vs-reference shelf gap, brand, bestseller rank | Transa, Ochsner Sport, Galaxus · REI, Bergfreunde |
| `culture_context` | Leading indicators before search/sales | viewership, emerging brands, event anticipation (UTMB, UCI) |
| `luxury_runway` | High→mass trickle-down, collab gravity | runway × technical collabs (Vogue Business, Hypebeast) |

Per-opportunity evidence URLs are in the `evidence_urls` column of
[`recommendations.csv`](outputs/swiss_outdoor/recommendations.csv) and in
[`opportunities.json`](outputs/swiss_outdoor/opportunities.json).

---

## Reusability

The engine is generic; only the scenario YAML changes. Proven by `uk_beauty_stub`, where the **same
pipeline** surfaces PDRN salmon-DNA serum (KR→UK transfer) as the top beauty opportunity.

| Change | Edit | Rerun |
| --- | --- | --- |
| New country | `target_market`, `reference_markets` | `collect_offline` + `pipeline` |
| New vertical | `categories`, `community_sources`, `transfer_profile` weights | same |
| New competitors | `local_competitors`, `reference_retailers` | same |
| Stricter filtering | `transfer_profile.discard_threshold`, weights | `pipeline` only |
| New source type | add a connector in `src/connectors/` + register | same |

See [`config/scenarios/_template.yaml`](config/scenarios/_template.yaml) — every field commented.

---

## Secrets

No API keys, tokens, or credentials are committed. `.env` is gitignored (only
[`.env.example`](.env.example) is tracked). All external services — Google Trends, Reddit API, Claude
API — are optional; the demo is fully reproducible offline from committed seed snapshots.
