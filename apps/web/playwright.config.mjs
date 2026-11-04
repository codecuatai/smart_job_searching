import { defineConfig } from '@playwright/test';
// Keep this configuration in ESM so it can share the root environment loader.
import { config } from '../../scripts/lib/env.mjs';
const settings = config();

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  outputDir: '../../artifacts/e2e/results',
  reporter: [
    ['line'],
    ['html', { outputFolder: '../../artifacts/e2e/report', open: 'never' }],
    ['json', { outputFile: '../../artifacts/e2e/results.json' }],
  ],
  use: {
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    baseURL: settings.e2eBaseUrl,
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    locale: 'vi-VN',
    timezoneId: 'Asia/Bangkok',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
});
