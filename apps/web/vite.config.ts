import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": process.env.SDS_API_URL ?? "http://localhost:8000" },
  },
  preview: {
    port: 4173,
    proxy: { "/api": process.env.SDS_API_URL ?? "http://localhost:8000" },
  },
  // The Vosk speech-to-text chunk (~6 MB) is only fetched when a speech model is installed.
  build: { sourcemap: true, chunkSizeWarningLimit: 6500 },
});
