import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Requests to /api are forwarded to Flask. The browser only ever talks to
// Vite, so the login cookie is same-origin and no CORS setup is needed.
// 127.0.0.1 (not "localhost") avoids an IPv6 mix-up on some Macs.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5555"
    }
  }
});
