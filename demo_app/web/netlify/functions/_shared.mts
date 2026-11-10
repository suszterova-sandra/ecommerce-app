// Netlify port of demo_app/server.py: personas, per-user tokens, the admin overview and the password gate.
import userTokens from "../../../.tokens.json";

export const HOST = "navy-blue-eagle.trial.cloud.gooddata.com";
export const PARENT_WS = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f";
export const REPORT_ID = "ecommerce_business_report";

export const PERSONAS = [
  { id: "admin", userId: "sandra.suszterova", name: "Sandra Suszterova", initials: "SS", role: "Organization admin", tagline: "Manages the parent workspace, tenants, themes and AI agents" },
  { id: "analyze", userId: "sas.analyze.user", name: "Analyze User", initials: "AU", role: "Analyst · Fashion Store", tagline: "Explores data, builds visualizations and metrics" },
  { id: "view", userId: "sas.view.user", name: "View User", initials: "VU", role: "Viewer · Fashion Store", tagline: "Consumes dashboards, reports and AI summaries" },
];

const env = (k: string) => (globalThis as any).Netlify?.env.get(k) ?? process.env[k];

/** Admin token only from the site's environment variables; user tokens from env or the committed .tokens.json. */
export function tokenFor(persona: string | null): string | undefined {
  if (persona === "admin") return env("GOODDATA_API_TOKEN") || undefined;
  if (persona === "analyze") return env("GOODDATA_TOKEN_ANALYZE") || (userTokens as Record<string, string>)["sas.analyze.user"];
  if (persona === "view") return env("GOODDATA_TOKEN_VIEW") || (userTokens as Record<string, string>)["sas.view.user"];
  return undefined;
}

/** When DEMO_PASSWORD is set, every function call must carry it (the app sends it as x-demo-key). */
export function locked(req: Request): Response | null {
  const pw = env("DEMO_PASSWORD");
  if (!pw) return null;
  const given = req.headers.get("x-demo-key") || new URL(req.url).searchParams.get("key");
  return given === pw ? null : json({ error: "password required" }, 401);
}

export const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

async function gd(path: string) {
  const token = tokenFor("admin");
  if (!token) throw new Error("GOODDATA_API_TOKEN is not set in the Netlify site's environment variables");
  const r = await fetch(`https://${HOST}${path}`, { headers: { Authorization: `Bearer ${token}`, Accept: "application/json" } });
  if (!r.ok) throw new Error(`GoodData ${r.status} on ${path}`);
  return r.json();
}

let cached: { t: number; v: any } | null = null;

/** Same structure as server.py's overview; cached for 5 minutes in the warm function instance. */
export async function overview(force = false) {
  if (!force && cached && Date.now() - cached.t < 300_000) return cached.v;
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
      const themeId = settings.data.find((s: any) => s.attributes.type === "ACTIVE_THEME")?.attributes.content.id ?? null;
      return {
        id: w.id,
        name: w.attributes.name.trim(),
        isParent: w.id === PARENT_WS,
        themeId,
        permissions: perms.permissions || [],
        hierarchyPermissions: perms.hierarchyPermissions || [],
        dashboards: dashboards.data.map((d: any) => ({ id: d.id, title: d.attributes.title })),
      };
    }),
  );
  const themeIds = [...new Set(details.map((d: any) => d.themeId).filter(Boolean))] as string[];
  const themeEntries = await Promise.all(
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
      ] as const;
    }),
  );
  const v = {
    host: `https://${HOST}`,
    parent: PARENT_WS,
    reportId: REPORT_ID,
    workspaces: details,
    themes: Object.fromEntries(themeEntries),
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
