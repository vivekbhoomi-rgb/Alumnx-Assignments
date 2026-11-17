import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api calls are proxied to the FastAPI backend during development.
export default defineConfig({
  plugins: [react()],
  server: { port: 8001, proxy: { "/api": "http://localhost:8000" } },
});

