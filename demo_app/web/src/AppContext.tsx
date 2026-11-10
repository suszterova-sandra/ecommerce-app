import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { gd, installEmbedHandshake, setHost } from "./api";
import type { Overview, Persona, PersonaId, Route, Tab, Theme, Workspace } from "./types";
import { localeOf, translate, type Key, type Lang } from "./i18n";
import { logoTile } from "./theme";

interface Ctx {
  personas: Persona[];
  persona: Persona;
  overview: Overview;
  workspaces: Workspace[];
  route: Route;
  navigate: (r: Route) => void;
  switchPersona: (id: PersonaId, route?: Route | null) => Promise<void>;
  refreshOverview: () => Promise<void>;
  themeOf: (wsId: string) => Theme | undefined;
  personaWsPerms: (p: PersonaId, wsId: string) => string[];
  groupName: (id: string) => string;
  toast: (t: string) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  /** GoodData locale of the current language, applied as the user's LOCALE and METADATA_LOCALE. */
  gdLocale: string;
  /** Bumps after GoodData has the new language, so embedded content reloads in it. */
  localeVersion: number;
  /** True once GoodData has this user's language; embeds wait for it so they load only once. */
  localeReady: boolean;
  t: (key: Key, vars?: Record<string, string>) => string;
  /** The shell's branding: the platform for the admin, the user's own tenant for everyone else. */
  brand: { name: string; logo?: string | null; logoBg?: string; theme?: Theme };
  /** The workspace a user belongs to (their tenant); the parent for the admin. */
  homeWs?: string;
}

const AppCtx = createContext<Ctx | null>(null);
export const useApp = () => useContext(AppCtx)!;

const TABS: Tab[] = ["home", "dashboards", "report", "analyze", "agents"];

function parseHash(): Route | null {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (parts[0] === "ws" && parts[1]) {
    const tab = (TABS as string[]).includes(parts[2]) ? (parts[2] as Tab) : "home";
    return { view: "ws", ws: parts[1], tab, sub: parts[3], viz: parts[4] };
  }
  if (parts[0] === "control") return { view: "control" };
  if (parts[0] === "home") return { view: "home" };
  return null;
}

const hashOf = (r: Route) => (r.view === "ws" ? `#/ws/${r.ws}/${r.tab}${r.sub ? "/" + r.sub : ""}${r.sub && r.viz ? "/" + r.viz : ""}` : r.view === "control" ? "#/control" : "#/home");

const RANK = (p: string) => (["MANAGE", "ANALYZE", "VIEW"].indexOf(p) + 10) % 10;

let handshakeInstalled = false;

export function AppProvider({ children }: { children: (state: "loading" | "ready" | string) => ReactNode }) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaId, setPersonaId] = useState<PersonaId>((localStorage.getItem("persona") as PersonaId) || "admin");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [route, setRoute] = useState<Route>({ view: "none" });
  const [status, setStatus] = useState<"loading" | "ready" | string>("loading");
  const [toastText, setToastText] = useState<string | null>(null);
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem("lang") as Lang) || "en");
  const [localeVersion, setLocaleVersion] = useState(0);
  const [localeReady, setLocaleReady] = useState(false);
  const appliedLocale = useRef<Record<string, string>>({});
  const toastTimer = useRef<number>();
  const ovRef = useRef<Overview | null>(null);

  const toast = useCallback((t: string) => {
    setToastText(t);
    clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToastText(null), 2600);
  }, []);

  const navigate = useCallback(
    (r: Route) => {
      if (r.view === "control" && personaId !== "admin") return;
      setRoute(r);
      if (location.hash !== hashOf(r)) history.replaceState(null, "", hashOf(r));
    },
    [personaId],
  );

  const switchPersona = useCallback(async (id: PersonaId, wanted?: Route | null) => {
    const ov = ovRef.current!;
    localStorage.setItem("persona", id);
    const list = await gd(id, "/api/v1/entities/workspaces?include=parent&size=500");
    const ws: Workspace[] = list.data
      .filter((w: any) => w.id === ov.parent || w.relationships?.parent?.data?.id === ov.parent)
      .map((w: any) => ({ id: w.id, name: w.attributes.name.trim(), isParent: w.id === ov.parent }))
      .sort((a: Workspace, b: Workspace) => Number(b.isParent) - Number(a.isParent) || a.name.localeCompare(b.name));
    const visible = new Set(ws.map((w) => w.id));
    let r: Route | null | undefined = wanted;
    if (!r || r.view === "none" || r.view === "control") r = { view: "home" };
    if (r.view === "ws" && !visible.has(r.ws)) r = ws[0] ? { view: "ws", ws: ws[0].id, tab: r.tab } : { view: "home" };
    setPersonaId(id);
    setWorkspaces(ws);
    setRoute(r);
    history.replaceState(null, "", hashOf(r));
  }, []);

  const refreshOverview = useCallback(async () => {
    const ov: Overview = await fetch("/app/overview?refresh=1").then((r) => r.json());
    if (ov.error) return;
    ovRef.current = ov;
    setOverview(ov);
    const id = (localStorage.getItem("persona") as PersonaId) || "admin";
    const list = await gd(id, "/api/v1/entities/workspaces?include=parent&size=500");
    setWorkspaces(
      list.data
        .filter((w: any) => w.id === ov.parent || w.relationships?.parent?.data?.id === ov.parent)
        .map((w: any) => ({ id: w.id, name: w.attributes.name.trim(), isParent: w.id === ov.parent }))
        .sort((a: Workspace, b: Workspace) => Number(b.isParent) - Number(a.isParent) || a.name.localeCompare(b.name)),
    );
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const p = await fetch("/app/personas").then((r) => r.json());
        if (p.locked) {
          const key = window.prompt("This demo is password protected. Password:");
          if (key) {
            localStorage.setItem("demoKey", key);
            location.reload();
          }
          throw new Error("Password required. Reload the page to try again.");
        }
        setHost(p.host);
        if (!handshakeInstalled) {
          installEmbedHandshake();
          handshakeInstalled = true;
        }
        setPersonas(p.personas);
        const ov: Overview = await fetch("/app/overview").then((r) => r.json());
        if (ov.error) throw new Error(`${ov.error}: ${ov.detail}`);
        ovRef.current = ov;
        setOverview(ov);
        const start: PersonaId = p.personas.find((x: Persona) => x.id === personaId && x.available)
          ? personaId
          : (p.personas.find((x: Persona) => x.available)?.id ?? "admin");
        await switchPersona(start, parseHash());
        setStatus("ready");
      } catch (e: any) {
        setStatus(e.message || String(e));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const onHash = () => {
      const r = parseHash();
      if (r) navigate(r);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [navigate]);

  const setLang = useCallback((l: Lang) => {
    localStorage.setItem("lang", l);
    setLangState(l);
  }, []);

  // GoodData speaks the user's language through their own settings: the UI (LOCALE) and the
  // translated metadata (METADATA_LOCALE, from the workspaces' de-DE / fr-FR translations).
  // Read them first and write only what differs: embedded dashboards wait for this (localeReady), so each
  // one loads once, in the right language, instead of loading and then reloading.
  useEffect(() => {
    if (!personas.length) return;
    const locale = localeOf(lang);
    const userId = personas.find((p) => p.id === personaId)?.userId;
    if (!userId) return;
    if (appliedLocale.current[userId] === locale || localStorage.getItem(`gdLocale:${userId}`) === locale) {
      appliedLocale.current[userId] = locale;
      setLocaleReady(true);
      return;
    }
    let live = true;
    setLocaleReady(false);
    (async () => {
      let current: Record<string, string> = {};
      try {
        const r = await gd(personaId, `/api/v1/entities/users/${userId}/userSettings?size=100`);
        current = Object.fromEntries(r.data.map((x: any) => [x.attributes.type, x.attributes.content?.value]));
      } catch {
        // e.g. the admin on the static site without a GoodData session: just try to write
      }
      let changed = false;
      for (const [id, type] of [
        ["locale", "LOCALE"],
        ["metadataLocale", "METADATA_LOCALE"],
      ]) {
        if (current[type] === locale || (!current[type] && locale === "en-US")) continue;
        changed = true;
        const body = JSON.stringify({ data: { id, type: "userSetting", attributes: { type, content: { value: locale } } } });
        const headers = { "Content-Type": "application/vnd.gooddata.api+json" };
        try {
          await gd(personaId, `/api/v1/entities/users/${userId}/userSettings/${id}`, { method: "PUT", body, headers });
        } catch {
          await gd(personaId, `/api/v1/entities/users/${userId}/userSettings`, { method: "POST", body, headers }).catch((e) => console.warn("locale", e));
        }
      }
      appliedLocale.current[userId] = locale;
      localStorage.setItem(`gdLocale:${userId}`, locale);
      if (changed) {
        if (personaId === "admin") await refreshOverview().catch(() => null);
        if (live) setLocaleVersion((v) => v + 1); // reload content that was showing the old language
      }
      if (live) setLocaleReady(true);
    })();
    return () => {
      live = false;
    };
  }, [lang, personaId, personas, refreshOverview]);

  const value = useMemo<Ctx | null>(() => {
    if (!overview || !personas.length) return null;
    const persona = personas.find((p) => p.id === personaId) || personas[0];
    const homeWs = persona.id === "admin" ? overview.parent : workspaces.find((w) => !w.isParent)?.id || workspaces[0]?.id;
    const homeWsMeta = overview.workspaces.find((w) => w.id === homeWs);
    const tenantTheme = persona.id !== "admin" && homeWsMeta?.themeId ? overview.themes[homeWsMeta.themeId] : undefined;
    const brand = tenantTheme
      ? { name: workspaces.find((w) => w.id === homeWs)?.name || "Store", logo: tenantTheme.logo, logoBg: logoTile(tenantTheme), theme: tenantTheme }
      : { name: "Ecommerce Platform" };
    return {
      brand,
      homeWs,
      personas,
      persona,
      overview,
      workspaces,
      route,
      navigate,
      switchPersona,
      refreshOverview,
      toast,
      themeOf: (wsId) => {
        const w = overview.workspaces.find((x) => x.id === wsId);
        return w?.themeId ? overview.themes[w.themeId] : undefined;
      },
      personaWsPerms: (pid, wsId) => {
        if (pid === "admin") return ["MANAGE"];
        const w = overview.workspaces.find((x) => x.id === wsId);
        const groups = new Set(overview.members[pid] || []);
        const userId = personas.find((p) => p.id === pid)?.userId;
        return [
          ...new Set(
            (w?.permissions || [])
              .filter((p) => (p.assignee.type === "userGroup" && groups.has(p.assignee.id)) || (p.assignee.type === "user" && p.assignee.id === userId))
              .map((p) => p.name),
          ),
        ].sort((a, b) => RANK(a) - RANK(b));
      },
      groupName: (id) => overview.groups[id] || id,
      lang,
      setLang,
      gdLocale: localeOf(lang),
      localeVersion,
      localeReady,
      t: (key, vars) => translate(lang, key, vars),
    };
  }, [overview, personas, personaId, workspaces, route, navigate, switchPersona, refreshOverview, toast, lang, setLang, localeVersion, localeReady]);

  return (
    <>
      {value ? <AppCtx.Provider value={value}>{children(status)}</AppCtx.Provider> : children(status)}
      {toastText && <div className="toast">{toastText}</div>}
    </>
  );
}

export function agentAccess(o: Overview, agent: { availableToAll?: boolean; groups: string[] }, pid: PersonaId) {
  if (agent.availableToAll) return true;
  const groups = new Set(o.members[pid] || []);
  return agent.groups.some((g) => groups.has(g));
}
