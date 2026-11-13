import type { Theme } from "./types";

export type ColorMode = "light" | "dark";

/** Platform pages (Home, Control Center) without a tenant theme follow the light/dark switch. */
const SHELL: Record<ColorMode, Record<string, string>> = {
  light: {
    "--ws-primary": "#F2C318", "--ws-contrast": "#0B0D10", "--ws-bg": "#F6F7F9", "--ws-surface": "#FFFFFF",
    "--ws-panel": "#F1F3F6", "--ws-line": "#E3E6EB", "--ws-muted": "#6B7280", "--ws-text": "#14171C",
    "--ws-accent": "#F2C318", "--ws-accent-contrast": "#0B0D10",
  },
  dark: {
    "--ws-primary": "#F2C318", "--ws-contrast": "#0B0D10", "--ws-bg": "#0B0D10", "--ws-surface": "#14171C",
    "--ws-panel": "#1B1F25", "--ws-line": "#2A3038", "--ws-muted": "#9BA3AE", "--ws-text": "#F2F4F7",
    "--ws-accent": "#F2C318", "--ws-accent-contrast": "#0B0D10",
  },
};

/** Map a GoodData theme palette onto the CSS variables the app shell uses. */
export function themeVars(t?: Theme | null, mode: ColorMode = "light"): Record<string, string> {
  if (!t) return SHELL[mode];
  const p = t.palette || {};
  const c = p.complementary || {};
  return {
    "--ws-primary": p.primary?.base || "#F2C318",
    "--ws-contrast": p.primary?.contrast || "#0B0D10",
    "--ws-bg": c.c1 || "#F6F7F9",
    "--ws-surface": c.c0 || "#FFFFFF",
    "--ws-panel": c.c2 || "#F1F3F6",
    "--ws-line": c.c3 || "#E3E6EB",
    "--ws-muted": c.c6 || "#6B7280",
    "--ws-text": c.c9 || c.c8 || "#14171C",
    "--ws-accent": t.accent || p.primary?.base || "#F2C318",
    "--ws-accent-contrast": isDark(t.accent || p.primary?.base || "#F2C318") ? "#FFFFFF" : "#0B0D10",
  };
}

export function isDark(hex: string) {
  const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})/i.exec(hex || "");
  if (!m) return false;
  const [r, g, b] = m.slice(1).map((x) => parseInt(x, 16));
  return 0.299 * r + 0.587 * g + 0.114 * b < 110;
}

/** Logos are designed for the theme surface: a white logo on a dark theme needs a dark tile. */
export const logoTile = (t?: Theme | null) => {
  const c0 = t?.palette?.complementary?.c0;
  return c0 && isDark(c0) ? c0 : "#FFFFFF";
};

/** Sidebar/top chrome: platform look for the admin, the tenant's palette for its users. */
export function applyChrome(brand: Theme | null | undefined, useHeader = false) {
  const root = document.documentElement;
  const keys = ["--chrome-bg", "--chrome-panel", "--chrome-line", "--chrome-text", "--chrome-muted", "--chrome-accent", "--chrome-accent-ink"];
  if (!brand) {
    keys.forEach((k) => root.style.removeProperty(k));
    delete root.dataset.chrome;
    return;
  }
  const h = brand.header;
  if (useHeader && h?.backgroundColor && isDark(h.backgroundColor)) {
    const bg = h.backgroundColor;
    const v: Record<string, string> = {
      "--chrome-bg": bg,
      "--chrome-panel": "rgba(255,255,255,.08)",
      "--chrome-line": "rgba(255,255,255,.12)",
      "--chrome-text": h.color || "#FFFFFF",
      "--chrome-muted": "rgba(255,255,255,.62)",
      "--chrome-accent": h.activeColor || brand.accent || "#FFFFFF",
      "--chrome-accent-ink": h.activeColor || brand.accent || "#FFFFFF",
    };
    for (const [k, val] of Object.entries(v)) root.style.setProperty(k, val);
    root.dataset.chrome = "dark";
    return;
  }
  delete root.dataset.chrome;
  const c = brand.palette.complementary || {};
  const primary = brand.palette.primary?.base || "#111111";
  const v: Record<string, string> = {
    "--chrome-bg": c.c1 || "#F6F7F9",
    "--chrome-panel": c.c0 || "#FFFFFF",
    "--chrome-line": c.c3 || "#E3E6EB",
    "--chrome-text": c.c9 || "#14171C",
    "--chrome-muted": c.c6 || "#6B7280",
    "--chrome-accent": primary,
    "--chrome-accent-ink": primary,
  };
  for (const [k, val] of Object.entries(v)) root.style.setProperty(k, val);
}

export function applyTheme(t: Theme | null | undefined, mode: ColorMode) {
  const root = document.documentElement;
  root.dataset.mode = mode;
  const vars = themeVars(t, mode);
  for (const [k, v] of Object.entries(vars)) root.style.setProperty(k, v);
  root.dataset.surface = isDark(vars["--ws-surface"]) ? "dark" : "light";
  root.style.colorScheme = root.dataset.surface;
}
