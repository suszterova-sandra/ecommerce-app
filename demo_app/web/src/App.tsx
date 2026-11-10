import { useEffect, useState } from "react";
import { AppProvider, useApp } from "./AppContext";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { ControlCenter } from "./components/ControlCenter";
import { Home } from "./components/Home";
import { ChatbotProvider, useChatbot } from "./components/Chatbot";
import { WorkspaceView } from "./components/WorkspaceView";
import { applyChrome, applyTheme, type ColorMode } from "./theme";

const initialMode = (): ColorMode => {
  const saved = localStorage.getItem("colorMode");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

function Main() {
  const { route, themeOf, persona, brand } = useApp();
  const chatbot = useChatbot();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("sidebarCollapsed") === "1");
  const [mode, setMode] = useState<ColorMode>(initialMode);
  useEffect(() => {
    // a tenant user's whole platform carries their brand; the admin keeps the platform look
    applyTheme(route.view === "ws" ? themeOf(route.ws) : brand.theme || null, mode);
    applyChrome(brand.theme);
  }, [route, themeOf, mode, brand.theme]);
  const toggleMode = () =>
    setMode((m) => {
      const next = m === "dark" ? "light" : "dark";
      localStorage.setItem("colorMode", next);
      return next;
    });
  const toggle = () =>
    setCollapsed((c) => {
      localStorage.setItem("sidebarCollapsed", c ? "0" : "1");
      return !c;
    });

  return (
    <div className={`app ${collapsed ? "collapsed" : ""} ${chatbot.isOpen ? "chat-open" : ""}`}>
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <main className="main">
        <Topbar mode={mode} onToggleMode={toggleMode} />
        <div className="viewport">
          {route.view === "home" && <Home key={persona.id} />}
          {route.view === "control" && <ControlCenter />}
          {route.view === "ws" && <WorkspaceView key={route.ws} />}
          {route.view === "none" && (
            <div className="page">
              <div className="card locked">
                <div>
                  <div className="ico">🔒</div>
                  <h3>No workspaces shared with this user</h3>
                  <p>Ask an administrator to grant access.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      {(status) =>
        status === "ready" ? (
          <ChatbotProvider>
            <Main />
          </ChatbotProvider>
        ) : (
          <div className="boot">
            {status === "loading" ? (
              <div>
                <span className="spinner" /> <p>Loading the organization…</p>
              </div>
            ) : (
              <div className="error-box">{status}</div>
            )}
          </div>
        )
      }
    </AppProvider>
  );
}
