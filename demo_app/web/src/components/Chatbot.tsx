/**
 * GoodData AI Assistant docked on the right, ported from goodsalesv4 (AIAssistant + ChatbotOverlay +
 * AppLayout): GoodData's own GenAIAssistant with a collapsible conversation history and a "new chat"
 * button. Every open, and every question sent from the app, starts a fresh conversation that carries the
 * dashboard being viewed as ambient context.
 *
 * Unlike goodsales (one token), the backend is built per persona from that user's API token, so switching
 * users swaps the assistant, its agents and its conversation history for real.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import tigerFactory, { ContextDeferredAuthProvider, TigerTokenAuthProvider } from "@gooddata/sdk-backend-tiger";
import { STATIC } from "../staticBackend";
import { Icon } from "../icons";
import type { IAnalyticalBackend, IUserWorkspaceSettings } from "@gooddata/sdk-backend-spi";
import { idRef, type IGenAIUserContext } from "@gooddata/sdk-model";
import { BackendProvider, WorkspaceProvider } from "@gooddata/sdk-ui";
import { ThemeProvider } from "@gooddata/sdk-ui-theme-provider";
import {
  GenAIAssistant,
  GenAIConversations,
  GenAiStore,
  makeUserItem,
  newMessageAction,
  setAmbientUserContextAction,
  setUserContextAction,
  startNewConversationAction,
  type TextContentObject,
} from "@gooddata/sdk-ui-gen-ai";
import { buildDashboardContext } from "@gooddata/sdk-ui-gen-ai/context";
import { tokenFor } from "../api";
import { useApp } from "../AppContext";
import type { PersonaId, Theme } from "../types";

import "@gooddata/sdk-ui-kit/styles/css/main.css";
import "@gooddata/sdk-ui-charts/styles/css/main.css";
import "@gooddata/sdk-ui-pivot/styles/css/main.css";
import "@gooddata/sdk-ui-ext/styles/css/main.css";
import "@gooddata/sdk-ui-gen-ai/styles/css/main.css";

type Dispatch = (action: any) => void;
type Pending = { text: string; objects: TextContentObject[]; userContext?: IGenAIUserContext };

interface ChatbotApi {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  /** Opens the assistant and asks `message` in a fresh conversation (goodsales' openWithMessage). */
  openWithMessage: (message: string, objects?: TextContentObject[], userContext?: IGenAIUserContext) => void;
  /** Ambient context attached to every message: the dashboard being viewed. */
  setDashboard: (dashboard: { id: string; title: string } | undefined) => void;
}

const ChatbotCtx = createContext<ChatbotApi>({ isOpen: false, open: () => {}, close: () => {}, openWithMessage: () => {}, setDashboard: () => {} });
export const useChatbot = () => useContext(ChatbotCtx);

// one backend per persona, built from that user's API token
const backends = new Map<PersonaId, Promise<IAnalyticalBackend>>();
function backendFor(persona: PersonaId, host: string) {
  if (!backends.has(persona)) {
    backends.set(
      persona,
      STATIC && persona === "admin"
        ? Promise.resolve(tigerFactory().onHostname(host).withAuthentication(new ContextDeferredAuthProvider()))
        : tokenFor(persona).then((token) => tigerFactory().onHostname(host).withAuthentication(new TigerTokenAuthProvider(token))),
    );
  }
  return backends.get(persona)!;
}

// The chat store ignores ambient context until its settings are loaded, so load them first (as goodsales does).
const settingsCache = new Map<string, Promise<IUserWorkspaceSettings | undefined>>();
function settingsFor(key: string, backend: IAnalyticalBackend, ws: string) {
  if (!settingsCache.has(key)) {
    settingsCache.set(
      key,
      backend
        .workspace(ws)
        .settings()
        .getSettingsForCurrentUser()
        .catch(() => undefined),
    );
  }
  return settingsCache.get(key)!;
}

export function ChatbotProvider({ children }: { children: ReactNode }) {
  const { t } = useApp();
  const launcherLabel = t("askAi");
  const [isOpen, setIsOpen] = useState(false);
  const dispatchRef = useRef<Dispatch | null>(null);
  const pendingRef = useRef<Pending | null>(null);
  const dashboardCtxRef = useRef<IGenAIUserContext | undefined>(undefined);

  const send = useCallback((dispatch: Dispatch, { text, objects, userContext }: Pending) => {
    if (userContext) dispatch(setUserContextAction({ userContext }));
    dispatch(newMessageAction(makeUserItem({ type: "text", text, objects } as any)));
  }, []);

  const startFresh = useCallback((dispatch: Dispatch) => {
    dispatch(startNewConversationAction());
    dispatch(setUserContextAction({ userContext: undefined, replaceUserContext: true }));
    dispatch(setAmbientUserContextAction({ userContext: dashboardCtxRef.current }));
  }, []);

  const onDispatcher = useCallback(
    (dispatch: Dispatch) => {
      dispatchRef.current = dispatch;
      startFresh(dispatch);
      if (pendingRef.current) {
        const p = pendingRef.current;
        pendingRef.current = null;
        send(dispatch, p);
      }
    },
    [send, startFresh],
  );

  const openWithMessage = useCallback(
    (text: string, objects: TextContentObject[] = [], userContext?: IGenAIUserContext) => {
      const p = { text, objects, userContext };
      if (dispatchRef.current) {
        startFresh(dispatchRef.current);
        send(dispatchRef.current, p);
      } else pendingRef.current = p;
      setIsOpen(true);
    },
    [send, startFresh],
  );

  const setDashboard = useCallback((d: { id: string; title: string } | undefined) => {
    dashboardCtxRef.current = d ? buildDashboardContext({ ref: idRef(d.id, "analyticalDashboard"), title: d.title, isNew: false, widgets: [] } as any) : undefined;
    dispatchRef.current?.(setAmbientUserContextAction({ userContext: dashboardCtxRef.current }));
  }, []);

  const close = useCallback(() => {
    dispatchRef.current = null; // the panel unmounts its store on close
    setIsOpen(false);
  }, []);

  // embedded dashboards re-measure on window resize: nudge them when the panel opens or closes
  useEffect(() => {
    const t = window.setTimeout(() => window.dispatchEvent(new Event("resize")), 220);
    return () => window.clearTimeout(t);
  }, [isOpen]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && isOpen && close();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  const api = useMemo(() => ({ isOpen, open: () => setIsOpen(true), close, openWithMessage, setDashboard }), [isOpen, close, openWithMessage, setDashboard]);

  return (
    <ChatbotCtx.Provider value={api}>
      {children}
      {isOpen && <ChatbotPanel onClose={close} onDispatcher={onDispatcher} />}
      {!isOpen && (
        <button className="ask-ai-launcher" onClick={() => setIsOpen(true)} aria-label="Ask AI">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path d="M8 12H8.01M12 12H12.01M16 12H16.01" strokeLinecap="round" />
            <path d="M21 12c0 4.4-4 8-9 8-1.6 0-3-.3-4.3-1L3 20l1.2-3.7C3.5 15.1 3 13.6 3 12c0-4.4 4-8 9-8s9 3.6 9 8z" strokeLinejoin="round" />
          </svg>
          {launcherLabel}
        </button>
      )}
    </ChatbotCtx.Provider>
  );
}

/** Workspace the assistant works in: the open workspace, else the user's main one. */
function useChatWorkspace() {
  const { route, persona, workspaces, overview } = useApp();
  if (route.view === "ws") return route.ws;
  if (persona.id === "admin") return overview.parent;
  return workspaces.find((w) => !w.isParent)?.id || workspaces[0]?.id;
}

function goodDataTheme(t?: Theme): any {
  if (!t) return undefined;
  return { palette: t.palette, button: { borderRadius: "8px", dropShadow: false, textCapitalization: false } };
}

function ChatbotPanel({ onClose, onDispatcher }: { onClose: () => void; onDispatcher: (d: Dispatch) => void }) {
  const { persona, overview, themeOf, workspaces, gdLocale, localeVersion, t } = useApp();
  const ws = useChatWorkspace();
  const [backend, setBackend] = useState<IAnalyticalBackend | null>(null);
  const [settings, setSettings] = useState<{ ready: boolean; value?: IUserWorkspaceSettings }>({ ready: false });
  const [historyCollapsed, setHistoryCollapsed] = useState(true);
  const dispatchRef = useRef<Dispatch | null>(null);

  useEffect(() => {
    let live = true;
    setBackend(null);
    setSettings({ ready: false });
    if (!ws) return;
    backendFor(persona.id, overview.host).then((b) => {
      if (!live) return;
      setBackend(b);
      settingsFor(`${persona.id}|${ws}|${localeVersion}`, b, ws).then((value) => live && setSettings({ ready: true, value }));
    });
    return () => {
      live = false;
    };
  }, [persona.id, ws, overview.host, localeVersion]);

  const handleDispatcher = useCallback(
    (d: Dispatch) => {
      dispatchRef.current = d;
      onDispatcher(d);
    },
    [onDispatcher],
  );

  const wsName = workspaces.find((w) => w.id === ws)?.name;
  const theme = ws ? themeOf(ws) : undefined;

  return (
    <aside className="gd-chatbot-panel chatbot-dock" aria-label="AI Assistant">
      <div className="chatbot-header">
        <div>
          <h3 className="gd-chatbot-title">{t("aiAssistant")}</h3>
          <div className="chatbot-sub">
            {wsName} · as {persona.name}
          </div>
        </div>
        <button onClick={onClose} title="Close AI Assistant" aria-label="Close AI Assistant" className="chatbot-close">
          <Icon name="x" size={18} />
        </button>
      </div>
      <div className="chatbot-body">
        {!backend || !settings.ready || !ws ? (
          <div className="chatbot-loading">
            <span className="spinner" /> Connecting the assistant for {persona.name}…
          </div>
        ) : (
          <BackendProvider backend={backend}>
            <WorkspaceProvider workspace={ws}>
              <ThemeProvider theme={goodDataTheme(theme)} enableComplementaryPalette={false} removeGlobalStylesOnUnmout>
                {/* one shared store, so the history list and the chat stay in sync */}
                <GenAiStore key={`${persona.id}|${ws}|${gdLocale}|${localeVersion}`} backend={backend} workspace={ws} onDispatcher={handleDispatcher} settings={settings.value}>
                  <div className="chatbot-columns">
                    <div className={`chatbot-history ${historyCollapsed ? "collapsed" : ""}`}>
                      <div className="chatbot-history-head">
                        {!historyCollapsed && <span className="chatbot-history-title">History</span>}
                        <div className="chatbot-history-buttons">
                          <button className="ch-btn accent" title="New chat" aria-label="New chat" onClick={() => dispatchRef.current?.(startNewConversationAction())}>
                            +
                          </button>
                          <button
                            className="ch-btn"
                            title={historyCollapsed ? "Show history" : "Hide history"}
                            aria-label={historyCollapsed ? "Show history" : "Hide history"}
                            onClick={() => setHistoryCollapsed((c) => !c)}
                          >
                            {historyCollapsed ? "⟲" : "‹"}
                          </button>
                        </div>
                      </div>
                      {!historyCollapsed && (
                        <div className="chatbot-history-list">
                          <GenAIConversations locale={gdLocale} />
                        </div>
                      )}
                    </div>
                    <div className="chatbot-chat">
                      <GenAIAssistant locale={gdLocale} disableFullControl={true} />
                    </div>
                  </div>
                </GenAiStore>
              </ThemeProvider>
            </WorkspaceProvider>
          </BackendProvider>
        )}
      </div>
    </aside>
  );
}
