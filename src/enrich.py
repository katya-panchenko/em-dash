"""Enrichment layer = the Claude reasoning step (Enrich + Narrative).

For each opportunity, score the 5 transfer-profile dimensions (0..1) with
reasoning, and write why-now / transferability / recommended_action / risks, plus
an executive-summary narrative. The deterministic weights + composite (score.py)
keep the *rankings* defensible; Claude supplies the *judgment*.

Claude is used when ANTHROPIC_API_KEY is set and the `anthropic` package is
installed; otherwise a transparent rule-based fallback runs so the pipeline works
offline and for free. No autonomous opportunity discovery (out of scope).
"""

from __future__ import annotations

import json
import os

from src.schema import Opportunity, SourceType, TransferDimensions
from src.scenario import ScenarioProfile

_DIM_LABELS = {
    "market_context_fit": "market-context fit",
    "legitimacy_threshold": "legitimacy",
    "buyer_risk_tolerance": "buyer risk tolerance",
    "commercial_readiness": "commercial readiness",
    "durability_expectation": "durability expectation",
}
_EU_MARKETS = {"DE", "FR", "IT", "AT", "EU", "UK", "DACH"}


def _text(opp: Opportunity) -> str:
    parts = [opp.name]
    for s in opp.signals:
        parts += [s.keyword or "", s.notes or "", s.source, (s.signal_flavor.value if s.signal_flavor else "")]
    return " ".join(parts).lower()


# ─── Deterministic fallback ──────────────────────────────────────────────────
def deterministic_dimensions(opp: Opportunity, scenario: ScenarioProfile) -> TransferDimensions:
    text = _text(opp)
    ref_names = {r.name.lower() for r in scenario.reference_retailers}
    has_eu_proof = any(
        s.source_type == SourceType.competitor_assortment
        and s.market in _EU_MARKETS
        and s.source.lower() in ref_names
        for s in opp.signals
    )
    has_competitor = any(s.source_type == SourceType.competitor_assortment for s in opp.signals)
    has_community = any(s.source_type == SourceType.community_forum for s in opp.signals)

    if "desert" in text:
        mcf = 0.2
    elif any(k in text for k in ("gorpcore", "aesthetic", "style")):
        mcf = 0.6
    else:
        mcf = 0.7

    if any(k in text for k in ("influencer", "collab", "gimmick", "tiktok", "viral")):
        leg = 0.2
    elif has_competitor and has_community:
        leg = 0.85
    else:
        leg = 0.55

    brt = 0.8 if has_eu_proof else (0.5 if opp.commercial_proof > 0 else 0.4)
    cr = max(0.2, opp.commercial_proof)

    if any(k in text for k in ("pfas", "repair", "durable", "durability")):
        dur = 0.85
    elif any(k in text for k in ("gimmick", "disposable")):
        dur = 0.3
    else:
        dur = 0.6

    return TransferDimensions(
        market_context_fit=mcf,
        legitimacy_threshold=leg,
        buyer_risk_tolerance=brt,
        commercial_readiness=cr,
        durability_expectation=dur,
    )


def _trickle_note(opp: Opportunity) -> str | None:
    text = _text(opp)
    functional = any(k in text for k in ("technical", "functional", "fabric", "membrane", "utility", "shell", "performance", "gorpcore"))
    collabs = sorted({s.collab_partner for s in opp.signals if s.collab_partner})
    if opp.early_watch:
        return "Runway/luxury-only with no mass-market uptake yet — decorative, not functional; too soon to call."
    if opp.luxury_trickle:
        bridge = f" collab bridge ({', '.join(collabs)})" if collabs else ""
        kind = "functional/technical" if functional else "aesthetic"
        return f"Luxury→mass trickle in motion:{bridge}; {kind} and corroborated by rising mass demand → likely to reach CH."
    return None


def _narrative(opp: Opportunity, scenario: ScenarioProfile) -> dict:
    dims = opp.transfer_dimensions
    origin = [m for m in opp.markets if m in scenario.reference_markets]
    types = sorted(t.value.replace("_", " ") for t in opp.source_types)
    top = max(dims.model_fields, key=lambda d: getattr(dims, d))
    weak = min(dims.model_fields, key=lambda d: getattr(dims, d))
    target = scenario.target_market
    trickle = _trickle_note(opp)

    # ── declining → cooling / early-warning framing (no buy) ──
    if opp.direction.value == "declining":
        why_now = (
            f"Cooling: search/community momentum is negative ({opp.momentum:+.0%}) in "
            f"{', '.join(origin) or 'lead markets'}, corroborated by {len(opp.source_types)} source types. "
            f"Lead-market cooling typically reaches {target}/DACH next."
        )
        transferability = f"Cooling score {opp.cooling_score:.2f} — a forward warning for the {target} assortment."
        action = "Hold reorders and monitor for clearance timing; do not expand this line."
        risks = "Decline may stall or reverse; confirm against sell-through before markdowns."
        return {"why_now": why_now, "transferability": transferability, "recommended_action": action,
                "risks": risks, "trickle_note": trickle}

    # ── early-watch (luxury-only) → not a buy yet ──
    if opp.early_watch:
        return {
            "why_now": f"Luxury/runway signal only ({', '.join(opp.brands) or 'designer'}), no mass-market corroboration yet.",
            "transferability": "Too early to call — watch for a rising search/community signal before acting.",
            "recommended_action": "Watch only; revisit if mass demand starts moving.",
            "risks": "Runway trends often stay niche; high chance it never reaches mass outdoor.",
            "trickle_note": trickle,
        }

    # ── rising buy ──
    why_now = (
        f"Rising in {', '.join(origin) or 'origin markets'} (velocity {opp.velocity:.0%}); "
        f"{opp.coverage_status.value.replace('_', ' ')} on {target}/DACH shelves; "
        f"corroborated by {len(opp.source_types)} source types ({', '.join(types)})."
    )
    transferability = (
        f"Transfer {opp.transfer_score:.0f}/100 — strongest on {_DIM_LABELS[top]}, "
        f"weakest on {_DIM_LABELS[weak]}."
    )
    if opp.confidence.value == "high" and opp.transfer_score >= 60:
        action = "Scout 2 EU-distributed brands; test-buy 20 units in Zürich + Bern stores."
    elif opp.transfer_score >= scenario.transfer_profile.discard_threshold:
        action = "Request supplier samples; monitor CH search + competitor shelves for one quarter."
    else:
        action = "Monitor only — insufficient proof for a CH buy."
    if opp.trendsetter_backed:
        action += f" Trendsetter-backed ({opp.top_brand})."
    risks = f"Weakest dimension: {_DIM_LABELS[weak]}."
    if opp.commercial_proof == 0:
        risks += " No reference-retailer / EU distribution proof yet."
    if len(opp.source_types) < 2:
        risks += " Single-source signal — needs corroboration."
    return {"why_now": why_now, "transferability": transferability, "recommended_action": action,
            "risks": risks, "trickle_note": trickle}


# ─── Claude path ─────────────────────────────────────────────────────────────
def _claude_available() -> bool:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _claude_enrich(opps: list[Opportunity], scenario: ScenarioProfile) -> dict | None:
    """One batched call: score dimensions + narrative per opp + exec summary.
    Returns {opportunity_id: {...}, "_summary": str} or None on failure."""
    import anthropic

    payload = [
        {
            "id": o.opportunity_id,
            "name": o.name,
            "category": o.category,
            "markets": o.markets,
            "source_types": [t.value for t in o.source_types],
            "direction": o.direction.value,
            "momentum": o.momentum,
            "luxury_trickle": o.luxury_trickle,
            "early_watch": o.early_watch,
            "top_brand": o.top_brand,
            "coverage_status": o.coverage_status.value,
            "local_coverage_gap": o.local_coverage_gap,
            "commercial_proof": o.commercial_proof,
            "evidence": [
                {"source": s.source, "market": s.market, "note": s.notes, "flavor": s.signal_flavor.value if s.signal_flavor else None}
                for s in o.signals
            ],
        }
        for o in opps
    ]
    dims_help = ", ".join(f"{k} ({v})" for k, v in scenario.transfer_profile.dimensions.items())
    prompt = (
        f"You are a buying analyst for {scenario.display_name} (target market {scenario.target_market}).\n"
        f"For EACH opportunity, score these transfer dimensions 0..1 (how well a global trend transfers to "
        f"{scenario.target_market}/DACH): {dims_help}. Then write a one-sentence why_now, a transferability "
        f"note, a concrete recommended_action, and risks.\n"
        f"IMPORTANT framing by field:\n"
        f"- If direction=='declining': why_now explains why it's COOLING; recommended_action is HOLD/monitor "
        f"(cut reorders / clearance timing), NEVER a buy.\n"
        f"- If luxury_trickle==true: add a trickle_note on whether it's functional/technical vs decorative and "
        f"name the collab bridge.\n"
        f"- If early_watch==true: it's luxury/runway-only with no mass uptake — recommended_action is WATCH only.\n"
        f"Legitimacy markers that matter: {scenario.legitimacy_markers}.\n"
        f"Keep every text field to ONE concise sentence.\n"
        f"Return STRICT JSON only (no prose, no markdown fence): {{\"opportunities\":[{{\"id\":..,"
        f"\"dimensions\":{{..5 keys..}},\"why_now\":..,\"transferability\":..,\"recommended_action\":..,"
        f"\"risks\":..,\"trickle_note\":..(or null)}}],\"summary\":\"<3-5 sentence exec summary>\"}}\n\n"
        f"Opportunities:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    data = json.loads(raw)
    out = {o["id"]: o for o in data.get("opportunities", [])}
    out["_summary"] = data.get("summary", "")
    return out


# ─── Public API ──────────────────────────────────────────────────────────────
def enrich(opps: list[Opportunity], scenario: ScenarioProfile, use_llm: bool = True, top_n: int = 15) -> str | None:
    """Set transfer dimensions/score + narrative on each opp; return the LLM exec
    summary if Claude produced one, else None (build it post-finalize via
    exec_summary()).

    Claude enriches the top_n by raw_score (cost control); the rest use the
    deterministic fallback.
    """
    ranked = sorted(opps, key=lambda o: o.raw_score, reverse=True)
    llm_data = None
    if use_llm and _claude_available():
        try:
            llm_data = _claude_enrich(ranked[:top_n], scenario)
            print(f"[enrich] Claude enriched top {min(top_n, len(ranked))} opportunities")
        except Exception as e:  # noqa: BLE001
            print(f"[enrich] Claude failed ({type(e).__name__}: {e}); using deterministic fallback")
    else:
        print("[enrich] no Claude key/package — using deterministic fallback")

    weights = scenario.transfer_profile.dimensions
    for opp in opps:
        rec = (llm_data or {}).get(opp.opportunity_id)
        if rec and isinstance(rec.get("dimensions"), dict):
            try:
                opp.transfer_dimensions = TransferDimensions.model_validate(rec["dimensions"])
            except Exception:
                opp.transfer_dimensions = deterministic_dimensions(opp, scenario)
        else:
            opp.transfer_dimensions = deterministic_dimensions(opp, scenario)
        opp.transfer_score = opp.transfer_dimensions.weighted_score(weights)

        if rec:
            opp.why_now = rec.get("why_now")
            opp.transferability = rec.get("transferability")
            opp.recommended_action = rec.get("recommended_action")
            opp.risks = rec.get("risks")
            opp.trickle_note = rec.get("trickle_note") or _trickle_note(opp)
        else:
            n = _narrative(opp, scenario)
            opp.why_now, opp.transferability = n["why_now"], n["transferability"]
            opp.recommended_action, opp.risks = n["recommended_action"], n["risks"]
            opp.trickle_note = n.get("trickle_note")

    if llm_data and llm_data.get("_summary"):
        return llm_data["_summary"]
    return None


def exec_summary(opps: list[Opportunity], scenario: ScenarioProfile, llm_summary: str | None = None) -> str:
    """Final exec summary. Use the LLM's if available, else a deterministic one.
    Call AFTER finalize() so final_score / discarded are set."""
    if llm_summary:
        return llm_summary
    return _exec_summary_fallback(opps, scenario)


def _exec_summary_fallback(opps: list[Opportunity], scenario: ScenarioProfile) -> str:
    live = sorted((o for o in opps if not o.discarded), key=lambda o: o.final_score, reverse=True)
    top = live[:3]
    killed = [o for o in opps if o.discarded]
    names = "; ".join(f"{o.name} ({o.transfer_score:.0f}/100, {o.confidence.value})" for o in top)
    return (
        f"For {scenario.display_name}, {len(live)} opportunities cleared the bar and {len(killed)} were "
        f"discarded as noise. Top picks: {names}. Each is rising in origin markets (incl. Asia), thin on "
        f"{scenario.target_market} shelves, and corroborated across multiple source types — the clearest "
        f"signal-to-shelf gaps for the buying team to act on now."
    )
