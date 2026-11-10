/**
 * Backend-less mode for static hosting (GitHub Pages). The browser does what demo_app/server.py does:
 *  - Analyze and View users: their API tokens are part of the build (demo_app/.tokens.json), so every
 *    visitor can use the demo and switch between them.
 *  - Admin: no token anywhere. The admin signs in with their own GoodData login; calls then use the
 *    GoodData session (cookies) and the live overview. Without it, visitors get the published snapshot
 *    (public/overview.json, from demo_app/snapshot_overview.py).
 * The site's origin must be in the GoodData organization's allowed origins.
 */
import userTokens from "../../.tokens.json";

export const STATIC = import.meta.env.VITE_STATIC === "1";

export const HOST = "navy-blue-eagle.trial.cloud.gooddata.com";
const PARENT_WS = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f";
const REPORT_ID = "ecommerce_business_report";

const PERSONAS = [
  { id: "admin", userId: "sandra.suszterova", name: "Sandra Suszterova", initials: "SS", role: "Organization admin", tagline: "Sign in with your GoodData account" },
  { id: "analyze", userId: "sas.analyze.user", name: "Analyze User", initials: "AU", role: "Analyst · Fashion Store", tagline: "Explores data, builds visualizations and metrics" },
  { id: "view", userId: "sas.view.user", name: "View User", initials: "VU", role: "Viewer · Fashion Store", tagline: "Consumes dashboards, reports and AI summaries" },
];

const TOKENS: Record<string, string | undefined> = {
  analyze: (userTokens as Record<string, string>)["sas.analyze.user"],
  view: (userTokens as Record<string, string>)["sas.view.user"],
};

/** GoodData's login page, coming back to this page afterwards. */
export const adminLoginUrl = () => `https://${HOST}/appLogin?redirectTo=${encodeURIComponent(window.location.href)}`;

let session: Promise<{ userId: string; name?: string } | null> | null = null;

/** Is someone signed in to GoodData in this browser (the admin path)? */
export function adminSession(nativeFetch: typeof fetch = window.fetch) {
  if (!session) {
    session = nativeFetch(`https://${HOST}/api/v1/profile`, { credentials: "include", redirect: "manual", headers: { Accept: "application/json" } })
      .then((r) => (r.ok ? r.json() : null))
      .then((p) => (p?.userId ? { userId: p.userId, name: p.name } : null))
      .catch(() => null);
  }
  return session;
}

const json = (obj: unknown, status = 200) => new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

let cached: { t: number; v: any } | null = null;

async function liveOverview(nativeFetch: typeof fetch) {
  const gd = async (path: string) => {
    const r = await nativeFetch(`https://${HOST}${path}`, { credentials: "include", headers: { Accept: "application/json" } });
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
            accent: a.content.header?.activeColor ?? null,
          },
        ];
      }),
    ),
  );
  return {
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
}

async function overview(nativeFetch: typeof fetch, force: boolean) {
  if (!force && cached && Date.now() - cached.t < 300_000) return cached.v;
  let v: any;
  if (await adminSession(nativeFetch)) {
    v = await liveOverview(nativeFetch).catch(() => null);
  }
  if (!v) v = await nativeFetch(`${import.meta.env.BASE_URL}overview.json`).then((r) => r.json());
  cached = { t: Date.now(), v };
  return v;
}

/** Replaces window.fetch for /app/* and /gd/* when the app runs without a backend. */
export function installStaticBackend() {
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(raw, window.location.origin);
    if (url.origin !== window.location.origin) return nativeFetch(input, init);

    if (url.pathname.endsWith("/app/personas")) {
      const signedIn = Boolean(await adminSession(nativeFetch));
      return json({
        host: `https://${HOST}`,
        parent: PARENT_WS,
        reportId: REPORT_ID,
        personas: PERSONAS.map((p) => ({ ...p, available: p.id === "admin" ? signedIn : Boolean(TOKENS[p.id]) })),
      });
    }
    if (url.pathname.endsWith("/app/token")) {
      const t = TOKENS[url.searchParams.get("persona") || ""];
      return t ? json({ token: t }) : json({ error: "the admin uses the GoodData session, not a token" }, 404);
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
      const persona = headers.get("X-Persona") || "admin";
      headers.delete("X-Persona");
      const target = `https://${HOST}${url.pathname.slice(gdAt + 3)}${url.search}`;
      if (persona === "admin") return nativeFetch(target, { ...init, headers, credentials: "include" });
      const token = TOKENS[persona];
      if (!token) return json({ error: "no token for this user" }, 401);
      headers.set("Authorization", `Bearer ${token}`);
      return nativeFetch(target, { ...init, headers });
    }
    return nativeFetch(input, init);
  };
}
