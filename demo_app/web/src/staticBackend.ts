/**
 * Backend-less mode for static hosting (GitHub Pages): the browser does what demo_app/server.py does.
 * No token is ever part of the build; the presenter enters them once and they stay in this browser's
 * localStorage. /app/* is answered here, /gd/* goes straight to GoodData with the persona's token
 * (the site's origin must be in the GoodData organization's allowed origins).
 */
export const STATIC = import.meta.env.VITE_STATIC === "1";

const HOST = "navy-blue-eagle.trial.cloud.gooddata.com";
const PARENT_WS = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f";
const REPORT_ID = "ecommerce_business_report";
const STORE = "demoTokens";

export const PERSONAS = [
  { id: "admin", userId: "sandra.suszterova", name: "Sandra Suszterova", initials: "SS", role: "Organization admin", tagline: "Manages the parent workspace, tenants, themes and AI agents" },
  { id: "analyze", userId: "sas.analyze.user", name: "Analyze User", initials: "AU", role: "Analyst · Fashion Store", tagline: "Explores data, builds visualizations and metrics" },
  { id: "view", userId: "sas.view.user", name: "View User", initials: "VU", role: "Viewer · Fashion Store", tagline: "Consumes dashboards, reports and AI summaries" },
];

export type StoredTokens = Partial<Record<"admin" | "analyze" | "view", string>>;

export function storedTokens(): StoredTokens {
  try {
    return JSON.parse(localStorage.getItem(STORE) || "{}");
  } catch {
    return {};
  }
}

export function saveTokens(t: StoredTokens) {
  localStorage.setItem(STORE, JSON.stringify(t));
}

export function clearTokens() {
  localStorage.removeItem(STORE);
}

const json = (obj: unknown, status = 200) => new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

let cached: { t: number; v: any } | null = null;

async function overview(nativeFetch: typeof fetch, force: boolean) {
  if (!force && cached && Date.now() - cached.t < 300_000) return cached.v;
  const token = storedTokens().admin;
  if (!token) throw new Error("No admin token");
  const gd = async (path: string) => {
    const r = await nativeFetch(`https://${HOST}${path}`, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
    if (!r.ok) throw new Error(`GoodData ${r.status} on ${path}`);
    return r.json();
  };
  const [ws, wdf, groups, agents, ...users] = await Promise.all([
    gd("/api/v1/entities/workspaces?include=parent&size=500"),
    gd("/api/v1/layout/workspaceDataFilters"),
    gd("/api/v1/entities/userGroups?size=200"),
    gd("/api/v1/entities/agents?include=userGroups&size=200"),
    ...PERSONAS.map((p) => gd(`/api/v1/entities/users/${p.userId}?include=userGroups`)),
  ]);
  const tree = ws.data.filter((w: any) => w.id === PARENT_WS || w.relationships?.parent?.data?.id === PARENT_WS);
  const details = await Promise.all(
    tree.map(async (w: any) => {
      const [settings, perms, dashboards] = await Promise.all([
        gd(`/api/v1/entities/workspaces/${w.id}/workspaceSettings?origin=NATIVE`),
        gd(`/api/v1/layout/workspaces/${w.id}/permissions`),
        gd(`/api/v1/entities/workspaces/${w.id}/analyticalDashboards?size=100&origin=ALL`),
      ]);
      return {
        id: w.id,
        name: w.attributes.name.trim(),
        isParent: w.id === PARENT_WS,
        themeId: settings.data.find((s: any) => s.attributes.type === "ACTIVE_THEME")?.attributes.content.id ?? null,
        permissions: perms.permissions || [],
        hierarchyPermissions: perms.hierarchyPermissions || [],
        dashboards: dashboards.data.map((d: any) => ({ id: d.id, title: d.attributes.title })),
      };
    }),
  );
  const themeIds = [...new Set(details.map((d: any) => d.themeId).filter(Boolean))] as string[];
  const themes = Object.fromEntries(
    await Promise.all(
      themeIds.map(async (tid) => {
        const a = (await gd(`/api/v1/entities/themes/${tid}`)).data.attributes;
        const assets = a.content.assets || {};
        return [
          tid,
          {
            id: tid,
            name: a.name || tid,
            palette: a.content.palette || {},
            logo: (assets.logos || []).find((l: any) => l.id === "logo")?.url ?? null,
            cover: (assets.backgrounds || []).find((b: any) => b.id === "cover_bg")?.url ?? null,
          },
        ];
      }),
    ),
  );
  const v = {
    host: `https://${HOST}`,
    parent: PARENT_WS,
    reportId: REPORT_ID,
    workspaces: details,
    themes,
    wdfs: wdf.workspaceDataFilters
      .filter((f: any) => f.workspace?.id === PARENT_WS)
      .map((f: any) => ({
        id: f.id,
        title: f.title,
        column: f.columnName,
        values: Object.fromEntries(f.workspaceDataFilterSettings.map((s: any) => [s.workspace.id, s.filterValues])),
      })),
    groups: Object.fromEntries(groups.data.map((g: any) => [g.id, g.attributes.name || g.id])),
    members: Object.fromEntries(PERSONAS.map((p, i) => [p.id, (users[i].data.relationships?.userGroups?.data || []).map((g: any) => g.id)])),
    agents: agents.data
      .filter((a: any) => a.attributes.enabled && !a.attributes.isPreview)
      .map((a: any) => ({
        id: a.id,
        name: a.attributes.name,
        description: a.attributes.description,
        skills: a.attributes.skillsMode === "custom" ? a.attributes.customSkills : ["all skills"],
        availableToAll: a.attributes.availableToAll,
        groups: (a.relationships?.userGroups?.data || []).map((g: any) => g.id),
        conference: a.id.startsWith("conference-"),
      })),
  };
  cached = { t: Date.now(), v };
  return v;
}

/** Replaces window.fetch for /app/* and /gd/* when the app runs without a backend. */
export function installStaticBackend() {
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(raw, window.location.origin);
    const sameOrigin = url.origin === window.location.origin;
    if (!sameOrigin) return nativeFetch(input, init);
    const tokens = storedTokens();

    if (url.pathname.endsWith("/app/personas")) {
      return json({
        host: `https://${HOST}`,
        parent: PARENT_WS,
        reportId: REPORT_ID,
        personas: PERSONAS.map((p) => ({ ...p, available: Boolean(tokens[p.id as keyof StoredTokens]) })),
      });
    }
    if (url.pathname.endsWith("/app/token")) {
      const t = tokens[(url.searchParams.get("persona") || "") as keyof StoredTokens];
      return t ? json({ token: t }) : json({ error: "no token" }, 404);
    }
    if (url.pathname.endsWith("/app/overview")) {
      try {
        return json(await overview(nativeFetch, url.searchParams.has("refresh")));
      } catch (e: any) {
        return json({ error: "GoodData", detail: String(e?.message || e) }, 502);
      }
    }
    const gdAt = url.pathname.indexOf("/gd/");
    if (gdAt >= 0) {
      const headers = new Headers(init.headers);
      const persona = (headers.get("X-Persona") || "admin") as keyof StoredTokens;
      const token = tokens[persona];
      if (!token) return json({ error: "no token for this user" }, 401);
      headers.delete("X-Persona");
      headers.set("Authorization", `Bearer ${token}`);
      return nativeFetch(`https://${HOST}${url.pathname.slice(gdAt + 3)}${url.search}`, { ...init, headers });
    }
    return nativeFetch(input, init);
  };
}
