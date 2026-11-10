import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import { installStaticBackend, STATIC } from "./staticBackend";

// static hosting (GitHub Pages): the browser answers /app/* and calls GoodData directly
if (STATIC) installStaticBackend();

// apply the saved light/dark choice before the first paint (no dark flash on the loading screen)
const saved = localStorage.getItem("colorMode");
document.documentElement.dataset.mode =
  saved === "light" || saved === "dark" ? saved : window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";

// Hosted on Netlify with DEMO_PASSWORD: every /app and /gd call carries the password the visitor entered.
const nativeFetch = window.fetch.bind(window);
window.fetch = (input: RequestInfo | URL, init: RequestInit = {}) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
  const key = localStorage.getItem("demoKey");
  if (key && (url.startsWith("/app/") || url.startsWith("/gd/"))) {
    const headers = new Headers(init.headers);
    headers.set("x-demo-key", key);
    init = { ...init, headers };
  }
  return nativeFetch(input, init);
};

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
