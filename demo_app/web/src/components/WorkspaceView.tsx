import { useCallback, useEffect, useRef, useState } from "react";
import { gd, urls } from "../api";
import { useApp } from "../AppContext";
import { logoTile } from "../theme";
import type { Tab } from "../types";
import { AgenticSummary } from "./AgenticSummary";
import { Portal } from "./Home";
import { useChatbot } from "./Chatbot";
import { Icon } from "../icons";
import { canCreateContent, useCatalog, usePermissions } from "../catalog";
import { Embed } from "./Embed";

export function WorkspaceView() {
  const { route, workspaces, themeOf, persona, navigate, t } = useApp();
  const wsId = route.view === "ws" ? route.ws : "";
  const perms = usePermissions(persona.id, wsId || undefined);

  const ws = workspaces.find((w) => w.id === wsId);
  if (route.view !== "ws" || !ws) return null;
  const th = themeOf(ws.id);
  // goodsalesv4's rule: authoring (Analyze, New dashboard) only for users who may create content
  const canAnalyze = canCreateContent(perms);
  const tabs: { id: Tab; label: string }[] = [
    { id: "home", label: t("home") },
    { id: "dashboards", label: t("dashboards") },
    { id: "report", label: t("aiReport") },
    ...(canAnalyze ? [{ id: "analyze" as Tab, label: t("analyze") }] : []),
  ];

  return (
    <div className="page">
      <header className="ws-bar">
        <span className="ws-logo" style={{ background: logoTile(th) }}>
          {th?.logo ? <img src={th.logo} alt="" /> : <b style={{ color: "var(--ws-primary)" }}>GD</b>}
        </span>
        <h1>{ws.name}</h1>
        <nav className="tabs inline">
          {tabs.map((x) => (
            <button key={x.id} className={`tab ${x.id === route.tab ? "active" : ""}`} onClick={() => navigate({ view: "ws", ws: ws.id, tab: x.id })}>
              {x.label}
            </button>
          ))}
        </nav>
      </header>

      {route.tab === "home" && <Portal key={`${persona.id}|${ws.id}`} fixedWs={ws.id} />}
      {route.tab === "dashboards" && <Dashboards ws={ws.id} sub={route.sub} viz={route.viz} canCreate={canAnalyze} permsKnown={perms !== null} />}
      {route.tab === "report" && <Report ws={ws.id} />}
      {route.tab === "analyze" && (perms === null ? <Loading text="…" /> : <Analyze ws={ws.id} canAnalyze={canAnalyze} />)}
    </div>
  );
}

const Loading = ({ text }: { text: string }) => (
  <div className="muted">
    <span className="spinner" /> {text}
  </div>
);

// ---------------------------------------------------------------- dashboards

const vizTitle = (id: string) => id.replace(/_[0-9a-f]{8}$/, "").replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

const SAVE_EVENTS = /saved|created|updated|copied|deleted/i;

function Dashboards({ ws, sub, viz, canCreate, permsKnown }: { ws: string; sub?: string; viz?: string; canCreate: boolean; permsKnown: boolean }) {
  const { persona, navigate, toast, t, localeVersion } = useApp();
  const chatbot = useChatbot();
  // the catalog (Shared / Private) lives in the sidebar; this page shows the selected dashboard
  const { list, refresh } = useCatalog(persona.id, ws, localeVersion);
  const knownIds = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (list && !knownIds.current) knownIds.current = new Set(list.map((d) => d.id));
  }, [list]);

  // after a save (new dashboard or "Save as new") re-read the catalog; a dashboard that was not
  // there before is the one just created, so open it (goodsalesv4 does this on GDC.DASH/EVT.SAVED)
  const onDashboardEvent = useCallback(
    (name: string) => {
      if (!SAVE_EVENTS.test(name)) return;
      window.setTimeout(async () => {
        const fresh = await refresh().catch(() => null);
        if (!fresh) return;
        const added = fresh.find((d) => !knownIds.current?.has(d.id));
        knownIds.current = new Set(fresh.map((d) => d.id));
        if (added) {
          toast(`“${added.title}” · ${added.isPrivate ? t("private") : t("shared")}`);
          navigate({ view: "ws", ws, tab: "dashboards", sub: added.id });
        }
      }, 1200);
    },
    [refresh, navigate, ws, toast, t],
  );

  const isNew = sub === "new";
  const cur = !isNew && list ? list.find((x) => x.id === sub) || list.find((x) => !x.isPrivate) || list[0] : undefined;

  // the open dashboard is the AI assistant's ambient context
  useEffect(() => {
    chatbot.setDashboard(cur ? { id: cur.id, title: cur.title } : undefined);
    return () => chatbot.setDashboard(undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cur?.id, cur?.title]);

  if (!list) return <Loading text={t("loadingDashboards")} />;

  if (isNew) {
    if (permsKnown && !canCreate) {
      navigate({ view: "ws", ws, tab: "dashboards" });
      return null;
    }
    return (
      <>
        <div className="dash-bar">
          <Icon name="plus" size={16} />
          <b>{t("newDashboard")}</b>
          <span className="muted small grow">{t("newDashboardHint")}</span>
          <button className="icon-btn sm" onClick={() => refresh()} title={t("refreshList")} aria-label={t("refreshList")}>
            <Icon name="refresh" size={15} />
          </button>
        </div>
        <Embed key={`new|${persona.id}`} url={urls.newDashboard(ws)} label="…" tall onEvent={onDashboardEvent} />
      </>
    );
  }

  if (!cur)
    return (
      <div className="card locked">
        <div>
          <div className="ico">
            <Icon name="dashboard" size={24} />
          </div>
          <h3>{t("noDashboards")}</h3>
        </div>
      </div>
    );

  return (
    <>
      <AgenticSummary
        key={`${persona.id}|${cur.id}`}
        ws={ws}
        dashboardId={cur.id}
        dashboardTitle={cur.title}
        actions={
          <a className="icon-btn sm" target="_blank" rel="noreferrer" href={urls.app(ws, `dashboards/#/dashboard/${cur.id}`)} title={t("openInGoodData")} aria-label={t("openInGoodData")}>
            <Icon name="external" size={15} />
          </a>
        }
      />
      {viz && cur.id === sub && (
        <div className="jump-banner">
          <Icon name="target" size={15} /> <b>{vizTitle(viz)}</b>
          <button className="icon-btn sm" onClick={() => navigate({ view: "ws", ws, tab: "dashboards", sub: cur.id })} aria-label="Clear">
            <Icon name="x" size={14} />
          </button>
        </div>
      )}
      <Embed url={urls.dashboard(ws, cur.id, cur.id === sub ? viz : undefined)} label={`${cur.title}…`} onEvent={onDashboardEvent} />
    </>
  );
}

// ---------------------------------------------------------------- AI report

function Report({ ws }: { ws: string }) {
  const { persona, overview, toast, t } = useApp();
  const [busy, setBusy] = useState(false);

  const exportPdf = async () => {
    setBusy(true);
    try {
      const r = await gd(persona.id, `/api/v1/actions/workspaces/${ws}/export/document`, {
        method: "POST",
        body: JSON.stringify({ format: "PDF", fileName: "Business Report", documentId: overview.reportId }),
      });
      for (let i = 0; i < 90; i++) {
        const res = await fetch(`/gd/api/v1/actions/workspaces/${ws}/export/document/${r.exportResult}`, {
          headers: { "X-Persona": persona.id, Accept: "application/pdf" },
        });
        if (res.status === 200) {
          window.open(URL.createObjectURL(await res.blob()), "_blank");
          break;
        }
        if (res.status !== 202) throw new Error(`${res.status} ${await res.text()}`);
        await new Promise((s) => setTimeout(s, 2000));
      }
    } catch (e: any) {
      toast(`Export failed: ${String(e.message).slice(0, 120)}`);
    }
    setBusy(false);
  };

  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        <div className="grow">
          <b>Business Report</b>{" "}
          <span className="muted small">· authored once in the parent, rendered in each tenant's theme, AI takeaways computed on {persona.name}'s data</span>
        </div>
        <button className="btn primary" onClick={exportPdf} disabled={busy}>
          {busy ? (
            <>
              <span className="spinner" /> Exporting…
            </>
          ) : (
            <>
              <Icon name="download" size={15} /> {t("exportPdf")}
            </>
          )}
        </button>
        <a className="btn ghost" target="_blank" rel="noreferrer" href={urls.app(ws, `reports/document/${overview.reportId}`)}>
          {t("openInGoodData")} <Icon name="external" size={14} />
        </a>
      </div>
      <Embed url={urls.document(ws, overview.reportId)} label="Rendering the AI report…" tall />
    </>
  );
}

// ---------------------------------------------------------------- analyze

function Analyze({ ws, canAnalyze }: { ws: string; canAnalyze: boolean }) {
  const { persona, personas, switchPersona, toast, t } = useApp();
  if (!canAnalyze) {
    const analyst = personas.find((p) => p.id === "analyze");
    return (
      <div className="card locked">
        <div>
          <div className="ico">
            <Icon name="lock" size={24} />
          </div>
          <h3>{persona.name} can view, not author</h3>
          <p>
            The View group has <b>VIEW</b> on this workspace (plus export, filter views, schedules and AI Assistant) but not <b>ANALYZE</b>, so
            Analytical Designer is not available. Switch to the Analyze user to build new visualizations on the same governed model.
          </p>
          {analyst?.available && (
            <div className="row" style={{ justifyContent: "center", marginTop: 16 }}>
              <button className="btn primary" onClick={() => switchPersona("analyze", { view: "ws", ws, tab: "analyze" }).then(() => toast("Now viewing as Analyze User"))}>
                Switch to Analyze User →
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        <div className="grow">
          <b>Analytical Designer</b> <span className="muted small">· drag metrics and attributes from the governed model; results are filtered to this tenant automatically</span>
        </div>
        <a className="btn ghost" target="_blank" rel="noreferrer" href={urls.app(ws, "analyze/#/reportId/edit")}>
          {t("openInGoodData")} <Icon name="external" size={14} />
        </a>
      </div>
      <Embed url={urls.analyze(ws)} label="Opening Analytical Designer…" tall />
    </>
  );
}
