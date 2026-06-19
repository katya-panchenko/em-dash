# Research Brief: How Retailers Detect Emerging Opportunities Today

> **Evidence status:** This brief is distilled from a multi-source web sweep (22 sources →
> 90 extracted claims → 10 synthesized findings). **Adversarial fact-checking was intentionally
> skipped**, so every claim here is an *unverified source extraction* — many figures come from
> vendor marketing or blogs. Confidence is capped at **medium** and flagged per point. Treat
> accuracy percentages, pricing, and client lists as self-reported and confirm before relying on them.

## TL;DR

Retailers spot emerging product, material, and brand opportunities by **fusing external signals**
(search trends, social/creator imagery, marketplace & competitor scans, trade shows, weather,
supplier intel) with **internal POS/sales data**, scoring the result on an AI vendor platform, and
translating survivors into buy decisions. The repeatable pattern is:

```
signals → normalize → score (noise vs. real demand) → transferability → buy / test / monitor
```

Outside fashion this is called **demand sensing**, and it is the pattern that transfers best to
outdoor / sporting-goods retail.

## 1. Signals & method

- **Signal fusion** — external signals blended with internal POS/sales is the consistent backbone. *(medium)*
- **Demand sensing** — blend POS + promo calendars + macro indicators + social listening + search
  trends + foot traffic to refine short-term forecasts (RELEX, corroborated independently). This is
  the **non-fashion** approach most applicable to outdoor. *(medium)*
- **Noise vs. real demand** — separated via confidence/stage scoring (Spate, Trendalytics) and, for
  Heuritech, deep learning + Hidden Markov models to isolate early signals from noise. *(low–medium)*
- **Clean data pipeline** (consolidating POS feeds, reconciling field names) cited as the foundational
  prerequisite for accurate forecasting. *(low — single blog)*

## 2. Vendor landscape

| Vendor | What it does | Category | Pricing (self-reported) | Conf. |
|---|---|---|---|---|
| **WGSN** | Expert-validated forecasting + buyer tools (TrendCurve AI, Opportunity Calculator, Assortment Builder); sizes opportunities from your own data, calibrates vs. historical sales | Fashion forecasting + buying | ~$25k/yr | medium |
| **Heuritech** | Computer vision on millions of daily social images, ~2,000 attributes, up to 24-month forecasts | Fashion trend prediction | ~€12k/yr | medium |
| **Trendalytics / Spate** | Predictive search + social aggregation with confidence/stage scoring; Spate cites 900B Google signals + 200M TikTok/IG posts, 72% accuracy | Search/social trend detection | Spate START ~$59/mo | low |
| **EDITED** | Real-time SKU-level pricing, inventory & assortment intelligence (30M+ apparel SKUs, 90k+ brands) — competitive benchmarking, *not* creative forecasting | Retail analytics | — | medium |
| **RELEX** | Demand sensing — POS + external signals | Cross-industry forecasting | — | medium |

A 2018 academic study comparing WGSN (human) vs. EDITED (big-data) womenswear forecasts found
similar results for color/pattern but weaker (<50%) for fabric/shape — tiny sample (20 forecasts)
and dated. *(low)*

## 3. Organization & decision-making

- Buying orgs split into **buying / planning / operations**; **small retailers combine buyer+planner**,
  large ones separate them. *(medium)*
- **Trade-show attendance** is an explicit, named part of the buying process. *(low)*

## 4. The DACH / outdoor angle (thinnest evidence)

Sources are overwhelmingly **fashion-centric**. The one concrete outdoor/DACH data point:
**Intersport Germany** using POS to rank categories — running +21%, bike +20%, sports-style +16%
as strongest May categories (ISPO). *(low)*

## 5. Gaps = our differentiation targets

The synthesis surfaced four open questions that are exactly where a hackathon build can add value:

1. **What Swiss/DACH _outdoor_ retailers actually use** — the vendor world is fashion-first; outdoor is underserved.
2. **How a signal becomes a buy** — scoring thresholds, sign-off, open-to-buy, human vs. AI override — poorly documented.
3. **Independently measured accuracy** vs. self-reported vendor figures.
4. **How small/independent buyers** detect opportunities without enterprise subscriptions — low-cost signals.

## 6. Implication for our system

The professional pattern maps almost 1:1 onto the challenge:

| Pro practice | Our system component |
|---|---|
| Fuse external + internal signals | Signal ingestion → normalized signal rows (`docs/data-contract.md`) |
| Confidence/stage scoring to filter noise | Opportunity scoring module |
| Demand sensing across markets | Cross-market signal comparison |
| (Missing) explicit CH/DACH transfer | **Transferability assessment — our differentiator** |
| Trend → buy decision | Recommendation rows with `recommended_action` |

We win by covering the gaps the incumbents leave: **outdoor-specific, DACH-localized, and an explicit
signal → buy-decision conversion.**

## Source list

Primary/secondary (higher trust): wgsn.com, heuritech.com, spate.nyc, relexsolutions.com,
udspace.udel.edu (academic), courses.lumenlearning.com, retaildogma.com, ispo.com.
Blog/lower trust: straive.com, gorgeautiful.com, algo.com, toolio.com, gitnux.org, tellius.com.
Full per-claim source mapping is in the workflow output; none were adversarially verified.
