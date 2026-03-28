const { defineConfig } = require('@playwright/test');

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8000';
const useLocalServer = !process.env.PLAYWRIGHT_BASE_URL;

module.exports = defineConfig({
  testDir: './tests-e2e',
  timeout: 30_000,
  fullyParallel: false,
  use: {
    baseURL,
    headless: true,
  },
  webServer: useLocalServer
    ? {
        command: 'python -m uvicorn main:app --host 127.0.0.1 --port 8000',
        url: 'http://127.0.0.1:8000',
        reuseExistingServer: true,
        timeout: 120_000,
      }
    : undefined,
});