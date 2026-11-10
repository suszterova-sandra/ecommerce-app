import { useApp } from "../AppContext";
import { canCreateContent, useCatalog, usePermissions } from "../catalog";
import { logoTile } from "../theme";
import type { Workspace } from "../types";
import { Icon } from "../icons";

export function WsSwatch({ wsId }: { wsId: string }) {
  const { themeOf } = useApp();
  const t = themeOf(wsId);
  return (
    <span className="sw" style={{ background: t?.logo ? logoTile(t) : t?.palette.primary?.base || "#888" }}>
      {t?.logo && <img src={t.logo} alt="" />}
    </span>
  );
}

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const { persona, workspaces, route, navigate, t, brand } = useApp();
  const hasParent = workspaces.some((w) => w.isParent);
  const activeWs = route.view === "ws" ? route.ws : undefined;
  // a user with a single workspace always sees its dashboards
  const expanded = (w: Workspace) => w.id === activeWs || workspaces.length === 1;

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" style={brand.logo ? { background: brand.logoBg } : undefined}>
          {brand.logo ? (
            <img src={brand.logo} alt="" />
          ) : (
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path fill="currentColor" d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM16.5 13a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z" />
            </svg>
          )}
        </div>
        <div className="brand-text">
          <div className="brand-name">{brand.name}</div>
          <div className="brand-sub">Powered by GoodData</div>
        </div>
        <button className="collapse-btn" onClick={onToggle} title={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-expanded={!collapsed}>
          <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" style={{ transform: collapsed ? "rotate(180deg)" : undefined }}>
            <path fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M15 6l-6 6 6 6" />
          </svg>
        </button>
      </div>


      <nav className="side-section">
        <button className={`nav-item ${route.view === "home" ? "active" : ""}`} title={collapsed ? t("home") : undefined} onClick={() => navigate({ view: "home" })}>
          <span className="sw ico-sw">
            <Icon name="home" size={15} />
          </span>
          <span className="lbl">{t("home")}</span>
        </button>
        {persona.id === "admin" && (
          <>
            <button className={`nav-item ${route.view === "control" ? "active" : ""}`} title={collapsed ? t("controlCenter") : undefined} onClick={() => navigate({ view: "control" })}>
              <span className="sw ico-sw">
                <Icon name="command" size={15} />
              </span>
              <span className="lbl">{t("controlCenter")}</span>
            </button>
          </>
        )}
        <div className="side-label" style={{ marginTop: 10 }}>{t("workspaces")}</div>
        {workspaces.map((w) => (
          <div key={w.id}>
            <button
              className={`nav-item ${!w.isParent && hasParent ? "nav-child" : ""} ${activeWs === w.id && route.view === "ws" && route.tab !== "dashboards" ? "active" : ""}`}
              title={collapsed ? w.name : undefined}
              onClick={() => navigate({ view: "ws", ws: w.id, tab: "home" })}
            >
              <WsSwatch wsId={w.id} />
              <span className="lbl">{w.name}</span>
              <span className="tag">
                <Icon name={expanded(w) ? "chevronDown" : "chevronRight"} size={14} />
              </span>
            </button>
            {expanded(w) && !collapsed && <DashboardTree ws={w.id} indent={!w.isParent && hasParent} />}
          </div>
        ))}
      </nav>
    </aside>
  );
}

/** Workspace → Shared / Private dashboards (+ New dashboard for users who may create content). */
function DashboardTree({ ws, indent }: { ws: string; indent: boolean }) {
  const { persona, route, navigate, t, localeVersion } = useApp();
  const { list } = useCatalog(persona.id, ws, localeVersion);
  const perms = usePermissions(persona.id, ws);
  const current = route.view === "ws" && route.ws === ws && route.tab === "dashboards" ? route.sub || "overview" : undefined;
  if (!list) return <div className={`tree ${indent ? "indent" : ""}`}><span className="tree-empty"><span className="spinner" /></span></div>;
  const shared = list.filter((d) => !d.isPrivate);
  const priv = list.filter((d) => d.isPrivate);
  const item = (d: { id: string; title: string; isPrivate: boolean }) => (
    <button
      key={d.id}
      className={`tree-item ${current === d.id ? "active" : ""}`}
      title={d.isPrivate ? `${d.title} · ${t("private")}` : d.title}
      onClick={() => navigate({ view: "ws", ws, tab: "dashboards", sub: d.id })}
    >
      <Icon name={d.isPrivate ? "lock" : "dashboard"} size={14} className="tree-ico" />
      <span className="tree-lbl">{d.title}</span>
    </button>
  );
  return (
    <div className={`tree ${indent ? "indent" : ""}`}>
      {shared.map(item)}
      {priv.length > 0 && <div className="tree-divider" />}
      {priv.map(item)}
      {canCreateContent(perms) && (
        <button className={`tree-item new ${current === "new" ? "active" : ""}`} onClick={() => navigate({ view: "ws", ws, tab: "dashboards", sub: "new" })}>
          <Icon name="plus" size={14} className="tree-ico" />
          <span className="tree-lbl">{t("newDashboard")}</span>
        </button>
      )}
    </div>
  );
}
