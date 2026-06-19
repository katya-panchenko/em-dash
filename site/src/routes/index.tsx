import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  ReferenceLine,
  Tooltip,
} from "recharts";
import {
  Mountain,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  AlertTriangle,
  Target,
  Sparkles,
  Calendar,
  MapPin,
  Archive,
  Newspaper,
  Search,
  MessageSquare,
  Store,
  BookOpen,
  ArrowUpRight,
  Info,
  Crown,
  Eye,
  ArrowDownRight,
  AlertCircle,
} from "lucide-react";

const DATA_URL =
  "https://raw.githubusercontent.com/katya-panchenko/em-dash/main/web/swiss_outdoor.json";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Alpine Signal Radar — Swiss Outdoor Retail" },
      {
        name: "description",
        content:
          "Buy signals, cooling categories, and trendsetter intelligence for Swiss outdoor retail buyers.",
      },
      { property: "og:title", content: "Alpine Signal Radar" },
      {
        property: "og:description",
        content: "Swiss outdoor retail opportunity detection.",
      },
    ],
  }),
  component: Index,
});

// ---------- Types ----------
interface Evidence {
  source_type: string;
  source: string;
  market: string;
  url?: string | null;
  note?: string | null;
}
interface Buy {
  rank: number;
  name: string;
  category: string;
  final_score: number;
  transfer_score: number;
  confidence: "high" | "medium" | "low";
  coverage_status: string;
  momentum: number;
  direction?: string;
  trendsetter_backed?: boolean;
  top_brand?: string | null;
  luxury_trickle?: boolean;
  trickle_note?: string | null;
  why_now?: string;
  transferability?: string;
  recommended_action?: string;
  risks?: string;
  evidence: Evidence[];
}
interface Cooling {
  rank: number;
  name: string;
  momentum: number;
  cooling_score: number;
  markets: string[];
  why_cooling: string;
  recommended_action: string;
  evidence: Evidence[];
}
interface Trendsetter {
  rank: number;
  name: string;
  tier: "luxury" | "prestige_outdoor" | string;
  influence_score: number;
  note: string;
  markets: string[];
  evidence_urls?: string[];
}
interface EarlyWatch {
  name: string;
  trickle_note?: string;
  why?: string;
}
interface GraveItem {
  name: string;
  reason: string;
}
interface Dataset {
  display_name: string;
  target_market: string;
  summary: string;
  buys: Buy[];
  cooling: Cooling[];
  trendsetters: Trendsetter[];
  early_watch: EarlyWatch[];
  graveyard: GraveItem[];
}

// ---------- Tokens ----------
const C = {
  paper: "#FFFFFF",
  tint: "#FBFAF8",
  ink: "#37352F",
  inkSoft: "#6B6B66",
  inkFaint: "#9B9A95",
  rule: "#ECEAE5",
  ruleStrong: "#DEDCD7",
  accent: "#2E7D6B",
  accentSoft: "#E8F1EE",
  warn: "#B9791F",
  warnSoft: "#FBF1DF",
  danger: "#B4422E",
  dangerSoft: "#F8E6E0",
  info: "#2F6FB5",
  infoSoft: "#E8F0F9",
};

const SOURCE_TYPE_META: Record<string, { label: string; icon: any }> = {
  search_trends: { label: "Search trends", icon: Search },
  community_forum: { label: "Community forum", icon: MessageSquare },
  competitor_assortment: { label: "Competitor assortment", icon: Store },
  culture_context: { label: "Culture & context", icon: BookOpen },
};

const CATEGORY_LABEL: Record<string, string> = {
  day_hiking: "Day hiking",
  trail_running: "Trail running",
};

function favicon(url: string) {
  try {
    const host = new URL(url).hostname;
    return `https://www.google.com/s2/favicons?domain=${host}&sz=64`;
  } catch {
    return null;
  }
}

function momentumStyle(v: number) {
  if (v > 0.05) return { Icon: TrendingUp, color: C.accent, label: "Rising" };
  if (v < -0.05) return { Icon: TrendingDown, color: C.danger, label: "Cooling" };
  return { Icon: Minus, color: C.warn, label: "Steady" };
}

function confidenceColor(c: string) {
  if (c === "high") return C.accent;
  if (c === "medium") return C.warn;
  return C.danger;
}

function coverageBadge(status: string) {
  if (status === "absent") return { label: "Shelf gap", bg: C.dangerSoft, color: C.danger };
  if (status === "partially_covered")
    return { label: "Partial coverage", bg: C.warnSoft, color: C.warn };
  if (status === "covered") return { label: "Stocked", bg: "#EFEEEA", color: C.inkSoft };
  return { label: status, bg: "#EFEEEA", color: C.inkSoft };
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

// ---------- Page ----------
function Index() {
  const [data, setData] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"buys" | "cooling" | "trendsetters" | "info">("buys");
  const [selectedBuy, setSelectedBuy] = useState<number | null>(null);

  useEffect(() => {
    fetch(DATA_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json: Dataset) => setData(json))
      .catch((e) => {
        console.error("Failed to load dataset", e);
        setError(String(e));
      });
  }, []);

  const buys = useMemo(
    () => (data?.buys ?? []).slice().sort((a, b) => a.rank - b.rank),
    [data],
  );
  const cooling = useMemo(
    () => (data?.cooling ?? []).slice().sort((a, b) => a.rank - b.rank),
    [data],
  );

  useEffect(() => {
    if (selectedBuy == null && buys.length) setSelectedBuy(buys[0].rank);
  }, [buys, selectedBuy]);

  const selected = buys.find((b) => b.rank === selectedBuy) ?? buys[0] ?? null;

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: C.paper,
        color: C.ink,
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
      }}
    >
      <Header marketLabel={data?.display_name} />
      <div className="mx-auto w-full max-w-[1240px] px-8 py-8">
        <TabsBar tab={tab} setTab={setTab} counts={{ buys: buys.length, cooling: cooling.length, trendsetters: data?.trendsetters.length ?? 0 }} />

        {data && tab === "buys" && (
          <BuysSection
            data={data}
            buys={buys}
            selected={selected}
            onSelect={(r) => setSelectedBuy(r)}
          />
        )}
        {data && tab === "cooling" && <CoolingSection cooling={cooling} />}
        {data && tab === "trendsetters" && (
          <TrendsettersSection trendsetters={data.trendsetters} earlyWatch={data.early_watch} />
        )}
        {tab === "info" && <InfoSection />}

        {data && tab === "buys" && <Graveyard graveyard={data.graveyard} />}
        <Footer />
      </div>

      {!data && !error && (
        <div className="px-8 pb-8 text-[13px]" style={{ color: C.inkFaint }}>
          Loading live dataset…
        </div>
      )}
      {error && (
        <div
          className="fixed bottom-4 left-4 rounded-md px-3 py-2 text-xs"
          style={{ background: C.dangerSoft, border: `1px solid ${C.danger}`, color: C.danger }}
        >
          Failed to load dataset — {error}
        </div>
      )}
    </div>
  );
}

// ---------- Header ----------
function Header({ marketLabel }: { marketLabel?: string }) {
  return (
    <header
      className="sticky top-0 z-10 flex items-center justify-between px-8 py-3"
      style={{
        background: "rgba(255,255,255,0.85)",
        backdropFilter: "saturate(180%) blur(8px)",
        borderBottom: `1px solid ${C.rule}`,
      }}
    >
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 items-center justify-center rounded-md"
          style={{ background: C.accentSoft, color: C.accent }}
        >
          <Mountain size={16} />
        </div>
        <div className="text-[15px] font-semibold" style={{ color: C.ink }}>
          Alpine Signal Radar
        </div>
        <span
          className="ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium"
          style={{ background: C.tint, color: C.inkSoft, border: `1px solid ${C.rule}` }}
        >
          Live
        </span>
      </div>
      <div className="flex items-center gap-4 text-[12px]" style={{ color: C.inkSoft }}>
        <span className="flex items-center gap-1.5">
          <MapPin size={12} /> {marketLabel ?? "Swiss outdoor retail · CH / DACH"}
        </span>
        <span className="flex items-center gap-1.5">
          <Calendar size={12} /> Last run 2026-06-19
        </span>
      </div>
    </header>
  );
}

// ---------- Tabs ----------
function TabsBar({
  tab,
  setTab,
  counts,
}: {
  tab: string;
  setTab: (t: any) => void;
  counts: { buys: number; cooling: number; trendsetters: number };
}) {
  const items = [
    { id: "buys", label: "Buy signals", count: counts.buys, Icon: Target },
    { id: "cooling", label: "Downward trends", count: counts.cooling, Icon: TrendingDown },
    { id: "trendsetters", label: "Trendsetters", count: counts.trendsetters, Icon: Crown },
    { id: "info", label: "How scores work", count: null, Icon: Info },
  ] as const;
  return (
    <div
      className="mb-6 flex flex-wrap items-center gap-1 border-b"
      style={{ borderColor: C.rule }}
    >
      {items.map((it) => {
        const active = tab === it.id;
        return (
          <button
            key={it.id}
            onClick={() => setTab(it.id)}
            className="flex items-center gap-2 px-3 py-2 text-[13px] transition-colors"
            style={{
              color: active ? C.ink : C.inkSoft,
              fontWeight: active ? 600 : 500,
              borderBottom: active ? `2px solid ${C.ink}` : "2px solid transparent",
              marginBottom: -1,
            }}
          >
            <it.Icon size={14} />
            {it.label}
            {it.count != null && (
              <span
                className="tabular rounded px-1.5 py-0.5 text-[10.5px]"
                style={{ background: C.tint, color: C.inkSoft }}
              >
                {it.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// ---------- Buys ----------
function BuysSection({
  data,
  buys,
  selected,
  onSelect,
}: {
  data: Dataset;
  buys: Buy[];
  selected: Buy | null;
  onSelect: (r: number) => void;
}) {
  return (
    <div className="flex gap-8">
      <aside className="sticky top-[64px] w-[280px] shrink-0 self-start">
        <div
          className="mb-3 text-[11px] font-medium uppercase tracking-wider"
          style={{ color: C.inkFaint }}
        >
          Ranked opportunities
        </div>
        <nav className="flex flex-col">
          {buys.map((o) => {
            const isSel = selected?.rank === o.rank;
            const m = momentumStyle(o.momentum);
            return (
              <button
                key={o.rank}
                onClick={() => onSelect(o.rank)}
                className="group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors"
                style={{ background: isSel ? C.tint : "transparent" }}
                onMouseEnter={(e) => {
                  if (!isSel) (e.currentTarget as HTMLElement).style.background = C.tint;
                }}
                onMouseLeave={(e) => {
                  if (!isSel) (e.currentTarget as HTMLElement).style.background = "transparent";
                }}
              >
                <span
                  className="tabular w-5 text-right text-[11.5px]"
                  style={{ color: C.inkFaint }}
                >
                  {o.rank}
                </span>
                <span
                  className="inline-block h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ background: confidenceColor(o.confidence) }}
                />
                <span
                  className="flex-1 truncate text-[13.5px]"
                  style={{ color: C.ink, fontWeight: isSel ? 600 : 400 }}
                >
                  {o.name}
                </span>
                <m.Icon size={12} style={{ color: m.color }} />
                <span className="tabular w-9 text-right text-[12px]" style={{ color: C.inkSoft }}>
                  {o.final_score.toFixed(2)}
                </span>
              </button>
            );
          })}
        </nav>
        <div
          className="mt-4 rounded-md p-3 text-[12px] leading-relaxed"
          style={{ background: C.accentSoft, color: C.ink }}
        >
          <div className="mb-1 flex items-center gap-1.5 font-medium" style={{ color: C.accent }}>
            <Sparkles size={12} /> Executive summary
          </div>
          {data.summary}
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <BuyDetail buy={selected} />
        <WhitespaceMap buys={buys} selectedRank={selected?.rank ?? null} onSelect={onSelect} />
        <CoolingPreview cooling={data.cooling} />
      </div>
    </div>
  );
}

function BuyDetail({ buy }: { buy: Buy | null }) {
  if (!buy) return null;
  const cb = coverageBadge(buy.coverage_status);
  const m = momentumStyle(buy.momentum);
  const catLabel = CATEGORY_LABEL[buy.category] ?? buy.category;

  const grouped: Record<string, Evidence[]> = {};
  for (const e of buy.evidence) (grouped[e.source_type] ||= []).push(e);

  return (
    <article>
      <div className="flex items-center gap-2 text-[12px]" style={{ color: C.inkFaint }}>
        <span>{catLabel}</span>
        <span>·</span>
        <span className="tabular">Rank #{buy.rank}</span>
      </div>
      <h1
        className="mt-1 text-[32px] font-bold leading-tight tracking-tight"
        style={{ color: C.ink }}
      >
        {buy.name}
      </h1>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Badge label={cb.label} bg={cb.bg} color={cb.color} />
        <Badge
          label={`${buy.confidence} confidence`}
          bg={C.accentSoft}
          color={confidenceColor(buy.confidence)}
        />
        <Badge
          label={`${m.label}`}
          bg={C.tint}
          color={C.inkSoft}
          Icon={m.Icon}
          iconColor={m.color}
        />
        {buy.trendsetter_backed && (
          <Badge
            label={buy.top_brand ? `Trendsetter: ${buy.top_brand}` : "Trendsetter-backed"}
            bg={C.infoSoft}
            color={C.info}
            Icon={Crown}
          />
        )}
        {buy.luxury_trickle && (
          <Badge label="Luxury trickle-down" bg={C.warnSoft} color={C.warn} Icon={Sparkles} />
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Opportunity score" value={buy.final_score.toFixed(2)} color={C.ink} hint="0–1 composite" />
        <Stat
          label="CH transfer"
          value={String(Math.round(buy.transfer_score))}
          color={C.info}
          progress={buy.transfer_score}
          hint="0–100"
        />
        <Stat
          label="Momentum"
          value={(buy.momentum >= 0 ? "+" : "") + buy.momentum.toFixed(2)}
          color={m.color}
          Icon={m.Icon}
          hint="Δ vs baseline"
        />
        <Stat
          label="Shelf coverage"
          value={cb.label}
          color={cb.color}
          hint="vs CH retailers"
        />
      </div>

      {buy.trickle_note && (
        <Callout title="Luxury trickle context" Icon={Sparkles} tint={C.warn} bg={C.warnSoft}>
          {buy.trickle_note}
        </Callout>
      )}
      {buy.why_now && (
        <Callout title="Why now" Icon={Sparkles} tint={C.accent} bg={C.accentSoft}>
          {buy.why_now}
        </Callout>
      )}
      {buy.recommended_action && (
        <Callout title="Recommended action" Icon={Target} tint={C.accent} bg={C.accentSoft}>
          {buy.recommended_action}
        </Callout>
      )}
      {buy.transferability && (
        <Callout title="Transferability" Icon={ArrowUpRight} tint={C.info} bg={C.infoSoft}>
          {buy.transferability}
        </Callout>
      )}
      {buy.risks && (
        <Callout title="Risks" Icon={AlertTriangle} tint={C.danger} bg={C.dangerSoft}>
          {buy.risks}
        </Callout>
      )}

      <h2 className="mt-10 mb-3 text-[18px] font-semibold" style={{ color: C.ink }}>
        Evidence
      </h2>
      <div className="space-y-5">
        {Object.entries(grouped).map(([type, items]) => {
          const meta = SOURCE_TYPE_META[type] ?? { label: type, icon: Newspaper };
          const MIcon = meta.icon;
          return (
            <div key={type}>
              <div
                className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider"
                style={{ color: C.inkSoft }}
              >
                <MIcon size={12} />
                {meta.label}
                <span style={{ color: C.inkFaint, fontWeight: 400 }}>· {items.length}</span>
              </div>
              <ul className="flex flex-col">
                {items.map((s, i) => (
                  <EvidenceRow key={i} ev={s} fallbackIcon={MIcon} />
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </article>
  );
}

function EvidenceRow({ ev, fallbackIcon: FIcon }: { ev: Evidence; fallbackIcon: any }) {
  const ic = ev.url ? favicon(ev.url) : null;
  return (
    <li className="flex gap-3 py-2.5" style={{ borderTop: `1px solid ${C.rule}` }}>
      {ic ? (
        <img
          src={ic}
          alt=""
          className="mt-0.5 h-4 w-4 shrink-0 rounded-sm"
          style={{ background: C.tint }}
        />
      ) : (
        <FIcon size={14} className="mt-1 shrink-0" style={{ color: C.inkFaint }} />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          {ev.url ? (
            <a
              href={ev.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[13.5px] font-medium hover:underline"
              style={{ color: C.info }}
            >
              {ev.source}
              <ExternalLink size={11} />
            </a>
          ) : (
            <span className="text-[13.5px] font-medium" style={{ color: C.ink }}>
              {ev.source}
            </span>
          )}
          <span className="text-[12px]" style={{ color: C.inkFaint }}>
            {ev.market}
          </span>
        </div>
        {ev.note && (
          <div className="mt-0.5 text-[12.5px]" style={{ color: C.inkSoft }}>
            {ev.note}
          </div>
        )}
      </div>
    </li>
  );
}

// ---------- Cooling ----------
function CoolingPreview({ cooling }: { cooling: Cooling[] }) {
  if (!cooling.length) return null;
  return (
    <section className="mt-12">
      <div className="mb-3 flex items-end justify-between">
        <div>
          <h2
            className="flex items-center gap-2 text-[18px] font-semibold"
            style={{ color: C.ink }}
          >
            <TrendingDown size={16} style={{ color: C.danger }} /> Downward trends
          </h2>
          <p className="text-[12.5px]" style={{ color: C.inkSoft }}>
            Hold reorders · early warning. Clear before momentum erodes margin.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {cooling.map((c) => (
          <CoolingCard key={c.rank} c={c} />
        ))}
      </div>
    </section>
  );
}

function CoolingSection({ cooling }: { cooling: Cooling[] }) {
  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[28px] font-bold tracking-tight" style={{ color: C.ink }}>
          Downward trends
        </h1>
        <p className="mt-1 text-[13.5px]" style={{ color: C.inkSoft }}>
          Cooling categories — hold reorders, run inventory down, and time clearance before the
          lifecycle handoff completes.
        </p>
      </div>
      <div className="flex flex-col gap-4">
        {cooling.map((c) => (
          <CoolingCard key={c.rank} c={c} expanded />
        ))}
      </div>
    </section>
  );
}

function CoolingCard({ c, expanded = false }: { c: Cooling; expanded?: boolean }) {
  return (
    <div
      className="rounded-lg p-4"
      style={{ background: C.paper, border: `1px solid ${C.rule}` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[11.5px]" style={{ color: C.inkFaint }}>
            <span className="tabular">#{c.rank}</span>
            <span>·</span>
            <span>{c.markets.join(" / ")}</span>
          </div>
          <div className="mt-0.5 text-[15px] font-semibold" style={{ color: C.ink }}>
            {c.name}
          </div>
        </div>
        <span
          className="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[12px] font-semibold tabular"
          style={{ background: C.dangerSoft, color: C.danger }}
        >
          <ArrowDownRight size={12} />
          {c.momentum.toFixed(2)}
        </span>
      </div>
      <p className="mt-2 text-[13px] leading-relaxed" style={{ color: C.ink }}>
        {c.why_cooling}
      </p>
      <div
        className="mt-3 flex gap-2 rounded-md px-3 py-2 text-[12.5px] leading-relaxed"
        style={{ background: C.warnSoft, color: C.ink }}
      >
        <AlertCircle size={14} className="mt-0.5 shrink-0" style={{ color: C.warn }} />
        <span>
          <span className="font-semibold" style={{ color: C.warn }}>
            Hold reorders ·{" "}
          </span>
          {c.recommended_action}
        </span>
      </div>
      {expanded && c.evidence?.length > 0 && (
        <ul className="mt-3 flex flex-col">
          {c.evidence.map((ev, i) => (
            <EvidenceRow key={i} ev={ev} fallbackIcon={Newspaper} />
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------- Trendsetters ----------
function TrendsettersSection({
  trendsetters,
  earlyWatch,
}: {
  trendsetters: Trendsetter[];
  earlyWatch: EarlyWatch[];
}) {
  const sorted = trendsetters.slice().sort((a, b) => a.rank - b.rank);
  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[28px] font-bold tracking-tight" style={{ color: C.ink }}>
          Trendsetters
        </h1>
        <p className="mt-1 text-[13.5px]" style={{ color: C.inkSoft }}>
          Brands shaping what shows up next on Swiss shelves — by collab gravity, community
          authority, and reference-retailer rank.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {sorted.map((t) => (
          <div
            key={t.rank}
            className="rounded-lg p-4"
            style={{ background: C.paper, border: `1px solid ${C.rule}` }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-[11.5px]" style={{ color: C.inkFaint }}>
                  <span className="tabular">#{t.rank}</span>
                  <span>·</span>
                  <span>{t.markets.join(" / ")}</span>
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-[15px] font-semibold" style={{ color: C.ink }}>
                  {t.tier === "luxury" ? (
                    <Crown size={14} style={{ color: C.warn }} />
                  ) : (
                    <Mountain size={14} style={{ color: C.accent }} />
                  )}
                  {t.name}
                </div>
              </div>
              <span
                className="tabular shrink-0 rounded-full px-2 py-0.5 text-[12px] font-semibold"
                style={{
                  background: t.tier === "luxury" ? C.warnSoft : C.accentSoft,
                  color: t.tier === "luxury" ? C.warn : C.accent,
                }}
              >
                {t.influence_score.toFixed(2)}
              </span>
            </div>
            <p className="mt-2 text-[13px] leading-relaxed" style={{ color: C.inkSoft }}>
              {t.note}
            </p>
            {t.evidence_urls && t.evidence_urls.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {t.evidence_urls.map((u, i) => {
                  const ic = favicon(u);
                  let host = u;
                  try {
                    host = new URL(u).hostname.replace(/^www\./, "");
                  } catch {}
                  return (
                    <a
                      key={i}
                      href={u}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11.5px] hover:underline"
                      style={{ background: C.tint, color: C.info }}
                    >
                      {ic && <img src={ic} alt="" className="h-3 w-3" />}
                      {host}
                    </a>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {earlyWatch.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-3 flex items-center gap-2 text-[18px] font-semibold" style={{ color: C.ink }}>
            <Eye size={16} style={{ color: C.inkSoft }} /> Early watch
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {earlyWatch.map((e, i) => (
              <div
                key={i}
                className="rounded-lg p-4"
                style={{ background: C.tint, border: `1px solid ${C.rule}` }}
              >
                <div className="text-[14px] font-semibold" style={{ color: C.ink }}>
                  {e.name}
                </div>
                {e.trickle_note && (
                  <div className="mt-1 text-[12.5px] leading-relaxed" style={{ color: C.inkSoft }}>
                    {e.trickle_note}
                  </div>
                )}
                {e.why && (
                  <div className="mt-1 text-[12.5px] leading-relaxed" style={{ color: C.inkFaint }}>
                    {e.why}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

// ---------- Info ----------
function InfoSection() {
  const items = [
    {
      label: "Opportunity score",
      range: "0.00 – 1.00",
      color: C.ink,
      bg: C.tint,
      Icon: Target,
      what: "Composite signal that ranks a category for action.",
      how: "Blends CH transfer, momentum, shelf coverage, evidence corroboration, and trendsetter backing into one comparable number.",
      read: "≥ 0.65 buy-ready · 0.40–0.65 pilot · < 0.40 monitor only.",
    },
    {
      label: "CH transfer",
      range: "0 – 100",
      color: C.info,
      bg: C.infoSoft,
      Icon: ArrowUpRight,
      what: "How well a foreign signal is expected to land with Swiss buyers.",
      how: "Weighs market-context fit, legitimacy threshold, buyer risk tolerance, commercial readiness in DACH, and durability expectation.",
      read: "≥ 70 strong transfer · 40–69 conditional · < 40 weak — usually disqualifies.",
    },
    {
      label: "Momentum",
      range: "−1.0 – +1.0",
      color: C.accent,
      bg: C.accentSoft,
      Icon: TrendingUp,
      what: "Direction and pace of search, forum, and assortment signals over the last cycle.",
      how: "Velocity of mentions and queries vs a rolling baseline across US / UK / DE / CH.",
      read: "Positive = rising (act now). Negative = cooling (clear inventory, see Downward trends).",
    },
    {
      label: "Shelf gap",
      range: "absent · partial · stocked",
      color: C.danger,
      bg: C.dangerSoft,
      Icon: Store,
      what: "Whether CH retailers already carry the category vs reference markets (REI, Bergfreunde).",
      how: "Compares assortment presence at Transa, Ochsner Sport, and Galaxus against US/EU references.",
      read: "Absent = whitespace · Partial = room to deepen · Stocked = price/merch play only.",
    },
  ];
  return (
    <section>
      <div className="mb-5">
        <h1 className="text-[28px] font-bold tracking-tight" style={{ color: C.ink }}>
          How the scores work
        </h1>
        <p className="mt-1 text-[13.5px]" style={{ color: C.inkSoft }}>
          Four numbers drive every recommendation. Read them together — a high opportunity score
          should be backed by transfer, momentum, and a real shelf gap.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {items.map((it) => (
          <div
            key={it.label}
            className="rounded-lg p-5"
            style={{ background: C.paper, border: `1px solid ${C.rule}` }}
          >
            <div className="flex items-center gap-2">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-md"
                style={{ background: it.bg, color: it.color }}
              >
                <it.Icon size={14} />
              </div>
              <div className="text-[15px] font-semibold" style={{ color: C.ink }}>
                {it.label}
              </div>
              <span
                className="ml-auto tabular text-[11.5px]"
                style={{ color: C.inkFaint }}
              >
                {it.range}
              </span>
            </div>
            <dl className="mt-3 space-y-2 text-[13px] leading-relaxed">
              <Row k="What it measures" v={it.what} />
              <Row k="How it's built" v={it.how} />
              <Row k="How to read it" v={it.read} />
            </dl>
          </div>
        ))}
      </div>
    </section>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="grid grid-cols-[120px_1fr] gap-3">
      <dt className="text-[11.5px] font-medium uppercase tracking-wider" style={{ color: C.inkFaint }}>
        {k}
      </dt>
      <dd style={{ color: C.ink }}>{v}</dd>
    </div>
  );
}

// ---------- Shared ----------
function Badge({
  label,
  bg,
  color,
  Icon,
  iconColor,
}: {
  label: string;
  bg: string;
  color: string;
  Icon?: any;
  iconColor?: string;
}) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11.5px] font-medium capitalize"
      style={{ background: bg, color }}
    >
      {Icon && <Icon size={11} style={{ color: iconColor ?? color }} />}
      {label}
    </span>
  );
}

function Stat({
  label,
  value,
  color,
  progress,
  Icon,
  hint,
}: {
  label: string;
  value: string;
  color: string;
  progress?: number;
  Icon?: any;
  hint?: string;
}) {
  return (
    <div
      className="rounded-lg px-3.5 py-3"
      style={{ background: C.tint, border: `1px solid ${C.rule}` }}
    >
      <div className="flex items-center justify-between text-[11px]" style={{ color: C.inkSoft }}>
        <span>{label}</span>
        {hint && <span style={{ color: C.inkFaint }}>{hint}</span>}
      </div>
      <div className="mt-1 flex items-baseline gap-1.5">
        {Icon && <Icon size={16} style={{ color }} />}
        <span className="tabular text-[20px] font-semibold leading-none" style={{ color }}>
          {value}
        </span>
      </div>
      {typeof progress === "number" && (
        <div className="mt-2 h-1 w-full overflow-hidden rounded-full" style={{ background: C.rule }}>
          <div style={{ width: `${progress}%`, height: "100%", background: color }} />
        </div>
      )}
    </div>
  );
}

function Callout({
  title,
  Icon,
  tint,
  bg,
  children,
}: {
  title: string;
  Icon: any;
  tint: string;
  bg: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mt-3 flex gap-3 rounded-lg px-4 py-3" style={{ background: bg }}>
      <Icon size={16} className="mt-0.5 shrink-0" style={{ color: tint }} />
      <div className="min-w-0 flex-1">
        <div className="text-[12px] font-semibold" style={{ color: tint }}>
          {title}
        </div>
        <p className="mt-0.5 text-[14px] leading-relaxed" style={{ color: C.ink }}>
          {children}
        </p>
      </div>
    </div>
  );
}

function Graveyard({ graveyard }: { graveyard: GraveItem[] }) {
  if (!graveyard?.length) return null;
  return (
    <section className="mt-12">
      <h2
        className="mb-3 flex items-center gap-2 text-[18px] font-semibold"
        style={{ color: C.ink }}
      >
        <Archive size={16} style={{ color: C.inkSoft }} /> Graveyard
        <span className="text-[13px] font-normal" style={{ color: C.inkFaint }}>
          Discarded — kept for transparency
        </span>
      </h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {graveyard.map((g, i) => (
          <div
            key={i}
            className="rounded-lg p-4"
            style={{ background: C.tint, border: `1px solid ${C.rule}` }}
          >
            <div className="text-[14px] font-semibold" style={{ color: C.ink }}>
              {g.name}
            </div>
            <div className="mt-1 text-[12.5px] leading-relaxed" style={{ color: C.inkSoft }}>
              {g.reason}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer
      className="mt-12 flex flex-wrap items-center justify-between gap-2 pt-4 text-[12px]"
      style={{ borderTop: `1px solid ${C.rule}`, color: C.inkFaint }}
    >
      <span>Alpine Signal Radar — Swiss outdoor retail opportunity scan</span>
      <span className="flex items-center gap-3">
        <a href="https://www.transa.ch" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: C.inkSoft }}>
          Transa
        </a>
        <a href="https://www.ochsnersport.ch" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: C.inkSoft }}>
          Ochsner Sport
        </a>
        <a href="https://www.galaxus.ch" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: C.inkSoft }}>
          Galaxus
        </a>
      </span>
    </footer>
  );
}

// ---------- Whitespace map ----------
function WhitespaceMap({
  buys,
  selectedRank,
  onSelect,
}: {
  buys: Buy[];
  selectedRank: number | null;
  onSelect: (r: number) => void;
}) {
  const points = buys.map((o) => ({
    x: o.momentum,
    y: o.transfer_score,
    z: Math.max(60, o.final_score * 500),
    name: o.name,
    rank: o.rank,
    score: o.final_score,
    confidence: o.confidence,
    fill: confidenceColor(o.confidence),
    stroke: o.rank === selectedRank ? C.ink : "transparent",
  }));

  return (
    <section className="mt-12">
      <div className="mb-3 flex items-end justify-between">
        <div>
          <h2 className="text-[18px] font-semibold" style={{ color: C.ink }}>
            Whitespace map
          </h2>
          <p className="text-[12.5px]" style={{ color: C.inkSoft }}>
            Momentum × CH transfer. Dot size = opportunity score.
          </p>
        </div>
        <div className="flex items-center gap-3 text-[11.5px]" style={{ color: C.inkSoft }}>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: C.accent }} /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: C.warn }} /> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: C.danger }} /> Low
          </span>
        </div>
      </div>
      <div
        className="rounded-lg"
        style={{ height: 300, background: C.paper, border: `1px solid ${C.rule}` }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 16, right: 30, bottom: 28, left: 20 }}>
            <CartesianGrid stroke={C.rule} strokeDasharray="3 4" />
            <XAxis
              type="number"
              dataKey="x"
              domain={[-0.5, 1]}
              tick={{ fill: C.inkSoft, fontSize: 11 }}
              stroke={C.ruleStrong}
              label={{ value: "Momentum →", position: "insideBottom", offset: -14, fill: C.inkSoft, fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              domain={[0, 100]}
              tick={{ fill: C.inkSoft, fontSize: 11 }}
              stroke={C.ruleStrong}
              label={{ value: "CH transfer", angle: -90, position: "insideLeft", fill: C.inkSoft, fontSize: 11 }}
            />
            <ZAxis type="number" dataKey="z" range={[60, 500]} />
            <ReferenceLine x={0} stroke={C.ruleStrong} strokeDasharray="4 4" />
            <ReferenceLine y={50} stroke={C.ruleStrong} strokeDasharray="4 4" />
            <Tooltip
              cursor={{ stroke: C.ruleStrong }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p: any = payload[0].payload;
                return (
                  <div
                    className="rounded-md shadow-sm"
                    style={{
                      background: C.paper,
                      border: `1px solid ${C.rule}`,
                      padding: "6px 8px",
                      fontSize: 12,
                      color: C.ink,
                    }}
                  >
                    <div style={{ marginBottom: 3, fontWeight: 600 }}>{truncate(p.name, 36)}</div>
                    <div style={{ color: C.inkSoft }}>
                      Momentum {p.x >= 0 ? "+" : ""}
                      {p.x.toFixed(2)} · Transfer {Math.round(p.y)}
                    </div>
                    <div style={{ color: confidenceColor(p.confidence), fontWeight: 500 }}>
                      Score {p.score.toFixed(2)}
                    </div>
                  </div>
                );
              }}
            />
            <Scatter
              data={points}
              isAnimationActive={false}
              onClick={(d: any) => d?.rank && onSelect(d.rank)}
              shape={(props: any) => {
                const { cx, cy, payload } = props;
                const r = Math.sqrt(payload.z / Math.PI);
                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={r}
                    fill={payload.fill}
                    fillOpacity={0.55}
                    stroke={payload.stroke}
                    strokeWidth={payload.stroke === "transparent" ? 0 : 1.5}
                    style={{ cursor: "pointer" }}
                  />
                );
              }}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}