import { HOST, json, locked, tokenFor } from "./_shared.mts";

/**
 * /gd/<path> -> GoodData, authenticated as the persona in X-Persona (same as server.py's proxy).
 * The upstream body is passed through as a stream, so AI chat (server-sent events) arrives incrementally.
 */
export default async (req: Request) => {
  const gate = locked(req);
  if (gate) return gate;
  const token = tokenFor(req.headers.get("x-persona") || "admin");
  if (!token) return json({ error: "this user has no API token configured" }, 401);

  const url = new URL(req.url);
  const target = `https://${HOST}${url.pathname.replace(/^\/gd/, "")}${url.search}`;
  const headers: Record<string, string> = { Authorization: `Bearer ${token}`, Accept: req.headers.get("accept") || "*/*" };
  const ct = req.headers.get("content-type");
  if (ct) headers["Content-Type"] = ct;

  const upstream = await fetch(target, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
  });
  const out = new Headers({ "Cache-Control": "no-store" });
  for (const h of ["content-type", "content-disposition"]) {
    const v = upstream.headers.get(h);
    if (v) out.set(h, v);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
};

export const config = { path: "/gd/*" };
