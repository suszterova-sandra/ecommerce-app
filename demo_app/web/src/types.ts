export type PersonaId = "admin" | "analyze" | "view";

export interface Persona {
  id: PersonaId;
  userId: string;
  name: string;
  initials: string;
  role: string;
  tagline: string;
  available: boolean;
}

export interface Palette {
  primary?: { base?: string; contrast?: string };
  complementary?: Record<string, string>;
}

export interface Theme {
  id: string;
  name: string;
  palette: Palette;
  logo: string | null;
  cover: string | null;
  /** Highlight colour of the brand (theme header activeColor): IKEA yellow, Nike orange, ... */
  accent?: string | null;
}

export interface Permission {
  name: string;
  assignee: { id: string; type: "user" | "userGroup" };
}

export interface OverviewWorkspace {
  id: string;
  name: string;
  isParent: boolean;
  themeId: string | null;
  permissions: Permission[];
  dashboards: { id: string; title: string }[];
}

export interface Wdf {
  id: string;
  title: string;
  column: string;
  values: Record<string, string[]>;
}

export interface HubAgent {
  id: string;
  name: string;
  description?: string;
  skills?: string[];
  availableToAll?: boolean;
  groups: string[];
  conference?: boolean;
}

export interface Overview {
  host: string;
  parent: string;
  reportId: string;
  workspaces: OverviewWorkspace[];
  themes: Record<string, Theme>;
  wdfs: Wdf[];
  groups: Record<string, string>;
  members: Record<PersonaId, string[]>;
  agents: HubAgent[];
  error?: string;
  detail?: string;
}

export interface Workspace {
  id: string;
  name: string;
  isParent: boolean;
}

export type Tab = "home" | "dashboards" | "report" | "analyze" | "agents";

export type Route =
  | { view: "home" }
  | { view: "control" }
  | { view: "ws"; ws: string; tab: Tab; sub?: string; viz?: string }
  | { view: "none" };

export interface AvailableAgent {
  id: string;
  name: string;
  description?: string | null;
  skills?: string[];
}
