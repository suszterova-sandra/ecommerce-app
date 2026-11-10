import { useApp } from "../AppContext";
import type { ColorMode } from "../theme";
import { useChatbot } from "./Chatbot";
import { LANGS, type Lang } from "../i18n";
import { adminLoginUrl, STATIC } from "../staticBackend";

export function Topbar({ mode, onToggleMode }: { mode: ColorMode; onToggleMode: () => void }) {
  const { personas, persona, switchPersona, route, overview, workspaces, toast, lang, setLang, t } = useApp();
  const parentName = overview.workspaces.find((w) => w.isParent)?.name || "Parent";
  const ws = route.view === "ws" ? workspaces.find((w) => w.id === route.ws) : undefined;
  const chatbot = useChatbot();

  return (
    <header className="topbar">
      <div className="crumbs">
        {route.view === "home" && (
          <>
            <span>Ecommerce Cloud</span>
            <span>›</span>
            <b>{t("home")}</b>
          </>
        )}
        {route.view === "control" && (
          <>
            <span>Organization</span>
            <span>›</span>
            <b>{t("controlCenter")}</b>
          </>
        )}
        {ws && (
          <>
            <span>{parentName}</span>
            <span>›</span>
            <b>{ws.isParent ? "Parent workspace" : ws.name}</b>
          </>
        )}
      </div>
      <div className="top-right">
      <button className={`ai-top-btn ${chatbot.isOpen ? "on" : ""}`} onClick={() => (chatbot.isOpen ? chatbot.close() : chatbot.open())}>
        ✦ {t("aiAssistant")}
      </button>
      <label className="lang-picker" title="Language of the app, the dashboards and the translated metadata">
        <span>{LANGS.find((l) => l.id === lang)?.flag}</span>
        <select value={lang} onChange={(e) => setLang(e.target.value as Lang)} aria-label="Language">
          {LANGS.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label} · {l.name}
            </option>
          ))}
        </select>
      </label>
      <button
        className="mode-toggle"
        onClick={onToggleMode}
        role="switch"
        aria-checked={mode === "dark"}
        aria-label="Dark mode"
        title={`Switch to ${mode === "dark" ? "light" : "dark"} mode${route.view === "ws" ? " (workspace pages keep the tenant's brand theme)" : ""}`}
      >
        <span className={mode === "light" ? "on" : ""}>
          <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="currentColor" /><g stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></g></svg>
        </span>
        <span className={mode === "dark" ? "on" : ""}>
          <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path fill="currentColor" d="M20.5 14.6A8.5 8.5 0 0 1 9.4 3.5a8.5 8.5 0 1 0 11.1 11.1z" /></svg>
        </span>
      </button>
      <div className="persona-switch" role="tablist" aria-label="Switch user">
        {personas.map((p) => (
          <button
            key={p.id}
            role="tab"
            className={p.id === persona.id ? "active" : ""}
            disabled={!p.available && !(STATIC && p.id === "admin")}
            title={p.available ? p.tagline : STATIC && p.id === "admin" ? "Sign in with your GoodData account" : "No API token for this user"}
            onClick={() => {
              if (STATIC && p.id === "admin" && !p.available) {
                window.location.href = adminLoginUrl(); // GoodData login, then back here as the admin
                return;
              }
              if (p.id !== persona.id) switchPersona(p.id, route).then(() => toast(`Now viewing as ${p.name}`));
            }}
          >
            <span className={`avatar sm ${p.id}`}>{p.initials}</span>
            {p.id === "admin" ? "Admin" : p.name.split(" ")[0]}
          </button>
        ))}
      </div>
      </div>
    </header>
  );
}
