import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

// apply the saved light/dark choice before the first paint (no dark flash on the loading screen)
const saved = localStorage.getItem("colorMode");
document.documentElement.dataset.mode =
  saved === "light" || saved === "dark" ? saved : window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
