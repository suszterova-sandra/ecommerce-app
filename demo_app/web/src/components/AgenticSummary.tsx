import { useEffect, useState } from "react";
import { dashboardSummary, keyDrivers, lastQuarters, matchMetric, workspaceMetrics, type KdaResult, type Metric, type ParsedSummary } from "../agentic";
import { useApp } from "../AppContext";
import { fmt } from "../insights";
import { markdown } from "../markdown";
import { useChatbot } from "./Chatbot";
import { languageName } from "../i18n";

const inline = (t: string) => markdown(t).replace(/^<p>|<\/p>$/g, "");

const STEPS = ["Collecting dashboard visualizations…", "Querying data with the dashboard filters…", "Generating the AI summary…"];

/**
 * Agentic summary above an embedded dashboard: GoodData's AI dashboard summary in three sections, and
 * key points that run key driver analysis for the metric they mention. Everything runs as the current user.
 */
export function AgenticSummary({ ws, dashboardId, dashboardTitle, onHide }: { ws: string; dashboardId: string; dashboardTitle: string; onHide: () => void }) {
  const { persona, t, lang } = useApp();
  const chatbot = useChatbot();
  const [summary, setSummary] = useState<ParsedSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [kda, setKda] = useState<{ status: "idle" | "loading" | "done" | "error"; metric?: Metric; result?: KdaResult; error?: string }>({ status: "idle" });
  const [regen, setRegen] = useState(0);

  useEffect(() => {
    let live = true;
    setSummary(null);
    setError(null);
    setKda({ status: "idle" });
    dashboardSummary(persona.id, ws, dashboardId, regen > 0, languageName(lang))
      .then((s) => live && setSummary(s))
      .catch((e) =>
        live &&
        setError(
          e.status === 403 || e.status === 404
            ? `GoodData does not generate dashboard summaries for view-only users. Switch to the Analyze user, or ask the AI Assistant.`
            : e.status >= 500
              ? "GoodData's AI service did not answer this time. Try Regenerate in a moment."
              : e.message,
        ),
      );
    workspaceMetrics(persona.id, ws).then((m) => live && setMetrics(m)).catch(() => {});
    return () => {
      live = false;
    };
  }, [persona.id, ws, dashboardId, regen, lang]);

  // the AI summary usually takes 10-30 s; show where it is
  const loading = !summary && !error;
  useEffect(() => {
    if (!loading) {
      setProgress(100);
      return;
    }
    setProgress(0);
    const t = window.setInterval(() => setProgress((p) => (p >= 92 ? 92 : p + 0.5)), 100);
    return () => window.clearInterval(t);
  }, [loading]);

  const runKda = (metric: Metric) => {
    if (kda.status === "loading") return;
    setKda({ status: "loading", metric });
    keyDrivers(persona.id, ws, metric)
      .then((result) => setKda({ status: "done", metric, result }))
      .catch((e) => setKda({ status: "error", metric, error: e.message }));
  };

  const keyPoints = (summary?.insights || []).slice(0, 5).map((text) => ({ text, metric: matchMetric(text, metrics) }));
  const q = lastQuarters();

  return (
    <section className="agentic">
      <div className="ag-head">
        <div className="ag-title">
          <span className="ag-badge">✦ {t("agenticSummary")}</span>
          <span className="muted small">
            {dashboardTitle} · {q.analyzed.label} vs {q.reference.label} · as {persona.name}
          </span>
        </div>
        <div className="row">
          {!loading && (
            <button className="btn ghost sm" onClick={() => setRegen((r) => r + 1)}>
              {t("regenerate")}
            </button>
          )}
          <button className="btn ghost sm" onClick={onHide}>
            {t("hide")}
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      {loading && (
        <div className="ag-loading">
          <div className="ag-loading-label">{t("summarizing")}</div>
          <div className="ag-bar">
            <i style={{ width: `${progress}%` }} />
          </div>
          <div className="muted small">{STEPS[progress < 20 ? 0 : progress < 50 ? 1 : 2]}</div>
        </div>
      )}

      {summary && (
        <div className="ag-body">
          <div className="ag-main">
            <div className="ag-label">{t("summary")}</div>
            <p className="ag-summary" dangerouslySetInnerHTML={{ __html: inline(summary.summary) }} />

            <div className="ag-label">
              {t("keyPoints")} <span className="muted">· {t("clickForKda")}</span>
            </div>
            <div className="ag-points">
              {keyPoints.map((k, i) => (
                <button
                  key={i}
                  className={`ag-point ${k.metric ? "clickable" : ""} ${kda.metric?.id === k.metric?.id && kda.status !== "idle" ? "active" : ""}`}
                  disabled={!k.metric || kda.status === "loading"}
                  title={k.metric ? `Run key driver analysis for ${k.metric.title}` : undefined}
                  onClick={() => k.metric && runKda(k.metric)}
                >
                  <span dangerouslySetInnerHTML={{ __html: inline(k.text) }} />
                  {k.metric && <span className="ag-kda-chip">🔍 {t("why")}</span>}
                </button>
              ))}
            </div>
            <div className="ag-ask">
              <button
                className="btn ghost sm"
                onClick={() =>
                  chatbot.openWithMessage(
                    `On the ${dashboardTitle} dashboard: ${summary.summary.replace(/\*\*/g, "")} What should I look at first, and why?`,
                  )
                }
              >
                ✦ {t("discussSummary")}
              </button>
            </div>

            {kda.status !== "idle" && (
              <KdaPanel
                state={kda}
                onClose={() => setKda({ status: "idle" })}
                onAsk={(text) => chatbot.openWithMessage(text)}
              />
            )}
          </div>

          <div className="ag-side">
            <div className="ag-label accent">{t("areasToWatch")}</div>
            <ol className="ag-recs">
              {summary.recommendations.slice(0, 3).map((r, i) => (
                <li key={i}>
                  <span className="n">{i + 1}</span>
                  <span dangerouslySetInnerHTML={{ __html: inline(r) }} />
                </li>
              ))}
            </ol>
            <div className="muted small" style={{ marginTop: 10 }}>
              GoodData AI · {summary.visualizations} visualizations{summary.generatedAt ? ` · ${new Date(summary.generatedAt).toLocaleTimeString()}` : ""}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function KdaPanel({ state, onClose, onAsk }: { state: { status: string; metric?: Metric; result?: KdaResult; error?: string }; onClose: () => void; onAsk: (text: string) => void }) {
  const { t } = useApp();
  const r = state.result;
  const fmtVal = formatter(state.metric?.id);
  const total = r ? r.overall.analyzed - r.overall.reference : 0;
  const max = r ? Math.max(1, ...r.drivers.map((d) => Math.abs(d.delta))) : 1;
  return (
    <div className="kda">
      <div className="kda-head">
        <div>
          <div className="ag-label" style={{ margin: 0 }}>{t("kda")}</div>
          <b>{state.metric?.title}</b>
          {r && (
            <span className="muted small">
              {" "}
              · {r.period.reference} → {r.period.analyzed}: {fmtVal(r.overall.reference)} → {fmtVal(r.overall.analyzed)} (
              <span className={total >= 0 ? "pos" : "neg"}>
                {total >= 0 ? "+" : "−"}
                {fmtVal(Math.abs(total))}
              </span>
              )
            </span>
          )}
        </div>
        <button className="btn ghost sm" onClick={onClose}>
          ✕
        </button>
      </div>
      {state.status === "loading" && (
        <div className="thinking" style={{ padding: "10px 0" }}>
          <span className="spinner" /> {t("runningKda")}
        </div>
      )}
      {state.status === "error" && <div className="error-box">Key driver analysis could not be completed: {state.error}</div>}
      {r && !r.drivers.length && <div className="muted small" style={{ padding: "8px 0" }}>No attribute explains the change for this period.</div>}
      {r && r.drivers.length > 0 && (
        <div className="kda-rows">
          {r.drivers.map((d, i) => (
            <div key={i} className="kda-row">
              <div className="kda-name">
                <span className="kda-attr">{d.attribute}</span>
                <b>{d.value}</b>
                {d.significant && <span className="kda-sig">{t("significant")}</span>}
              </div>
              <div className="kda-bar">
                <i className={d.delta >= 0 ? "up" : "down"} style={{ width: `${(Math.abs(d.delta) / max) * 100}%` }} />
              </div>
              <div className="kda-val">
                <span className={d.delta >= 0 ? "pos" : "neg"}>
                  {d.delta >= 0 ? "+" : "−"}
                  {fmtVal(Math.abs(d.delta))}
                </span>
                <span className="muted small">
                  {fmtVal(d.reference)} → {fmtVal(d.analyzed)}
                  {Math.abs(d.share) <= 5 && total ? ` · ${Math.round(d.share * 100)}% ${t("ofChangeShort")}` : ""}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      {r && r.drivers.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <button
            className="btn ghost sm"
            onClick={() =>
              onAsk(
                `Key driver analysis of ${state.metric?.title} from ${r.period.reference} to ${r.period.analyzed}: ${r.drivers
                  .slice(0, 4)
                  .map((d) => `${d.attribute} ${d.value} ${d.delta >= 0 ? "+" : "-"}${Math.abs(Math.round(d.delta))}`)
                  .join("; ")}. Explain what is behind these drivers and what we should do about them.`,
              )
            }
          >
            ✦ {t("askWhatToDo")}
          </button>
        </div>
      )}
      {r && r.restricted > 0 && <div className="muted small">{r.restricted} attributes were left out because this user cannot access them.</div>}
    </div>
  );
}

// format by what the metric measures: rates as %, counts as plain numbers, everything else as money
const COUNT = /orders|customers|count|units|quantity|frequency/;
const RATE = /rate|margin|percentage|share|elastic/;
const formatter = (metricId = "") => (v: number) =>
  RATE.test(metricId) ? fmt(v, "pct") : COUNT.test(metricId) ? fmt(v, "count") : fmt(v, "money");
