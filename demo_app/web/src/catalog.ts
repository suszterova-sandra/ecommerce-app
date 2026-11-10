import { useCallback, useEffect, useState } from "react";
import { gd } from "./api";
import type { PersonaId } from "./types";

/** goodsalesv4's dashboard catalog: Shared vs Private (accessInfo.private), titles in the user's metadata language. */
export interface CatalogDashboard {
  id: string;
  title: string;
  isPrivate: boolean;
}

const byTitle = (a: CatalogDashboard, b: CatalogDashboard) => a.title.localeCompare(b.title, undefined, { numeric: true, sensitivity: "base" });

const cache = new Map<string, Promise<CatalogDashboard[]>>();
const listeners = new Set<() => void>();

function load(persona: PersonaId, ws: string, version: number, force = false) {
  const key = `${persona}|${ws}|${version}`;
  if (force || !cache.has(key)) {
    const p = gd(persona, `/api/v1/entities/workspaces/${ws}/analyticalDashboards?size=200&origin=ALL&metaInclude=accessInfo`).then((d) =>
      d.data.map((x: any) => ({ id: x.id, title: x.attributes.title, isPrivate: Boolean(x.meta?.accessInfo?.private) })).sort(byTitle),
    );
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return cache.get(key)!;
}

/** Re-read a workspace's catalog everywhere it is shown (sidebar, dashboards page). */
export async function refreshCatalog(persona: PersonaId, ws: string, version: number) {
  const fresh = await load(persona, ws, version, true);
  listeners.forEach((l) => l());
  return fresh;
}

export function useCatalog(persona: PersonaId, ws: string | undefined, version: number) {
  const [list, setList] = useState<CatalogDashboard[] | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const l = () => setTick((t) => t + 1);
    listeners.add(l);
    return () => {
      listeners.delete(l);
    };
  }, []);
  useEffect(() => {
    if (!ws) return;
    let live = true;
    load(persona, ws, version)
      .then((d) => live && setList(d))
      .catch(() => live && setList((x) => x || []));
    return () => {
      live = false;
    };
  }, [persona, ws, version, tick]);
  const refresh = useCallback(() => (ws ? refreshCatalog(persona, ws, version) : Promise.resolve([])), [persona, ws, version]);
  return { list, refresh };
}

// workspace permissions per user, shared by the sidebar and the workspace view
const permCache = new Map<string, Promise<string[]>>();
export function usePermissions(persona: PersonaId, ws: string | undefined) {
  const [perms, setPerms] = useState<string[] | null>(null);
  useEffect(() => {
    if (!ws) return;
    let live = true;
    const key = `${persona}|${ws}`;
    if (!permCache.has(key)) {
      const p = gd(persona, `/api/v1/entities/workspaces/${ws}?metaInclude=permissions`).then((d) => (d?.data?.meta?.permissions || []) as string[]);
      p.catch(() => permCache.delete(key));
      permCache.set(key, p);
    }
    setPerms(null);
    permCache
      .get(key)!
      .then((p) => live && setPerms(p))
      .catch(() => live && setPerms([]));
    return () => {
      live = false;
    };
  }, [persona, ws]);
  return perms;
}

export const canCreateContent = (perms: string[] | null) => !!perms && (perms.includes("ANALYZE") || perms.includes("MANAGE"));
