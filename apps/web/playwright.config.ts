import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

// Uses a preinstalled Chromium when one is available (CI images, sandboxes); otherwise Playwright's own.
const preinstalled = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";

/**
 * End-to-end smoke tests. Needs the API on :8000 with demo data and SDS_RELAX_SCHEDULE=1:
 *   cd backend && uv run python -m app.cli demo && SDS_RELAX_SCHEDULE=1 uv run uvicorn app.main:app
 */
export default defineConfig({
  testDir: "e2e",
  timeout: 300_000,
  retries: 0,
  use: {
    baseURL: process.env.SDS_WEB_URL ?? "http://localhost:5173",
    viewport: { width: 1100, height: 900 },
    launchOptions: {
      executablePath: existsSync(preinstalled) ? preinstalled : undefined,
      args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"],
    },
  },
  webServer: process.env.SDS_WEB_URL ? undefined : {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
  },
});
