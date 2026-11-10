import { gd } from "./api";
import type { PersonaId } from "./types";

/** Where each number lives in GoodData, so a tile or driver opens the dashboard at that visualization. */
export interface Target {
  dashboard: string;
  viz: string;
  vizTitle: string;
  dashTitle: string;
}

export interface Kpi {
  id: string;
  label: string;
  metric: string;
  format: "money" | "count" | "pct";
  goodWhenUp: boolean;
  target: Target;
  cur?: number;
  prev?: number;
}

const T = (dashboard: string, dashTitle: string, viz: string, vizTitle: string): Target => ({ dashboard, dashTitle, viz, vizTitle });

export const KPIS: Kpi[] = [
  { id: "net_sales", label: "Net sales", metric: "net_sales", format: "money", goodWhenUp: true, target: T("overview", "Overview", "net_sales_headline", "Net Sales") },
  { id: "orders", label: "Orders", metric: "net_orders", format: "count", goodWhenUp: true, target: T("overview", "Overview", "orders_processed_headline", "Orders Processed") },
  { id: "customers", label: "Active customers", metric: "active_customers", format: "count", goodWhenUp: true, target: T("overview", "Overview", "active_customers_headline", "Active Customers") },
  { id: "gross_profit", label: "Gross profit", metric: "gross_profit", format: "money", goodWhenUp: true, target: T("overview", "Overview", "gross_profit_headline", "Gross Profit") },
];

export const WATCH: Kpi[] = [
  { id: "margin", label: "Gross margin", metric: "gross_profit_margin", format: "pct", goodWhenUp: true, target: T("products", "Products", "gross_profit_by_product_category", "Gross Profit by Product Category") },
  { id: "aov", label: "Avg. order value", metric: "average_order_volume", format: "money", goodWhenUp: true, target: T("sales", "Sales", "average_orders_breakdown", "Average Orders Breakdown") },
  { id: "returns", label: "Return rate", metric: "return_rate", format: "pct", goodWhenUp: false, target: T("products", "Products", "product_performance_by_orders_and_returns", "Product Performance by Orders & Returns") },
  { id: "cancel", label: "Cancellation rate", metric: "order_cancellation_rate", format: "pct", goodWhenUp: false, target: T("sales", "Sales", "completed_vs_canceled_orders_trend", "Completed vs. Canceled Orders Trend") },
];

const DIMS = [
  { id: "product_brand", noun: "Brand", target: T("overview", "Overview", "best_selling_product_brands", "Best-selling Product Brands") },
  { id: "product_category", noun: "Category", target: T("overview", "Overview", "net_sales_by_product_category", "Net Sales by Product Category") },
  { id: "customer_country", noun: "Country", target: T("overview", "Overview", "active_customers_by_country", "Active Customers by Country") },
  { id: "customer_state", noun: "State", target: T("customers", "Customers", "top_5_states_by_number_of_orders", "Top 5 States by Number of Orders") },
];

export interface Driver {
  dim: string;
  noun: string;
  member: string;
  cur: number;
  prev: number;
  delta: number;
  share: number; // of the total net sales change, signed
  target: Target;
}

export interface Insights {
  period: { cur: string; prev: string };
  kpis: Kpi[];
  watch: Kpi[];
  drivers: Driver[];
}

// ------------------------------------------------------------------ execution (as the persona)

const measure = (lid: string, metric: string, quarter: number) => ({
  localIdentifier: lid,
  definition: {
    measure: {
      item: { identifier: { id: metric, type: "metric" } },
      filters: [{ relativeDateFilter: { dataset: { identifier: { id: "date", type: "dataset" } }, granularity: "QUARTER", from: quarter, to: quarter } }],
    },
  },
});

async function execute(persona: PersonaId, ws: string, execution: any, dims: any[]) {
  const r = await gd(persona, `/api/v1/actions/workspaces/${ws}/execution/afm/execute`, {
    method: "POST",
    body: JSON.stringify({ execution: { filters: [], ...execution }, resultSpec: { dimensions: dims } }),
  });
  return gd(persona, `/api/v1/actions/workspaces/${ws}/execution/afm/execute/result/${r.executionResponse.links.executionResult}`);
}

const num = (v: any) => (v === null || v === undefined || v === "" ? undefined : Number(v));

async function kpiValues(persona: PersonaId, ws: string, list: Kpi[]) {
  const measures = list.flatMap((k) => [measure(`${k.id}_c`, k.metric, -1), measure(`${k.id}_p`, k.metric, -2)]);
  const res = await execute(persona, ws, { attributes: [], measures }, [{ localIdentifier: "d0", itemIdentifiers: ["measureGroup"] }]);
  const row: any[] = res.data;
  return list.map((k, i) => ({ ...k, cur: num(row[i * 2]), prev: num(row[i * 2 + 1]) }));
}

async function dimDrivers(persona: PersonaId, ws: string, dim: (typeof DIMS)[number]): Promise<Omit<Driver, "share">[]> {
  const res = await execute(
    persona,
    ws,
    { attributes: [{ localIdentifier: "a", label: { identifier: { id: dim.id, type: "label" } } }], measures: [measure("c", "net_sales", -1), measure("p", "net_sales", -2)] },
    [
      { localIdentifier: "d0", itemIdentifiers: ["a"] },
      { localIdentifier: "d1", itemIdentifiers: ["measureGroup"] },
    ],
  );
  const headers = res.dimensionHeaders?.[0]?.headerGroups?.[0]?.headers || [];
  return headers
    .map((h: any, i: number) => {
      const cur = num(res.data[i][0]) || 0;
      const prev = num(res.data[i][1]) || 0;
      return { dim: dim.id, noun: dim.noun, member: h.attributeHeader.labelValue ?? "(empty)", cur, prev, delta: cur - prev, target: dim.target };
    })
    .filter((d: any) => d.member && d.member !== "_");
}

function quarterLabel(offset: number) {
  const now = new Date();
  let q = Math.floor(now.getMonth() / 3) + offset;
  let y = now.getFullYear();
  while (q < 0) {
    q += 4;
    y -= 1;
  }
  return `Q${q + 1} ${y}`;
}

const cache = new Map<string, Promise<Insights>>();

export function loadInsights(persona: PersonaId, ws: string): Promise<Insights> {
  const key = `${persona}|${ws}`;
  if (!cache.has(key)) {
    const p = (async () => {
      const [kpis, watch, ...perDim] = await Promise.all([
        kpiValues(persona, ws, KPIS),
        kpiValues(persona, ws, WATCH).catch(() => WATCH),
        ...DIMS.map((d) => dimDrivers(persona, ws, d).catch(() => [])),
      ]);
      const ns = kpis.find((k) => k.id === "net_sales")!;
      const total = (ns.cur || 0) - (ns.prev || 0);
      // a dimension with one member explains nothing; keep the biggest movers, at most 2 per dimension
      const candidates = perDim
        .filter((list) => list.length > 1)
        .flatMap((list) => [...list].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 2))
        .filter((d) => Math.abs(d.delta) > 0)
        .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
      const drivers: Driver[] = [];
      for (const d of candidates) {
        if (drivers.length >= 4) break;
        if (drivers.filter((x) => x.dim === d.dim).length >= 2) continue;
        drivers.push({ ...d, share: total ? d.delta / Math.abs(total) : 0 });
      }
      return { period: { cur: quarterLabel(-1), prev: quarterLabel(-2) }, kpis, watch, drivers };
    })();
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  return cache.get(key)!;
}

// ------------------------------------------------------------------ formatting

export function fmt(v: number | undefined, f: Kpi["format"]) {
  if (v === undefined || Number.isNaN(v)) return "—";
  if (f === "pct") return `${(Math.abs(v) <= 1.5 ? v * 100 : v).toFixed(1)}%`;
  const a = Math.abs(v);
  if (f === "count" && a < 1e4) return `${v < 0 ? "−" : ""}${Math.round(a).toLocaleString()}`;
  const s = a >= 1e9 ? `${(a / 1e9).toFixed(1)}B` : a >= 1e6 ? `${(a / 1e6).toFixed(1)}M` : a >= 1e3 ? `${(a / 1e3).toFixed(a >= 1e5 ? 0 : 1)}K` : a.toFixed(f === "money" ? 0 : 0);
  return `${v < 0 ? "−" : ""}${f === "money" ? "$" : ""}${s}`;
}

export function change(k: { cur?: number; prev?: number; format: Kpi["format"] }) {
  if (k.cur === undefined || k.prev === undefined) return null;
  if (k.format === "pct") {
    const pp = ((Math.abs(k.cur) <= 1.5 ? 100 : 1) * (k.cur - k.prev));
    return { up: pp >= 0, text: `${pp >= 0 ? "+" : "−"}${Math.abs(pp).toFixed(1)} pp` };
  }
  if (!k.prev) return null;
  const pct = ((k.cur - k.prev) / Math.abs(k.prev)) * 100;
  return { up: pct >= 0, text: `${pct >= 0 ? "+" : "−"}${Math.abs(pct).toFixed(1)}%` };
}
