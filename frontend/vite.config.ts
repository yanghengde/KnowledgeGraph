import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  base: "/static/react/",
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../web/static/react"),
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 800,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5050",
    },
  },
});
