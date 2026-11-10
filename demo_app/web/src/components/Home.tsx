import { useEffect, useState } from "react";
import { gd, urls } from "../api";
import { useApp } from "../AppContext";
import { languageName, type Key, type Lang } from "../i18n";
import { change, fmt, loadInsights, type Driver, type Insights, type Kpi, type Target } from "../insights";
import { markdown } from "../markdown";
import { logoTile } from "../theme";
import type { PersonaId } from "../types";
import { useChatbot } from "./Chatbot";
import { Prewarm } from "./Embed";
import { STATIC } from "../staticBackend";

const DIM_ICON: Record<string, string> = { product_brand: "🏷️", product_category: "🗂️", customer_country: "🌍", customer_state: "📍" };
const DIM_KEY: Record<string, Key> = { product_brand: "brand", product_category: "category", customer_country: "country", customer_state: "state" };
const KPI_KEY: Record<string, Key> = {
  net_sales: "netSales",
  orders: "orders",
  customers: "activeCustomers",
  gross_profit: "grossProfit",
  margin: "grossMargin",
  aov: "aov",
  returns: "returnRate",
  cancel: "cancelRate",
};

// workspace chosen on the global Home, per user
const globalWs = new Map<PersonaId, string>();
const briefings = new Map<string, Promise<{ text: string; meta: string }>>();

function briefingFor(persona: PersonaId, ws: string, lang: Lang) {
  const key = `${persona}|${ws}|${lang}`;
  if (!briefings.has(key)) {
    const p = gd(persona, `/api/v1/ai/workspaces/${ws}/summary`, {
      method: "POST",
      body: JSON.stringify({ dashboardId: "overview", formatHint: lang === "en" ? undefined : `Write the whole answer in ${languageName(lang)}.` }),
    }).then((r) => ({ text: r.summary as string, meta: `${r.visualizationsIncluded?.length || 0} visualizations · Overview` }));
    p.catch(() => briefings.delete(key));
    briefings.set(key, p);
  }
  return briefings.get(key)!;
}

export const Home = () => <Portal />;

/** The welcome portal: global (with a workspace picker) or fixed to one workspace (its Home tab). */
export function Portal({ fixedWs }: { fixedWs?: string }) {
  const { persona, workspaces, overview, navigate, themeOf, t, lang } = useApp();
  const chatbot = useChatbot();
  const [wsChoice, setWsChoice] = useState<string>(
    () => fixedWs ?? globalWs.get(persona.id) ?? (persona.id === "admin" ? overview.parent : workspaces.find((w) => !w.isParent)?.id || workspaces[0]?.id || ""),
  );
  const ws = workspaces.find((w) => w.id === (fixedWs ?? wsChoice)) || workspaces[0];
  const theme = ws ? themeOf(ws.id) : undefined;
  const [insights, setInsights] = useState<Insights | null>(null);
  const [insightsError, setInsightsError] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<{ text: string; meta: string } | null>(null);
  const [briefingError, setBriefingError] = useState(false);
  const [briefOpen, setBriefOpen] = useState(false);

  useEffect(() => {
    if (!ws) return;
    let live = true;
    setInsights(null);
    setInsightsError(null);
    loadInsights(persona.id, ws.id)
      .then((r) => live && setInsights(r))
      .catch((e) => live && setInsightsError(e.message));
    return () => {
      live = false;
    };
  }, [persona.id, ws?.id]);

  useEffect(() => {
    if (!ws) return;
    let live = true;
    setBriefing(null);
    setBriefingError(false);
    briefingFor(persona.id, ws.id, lang)
      .then((r) => live && setBriefing(r))
      .catch(() => live && setBriefingError(true));
    return () => {
      live = false;
    };
  }, [persona.id, ws?.id, lang]);

  if (!ws) return null;

  const open = (tg: Target) => navigate({ view: "ws", ws: ws.id, tab: "dashboards", sub: tg.dashboard, viz: tg.viz });
  const pickWs = (id: string) => {
    globalWs.set(persona.id, id);
    setWsChoice(id);
  };

  const ns = insights?.kpis.find((k) => k.id === "net_sales");
  const nsChange = ns ? change(ns) : null;
  const total = ns && ns.cur !== undefined && ns.prev !== undefined ? ns.cur - ns.prev : 0;
  const top = insights?.drivers.find((d) => Math.sign(d.delta) === Math.sign(total)) || insights?.drivers[0];
  const headline =
    ns && nsChange
      ? t("netSalesIn", { dir: nsChange.up ? t("grew") : t("fell"), pct: nsChange.text.replace(/^[+−]/, ""), val: fmt(ns.cur, "money"), q: insights!.period.cur })
      : null;
  const subline = top
    ? `${t(DIM_KEY[top.dim])} ${top.member} ${top.delta >= 0 ? t("added") : t("tookAway")} ${fmt(Math.abs(top.delta), "money")}${
        Math.sign(top.delta) === Math.sign(total) && Math.abs(top.share) <= 1 ? `, ${Math.round(Math.abs(top.share) * 100)}% ${t("ofChange")}` : ""
      }.`
    : null;
  const h = new Date().getHours();
  const hello = h < 12 ? t("goodMorning") : h < 18 ? t("goodAfternoon") : t("goodEvening");
  const date = new Date().toLocaleDateString(lang === "en" ? "en-US" : lang === "de" ? "de-DE" : "fr-FR", { weekday: "long", day: "numeric", month: "long" });

  return (
    <div className={`portal ${fixedWs ? "in-ws" : ""}`}>
      {!(STATIC && persona.id === "admin") && <Prewarm url={urls.dashboard(ws.id, "overview")} />}
      <section className="portal-hero" style={theme?.cover ? { backgroundImage: `url('${theme.cover}')` } : undefined}>
        <div className="ph-shade" />
        <div className="ph-inner">
          <div className="ph-top">
            <span className="ph-date">{date}</span>
            <label className="scope">
              <span className="scope-logo" style={{ background: theme?.logo ? logoTile(theme) : theme?.palette.primary?.base }}>
                {theme?.logo && <img src={theme.logo} alt="" />}
              </span>
              {fixedWs || workspaces.length < 2 ? (
                <span className="scope-name">{ws.name}</span>
              ) : (
                <select value={ws.id} onChange={(e) => pickWs(e.target.value)} aria-label={t("workspaces")}>
                  {workspaces.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              )}
            </label>
          </div>
          <div className="ph-hello">
            {hello}, {persona.id === "admin" ? persona.name.split(" ")[0] : persona.name} 👋
          </div>
          <h1>{headline || (insightsError ? t("overviewFallback") : <span className="sk sk-title" />)}</h1>
          <p className="ph-sub">
            {subline || (insights || insightsError ? "" : <span className="sk sk-line" />)}
            {insights && <span className="muted-on-dark"> {t("comparedWith", { q: insights.period.prev })}</span>}
          </p>
          <div className="ph-actions">
            <button className="btn primary" onClick={() => navigate({ view: "ws", ws: ws.id, tab: "dashboards", sub: "overview" })}>
              {t("openOverview")} →
            </button>
            <button className="btn glass" onClick={() => (headline ? chatbot.openWithMessage(`${headline}. ${subline || ""}`) : chatbot.open())}>
              ✦ {t("askAiAbout")}
            </button>
            <button className="btn glass" onClick={() => navigate({ view: "ws", ws: ws.id, tab: "report" })}>
              📄 {t("aiBusinessReport")}
            </button>
          </div>
        </div>
      </section>

      {insightsError && <div className="error-box" style={{ marginTop: 16 }}>{insightsError}</div>}

      <section className="kpi-row">
        {(insights?.kpis || [null, null, null, null]).map((k, i) =>
          k ? <KpiTile key={k.id} k={k} period={insights!.period.prev} onOpen={open} /> : <div key={i} className="kpi-tile sk-tile" />,
        )}
      </section>

      <section className="portal-grid">
        <div className="card">
          <div className="card-h">
            <div>
              <h3>{t("keyDrivers")}</h3>
              <div className="muted small">{insights ? t("keyDriversSub", { a: insights.period.prev, b: insights.period.cur }) : ""}</div>
            </div>
          </div>
          <div className="drivers">
            {!insights && !insightsError && [0, 1, 2].map((i) => <div key={i} className="driver sk-tile" />)}
            {insights?.drivers.map((d) => (
              <DriverCard key={d.dim + d.member} d={d} max={Math.max(...insights.drivers.map((x) => Math.max(x.cur, x.prev)))} onOpen={open} />
            ))}
            {insights && !insights.drivers.length && <div className="muted small" style={{ padding: 16 }}>{t("noDriver")}</div>}
          </div>
        </div>

        <div className="card briefing">
          <div className="card-h">
            <div>
              <h3>✨ {t("aiBriefing")}</h3>
              <div className="muted small">{t("aiBriefingSub", { u: persona.name })}</div>
            </div>
          </div>
          <div className={`card-b summary-text ${briefOpen ? "" : "clamped"}`}>
            {briefing ? (
              <div dangerouslySetInnerHTML={{ __html: markdown(briefing.text) }} />
            ) : briefingError ? (
              <div className="muted">—</div>
            ) : (
              <>
                <span className="thinking">
                  <span className="spinner" /> {t("readingOverview")}
                </span>
                <span className="sk sk-line" />
                <span className="sk sk-line" />
                <span className="sk sk-line short" />
              </>
            )}
          </div>
          {briefing && (
            <div className="briefing-foot">
              <span className="muted small">{briefing.meta}</span>
              <button className="btn ghost" onClick={() => setBriefOpen((o) => !o)}>
                {briefOpen ? t("showLess") : t("readFull")}
              </button>
            </div>
          )}
        </div>
      </section>

      <section style={{ marginBottom: 40 }}>
        <div className="section-title">
          <h2>{t("watchList")}</h2>
          <span className="muted small">{insights ? `${insights.period.cur} vs ${insights.period.prev}` : ""}</span>
        </div>
        <div className="watch-row">
          {(insights?.watch || [null, null, null, null]).map((k, i) => (k ? <WatchTile key={k.id} k={k} onOpen={open} /> : <div key={i} className="watch-tile sk-tile" />))}
        </div>
      </section>
    </div>
  );
}

function Delta({ k }: { k: Kpi }) {
  const c = change(k);
  if (!c) return null;
  return <span className={`delta ${c.up === k.goodWhenUp ? "good" : "bad"}`}>{c.up ? "▲" : "▼"} {c.text.replace(/^[+−]/, "")}</span>;
}

function KpiTile({ k, period, onOpen }: { k: Kpi; period: string; onOpen: (t: Target) => void }) {
  const { t } = useApp();
  return (
    <button className="kpi-tile" onClick={() => onOpen(k.target)}>
      <span className="kt-label">{t(KPI_KEY[k.id])}</span>
      <span className="kt-value">{fmt(k.cur, k.format)}</span>
      <span className="kt-foot">
        <Delta k={k} />
        <span className="muted small">{t("vsIn", { v: fmt(k.prev, k.format), q: period })}</span>
      </span>
      <span className="kt-go">{k.target.dashTitle} →</span>
    </button>
  );
}

function WatchTile({ k, onOpen }: { k: Kpi; onOpen: (t: Target) => void }) {
  const { t } = useApp();
  return (
    <button className="watch-tile" onClick={() => onOpen(k.target)}>
      <span className="kt-label">{t(KPI_KEY[k.id])}</span>
      <span className="wt-value">{fmt(k.cur, k.format)}</span>
      <Delta k={k} />
    </button>
  );
}

function DriverCard({ d, max, onOpen }: { d: Driver; max: number; onOpen: (t: Target) => void }) {
  const { t } = useApp();
  const up = d.delta >= 0;
  const pct = d.prev ? (d.delta / Math.abs(d.prev)) * 100 : null;
  return (
    <button className="driver" onClick={() => onOpen(d.target)}>
      <span className="dr-ico">{DIM_ICON[d.dim] || "•"}</span>
      <span className="dr-main">
        <span className="dr-noun">{t(DIM_KEY[d.dim])}</span>
        <span className="dr-member">{d.member}</span>
        <span className="dr-bars">
          <i className="prev" style={{ width: `${(Math.max(d.prev, 0) / max) * 100}%` }} />
          <i className={`cur ${up ? "up" : "down"}`} style={{ width: `${(Math.max(d.cur, 0) / max) * 100}%` }} />
        </span>
        <span className="dr-link">{d.target.dashTitle} →</span>
      </span>
      <span className="dr-side">
        <span className={`delta ${up ? "good" : "bad"}`}>
          {up ? "+" : "−"}
          {fmt(Math.abs(d.delta), "money")}
        </span>
        {pct !== null && Number.isFinite(pct) && (
          <span className="muted small">
            {up ? "+" : "−"}
            {Math.abs(pct).toFixed(0)}%
          </span>
        )}
      </span>
    </button>
  );
}
