# Submission — Alpine Signal Radar

A **scenario-driven retail opportunity radar**. Pitched on Swiss outdoor, but the engine is generic:
every retailer, community, market, and transfer rule lives in a scenario YAML, not in code. Swap the
profile → retarget to any market, category, or industry.

## Team

- Team name: _<fill in>_
- Team members: _<fill in>_
- GitHub fork URL: _<fill in>_
- Demo URL, if any: notebook — [`notebooks/dashboard.ipynb`](notebooks/dashboard.ipynb)
- Video walkthrough URL, if any: _<optional>_

## Summary

We built the full **signal → score → transfer → action** pipeline, plus a notebook dashboard. It
detects emerging outdoor opportunities by fusing five signal types, deduplicating them into candidate
opportunities, scoring each with a transparent composite, judging Swiss/DACH transferability (Claude
reasoning layer, with a deterministic fallback), and emitting ranked, actionable recommendations. The
design directly targets the gap the incumbents (WGSN/Heuritech/EDITED — see
[`docs/research-brief.md`](docs/research-brief.md)) leave: **outdoor-specific, CH/DACH transfer, and an
explicit signal→buy conversion.**

Beyond *rising* trends it also flags **cooling categories** (signed momentum → an early-warning
watchlist, e.g. hydration bladders cooling as filter-flask hydration rises), and ranks **trendsetter
brands** (luxury houses + prestige outdoor leaders) by a computed Brand Influence score — with a
`luxury_runway` source + corroboration gate that separates real high→mass trickle-down from runway noise.

## How To Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# optional: live data + Claude reasoning (works without them via seed + deterministic fallback)
cp .env.example .env   # add ANTHROPIC_API_KEY and/or Reddit creds

# 1) collect signals offline → cache (live where possible, seed fallback)
python -m src.collect_offline --scenario config/scenarios/swiss_outdoor.yaml
# 2) run the pipeline → signals.csv, recommendations.csv, opportunities.json, summary.md
python -m src.pipeline --scenario config/scenarios/swiss_outdoor.yaml
# 3) open the dashboard
jupyter notebook notebooks/dashboard.ipynb
```

Reuse for another vertical (same commands, different profile):

```bash
python -m src.collect_offline --scenario config/scenarios/uk_beauty_stub.yaml
python -m src.pipeline --scenario config/scenarios/uk_beauty_stub.yaml
```

## Inputs

- **Market:** CH / DACH (target); US, UK, DE, JP, KR, CN (origin/early-signal, incl. Asia).
- **Category:** trail running, day hiking (seed keywords in the profile).
- **Sources:** `search_trends` (Google Trends), `community_forum` (Reddit), `competitor_assortment`
  (REI/Bergfreunde vs Transa/Ochsner/Galaxus), `culture_context` (viewership, emerging-business,
  event-anticipation, geo-style-diffusion, segment-trend), `luxury_runway` (luxury×technical collabs,
  runway → mass trickle-down).
- **Trendsetter brands:** configurable list (luxury + prestige outdoor) in the scenario YAML.
- **Languages:** English (+ German/CH local vocabulary via r/SwissHiking).
- **External:** Google Trends, Reddit API, retailer sites, Claude API. All optional — committed seed
  snapshots make the demo reproducible offline.

## Outputs

- **Dashboard:** [`notebooks/dashboard.ipynb`](notebooks/dashboard.ipynb) — ranked chart, hero card +
  transfer radar, blank-shelf table, whitespace map, graveyard, category toggle, cross-scenario beat.
- **Report:** [`outputs/swiss_outdoor/summary.md`](outputs/swiss_outdoor/summary.md) (exec narrative).
- **Structured data:** `outputs/swiss_outdoor/signals.csv`, `recommendations.csv`,
  `cooling_watchlist.csv` (declining), `brand_influence.csv` (ranked trendsetters), `opportunities.json`.
- **Visuals:** `outputs/swiss_outdoor/figures/` (ranked, whitespace, hero radar).

## Ranked Opportunities

Composite: `raw = 0.35·gap + 0.30·corroboration + 0.20·velocity + 0.15·commercial_proof`, then
`final = raw · transfer_score/100`. Confidence = high (≥3 source types + local gap) / medium / low.

| Rank | Opportunity | Evidence | Confidence (transfer) |
| --- | --- | --- | --- |
| 1 | Integrated filter-flask hydration | Stocked at REI + Bergfreunde, **absent** at Transa/Ochsner/Galaxus; search rising US/UK/KR, CH flat; rising threads on r/Ultralight + r/trailrunning | high (79/100) |
| 2 | Single-vessel water filtration | REI stocks (GRAYL), absent in CH; r/Ultralight + r/SwissHiking; US search rising | high (71/100) |
| 3 | Smarter-light minimal-frame packs | REI + Bergfreunde stock, thin at Transa; "smarter light" narrative on r/Ultralight | high (79/100) |
| 4 | PFAS-free repairable shells | EU regulation-driven (DE search), Bergfreunde/Transa partial; r/Ultralight | high (81/100) |
| 5 | Challenger trail-running brands | REI stocks, absent CH; r/trailrunning (Mount to Coast); UTMB 2026 event anticipation | high (65/100) |

**Graveyard (discarded as noise):** influencer trail-apparel collab (single source, fails legitimacy);
desert-ultra race vest (single source; transfer 39 < 40, weak market-context fit); TikTok viral
hydration gimmick (single source; transfer 36 < 40, weak legitimacy).

## Downward Trends & Trendsetter Brands

**Cooling watchlist (early warning)** — declining categories to hold reorders on, e.g. **hydration
bladder packs** (cooling as filter-flask hydration rises — a lifecycle handoff), **maximalist
stack-height shoes**, **legacy PFAS membrane hardshells**. See `cooling_watchlist.csv`.

**Trendsetter brands to watch** (computed influence; see `brand_influence.csv`) — top of the ranking:
**Salomon** (MM6 collab + community + shelf), **Arc'teryx** (Jil Sander collab + PFAS-free leadership),
**On** (Loewe collab), then luxury houses by collab gravity. The **corroboration gate** parks a
luxury-only decorative signal (embellished logo-mania) in "too soon to call" — proving the noise filter.

## Evidence Trail

Per-opportunity evidence URLs are in `recommendations.csv` (`evidence_urls`) and `opportunities.json`.
Seed snapshots with source URLs: `data/seed/swiss_outdoor/*.json`. Sources include REI, Bergfreunde,
Transa/Ochsner/Galaxus, r/trailrunning, r/Ultralight, r/SwissHiking, Google Trends, UTMB, UCI.

## Reusability

The engine is generic; only scenario YAML changes. Proven by `uk_beauty_stub` — the **same pipeline**
surfaces PDRN salmon-DNA serum (KR→UK transfer) as the top beauty opportunity.

| Change | Edit | Rerun |
| --- | --- | --- |
| New country | `target_market`, `reference_markets` | `collect_offline` + `pipeline` |
| New vertical | `categories`, `community_sources`, `transfer_profile` weights | same |
| New competitors | `local_competitors`, `reference_retailers` | same |
| Stricter filtering | `transfer_profile.discard_threshold`, weights | `pipeline` only |
| New source type | add a connector in `src/connectors/` + register | same |

See [`config/scenarios/_template.yaml`](config/scenarios/_template.yaml) (every field commented).

## Known Limitations

- Demo runs on committed **seed snapshots** (Claude-research-assisted) for `competitor_assortment` and
  `culture_context`; live connectors exist for `search_trends` (pytrends) and `community_forum` (praw)
  but are run offline before the demo. Seed values are illustrative, not a live market pull.
- Transfer scoring uses Claude when a key is present, else a transparent rule-based fallback.
- `trade_publication` (ISPO) and autonomous LLM opportunity *discovery* are documented but not built.
- Single category family (outdoor) implemented; beauty is a 2-opportunity stub.

## Architecture Notes

```
config/scenarios/*.yaml   scenario profiles (swiss_outdoor, _template, uk_beauty_stub)
src/
  schema.py               pydantic SignalRow / Opportunity / RecommendationRow + source_type enum
  scenario.py             load + validate a profile
  connectors/             search_trends · community_forum · competitor_assortment · culture_context
  collect_offline.py      run connectors → outputs/<scn>/<src>.json cache
  dedup.py                cluster signals into opportunities (corroboration = confidence)
  score.py                deterministic composite + discard rules
  enrich.py               Claude transfer-dimension scoring + narrative (+ deterministic fallback)
  pipeline.py             orchestrate → signals.csv, recommendations.csv, opportunities.json, summary.md
  report.py               dashboard plots/tables
notebooks/dashboard.ipynb the demo
```

Data flow: **connectors → normalize (schema) → dedup → score → enrich (transfer + narrative) →
finalize (final score + discard) → rank → export → dashboard.** Rankings stay on the transparent
composite (defensible to a jury); Claude supplies the transfer judgment and narrative.
