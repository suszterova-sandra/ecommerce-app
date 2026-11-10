import { HOST, json, locked, overview, PARENT_WS, PERSONAS, REPORT_ID, tokenFor } from "./_shared.mts";

/** /app/personas, /app/token, /app/overview: same contract as demo_app/server.py. */
export default async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname;

  if (path === "/app/personas") {
    // tells the app whether it must ask for the site password first
    const gate = locked(req);
    return json({
      host: `https://${HOST}`,
      parent: PARENT_WS,
      reportId: REPORT_ID,
      locked: Boolean(gate),
      personas: PERSONAS.map((p) => ({ ...p, available: !gate && Boolean(tokenFor(p.id)) })),
    });
  }

  const gate = locked(req);
  if (gate) return gate;

  if (path === "/app/token") {
    const token = tokenFor(url.searchParams.get("persona"));
    return token ? json({ token }) : json({ error: "no token for persona" }, 404);
  }
  if (path === "/app/overview") {
    try {
      return json(await overview(url.searchParams.has("refresh")));
    } catch (e: any) {
      return json({ error: "GoodData", detail: String(e?.message || e) }, 502);
    }
  }
  return json({ error: "not found" }, 404);
};

export const config = { path: ["/app/personas", "/app/token", "/app/overview"] };
