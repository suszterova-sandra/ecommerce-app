import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Python backend (../server.py, port 8765) holds the API tokens and proxies GoodData.
// Port 5173 is in the org's allowed embedding origins, so keep it.
const backend = "http://127.0.0.1:8765";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/gd": backend, "/app": backend },
  },
});
