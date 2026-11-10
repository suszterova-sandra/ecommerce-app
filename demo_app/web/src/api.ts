import type { PersonaId } from "./types";

/** Every /gd/ call is made as the given persona; the backend swaps in that user's API token. */
export class GdError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function gd<T = any>(persona: PersonaId, path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch("/gd" + path, {
    ...init,
    headers: {
      "X-Persona": persona,
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers || {}),
    },
  });
  if (!res.ok) throw new GdError(res.status, `${res.status} ${(await res.text().catch(() => "")).slice(0, 300)}`);
  return res.json();
}

const tokens: Partial<Record<PersonaId, string>> = {};

export async function tokenFor(persona: PersonaId): Promise<string> {
  if (!tokens[persona]) {
    const r = await fetch(`/app/token?persona=${persona}`).then((r) => r.json());
    tokens[persona] = r.token;
  }
  return tokens[persona]!;
}

let HOST = "";
export const setHost = (h: string) => (HOST = h);

export const urls = {
  dashboard: (ws: string, id: string, viz?: string) =>
    `${HOST}/embedded/workspace/${ws}/dashboards/?apiTokenAuthentication=true#/dashboard/${id}?apiTokenAuthentication=true&showNavigation=false${viz ? `&visualizationId=${viz}` : ""}`,
  newDashboard: (ws: string) =>
    `${HOST}/embedded/workspace/${ws}/dashboards/?apiTokenAuthentication=true#/new-dashboard?apiTokenAuthentication=true&showNavigation=false`,
  document: (ws: string, id: string) => `${HOST}/embedded/workspace/${ws}/reports/document/${id}?apiTokenAuthentication=true`,
  analyze: (ws: string) =>
    `${HOST}/embedded/workspace/${ws}/analyze/?apiTokenAuthentication=true#/reportId/edit?apiTokenAuthentication=true`,
  app: (ws: string, path: string) => `${HOST}/workspace/${ws}/${path}`,
};

// GoodData posts "resized" once the dashboard is laid out; "loaded" is not always sent
const READY_EVENTS = ["loaded", "resized", "insightRendered", "newInsightInitialized", "dashboardLoaded", "insightOpened"];

/**
 * GoodData embedding handshake: the iframe posts `listeningForApiToken`, we answer with `setApiToken`
 * carrying the token of the persona the iframe was rendered for (data-persona).
 */
export function installEmbedHandshake() {
  window.addEventListener("message", async (e: MessageEvent) => {
    if (!HOST || e.origin !== HOST) return;
    const name = e.data?.gdc?.event?.name;
    const frame = [...document.querySelectorAll<HTMLIFrameElement>("iframe[data-gd]")].find((f) => f.contentWindow === e.source);
    if (!frame) return;
    if (name === "listeningForApiToken") {
      const token = await tokenFor(frame.dataset.persona as PersonaId);
      const product = e.data.gdc.product || "dashboard";
      (e.source as Window).postMessage({ gdc: { product, event: { name: "setApiToken", data: { token, type: "gooddata" } } } }, HOST);
    }
    if (READY_EVENTS.includes(name)) frame.dispatchEvent(new CustomEvent("gd-ready"));
    if (name) frame.dispatchEvent(new CustomEvent("gd-event", { detail: { name, data: e.data?.gdc?.event?.data } }));
  });
}
