import { useEffect, useRef, useState } from "react";
import { useApp } from "../AppContext";
import type { ColorMode } from "../theme";
import { useChatbot } from "./Chatbot";
import { LANGS, type Lang } from "../i18n";
import { adminLoginUrl, STATIC } from "../staticBackend";
import { Icon } from "../icons";

export function Topbar({ mode, onSetMode }: { mode: ColorMode; onSetMode: (m: ColorMode) => void }) {
  const { personas, persona, switchPersona, route, toast, lang, setLang, t, brand } = useApp();
  const chatbot = useChatbot();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  // dark mode belongs to the platform pages; tenant pages and tenant users always carry the store's brand
  const darkAvailable = !brand.theme && route.view !== "ws";

  useEffect(() => {
    if (!menuOpen) return;
    const close = (e: MouseEvent) => !menuRef.current?.contains(e.target as Node) && setMenuOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [menuOpen]);

  return (
    <header className="topbar">
      <div className="crumbs">
        {route.view === "home" && <b>{t("home")}</b>}
        {route.view === "control" && <b>{t("controlCenter")}</b>}
      </div>
      <div className="top-right">
        <button className={`ai-top-btn ${chatbot.isOpen ? "on" : ""}`} onClick={() => (chatbot.isOpen ? chatbot.close() : chatbot.open())}>
          <Icon name="sparkles" size={15} /> {t("aiAssistant")}
        </button>

        <div className="persona-switch" role="tablist" aria-label="Switch user">
          {personas.map((p) => (
            <button
              key={p.id}
              role="tab"
              className={p.id === persona.id ? "active" : ""}
              disabled={!p.available && !(STATIC && p.id === "admin")}
              title={`${p.name} · ${p.role}${!p.available && STATIC && p.id === "admin" ? " · sign in with your GoodData account" : ""}`}
              onClick={() => {
                if (STATIC && p.id === "admin" && !p.available) {
                  window.location.href = adminLoginUrl(); // GoodData login, then back here as the admin
                  return;
                }
                if (p.id !== persona.id) switchPersona(p.id, route).then(() => toast(`${p.name} · ${p.role}`));
              }}
            >
              <span className={`avatar sm ${p.id}`}>{p.initials}</span>
              {p.id === "admin" ? "Admin" : p.name.split(" ")[0]}
            </button>
          ))}
        </div>

        <div className="settings" ref={menuRef}>
          <button className={`icon-btn ${menuOpen ? "on" : ""}`} onClick={() => setMenuOpen((o) => !o)} aria-label="Settings" aria-expanded={menuOpen} title="Language and appearance">
            <Icon name="settings" size={17} />
          </button>
          {menuOpen && (
            <div className="settings-menu" role="menu">
              <div className="sm-label">
                <Icon name="globe" size={14} /> Language
              </div>
              <div className="seg">
                {LANGS.map((l) => (
                  <button key={l.id} className={l.id === lang ? "on" : ""} onClick={() => setLang(l.id as Lang)} title={l.name}>
                    {l.label}
                  </button>
                ))}
              </div>
              <div className="sm-label">
                <Icon name="sun" size={14} /> Appearance
              </div>
              <div className="seg">
                <button className={mode === "light" || !darkAvailable ? "on" : ""} onClick={() => onSetMode("light")}>
                  <Icon name="sun" size={14} /> Light
                </button>
                <button className={mode === "dark" && darkAvailable ? "on" : ""} disabled={!darkAvailable} onClick={() => onSetMode("dark")}>
                  <Icon name="moon" size={14} /> Dark
                </button>
              </div>
              {!darkAvailable && <div className="sm-hint">Store pages use the store's own brand theme.</div>}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
