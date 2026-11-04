import { existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export const ROOT = fileURLToPath(new URL('../..', import.meta.url));
export const WEB_DIR = resolve(ROOT, 'apps/web');
export const ENV_PATH = resolve(ROOT, '.env');

// Defaults are safe to commit; the actual Gemini key belongs only in .env.
export const DEFAULT_ENV = `# UniTalent: the only environment file in this repository.
# Generate missing configuration with npm run env:init or npm run setup.
COMPOSE_PROJECT_NAME=unitalent
WEB_PORT=3000
API_PORT=8000
AI_PORT=8001
SEED_DEMO=true
DEMO_PASSWORD=demo12345
COOKIE_SECURE=false
DATA_VOLUME=unitalent_data
DATA_VOLUME_EXTERNAL=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_ENABLED=true
GEMINI_TIMEOUT_SECONDS=60
ANALYTICS_DATASET=real
BI_PORT=3001
BI_POSTGRES_PASSWORD=LocalWarehouse-4829
METABASE_DB_PASSWORD=LocalMetadata-4829
BI_READER_PASSWORD=Local-BI-Reader-4829
BI_ADMIN_EMAIL=bi-admin@unitalent.local
BI_ADMIN_PASSWORD=Local-BI-Admin-4829!
BI_REFRESH_SECONDS=60
# Optional: ALLOWED_ORIGINS, DATABASE_PATH, API_URL, AI_SERVICE_URL,
# E2E_BASE_URL, PLAYWRIGHT_CHANNEL. See docs/guides/configuration.md.
`;

export function ensureRootEnv() {
  if (!existsSync(ENV_PATH)) writeFileSync(ENV_PATH, DEFAULT_ENV, { flag: 'wx' });
}

export function loadRootEnv() {
  if (existsSync(ENV_PATH)) process.loadEnvFile(ENV_PATH);
}

function port(name, fallback) {
  const value = Number(process.env[name] || fallback);
  if (!Number.isInteger(value) || value < 1 || value > 65535) throw new Error(`${name} must be a valid TCP port.`);
  return value;
}

export function config() {
  loadRootEnv();
  const webPort = port('WEB_PORT', 3000);
  const apiPort = port('API_PORT', 8000);
  const aiPort = port('AI_PORT', 8001);
  return {
    webPort, apiPort, aiPort,
    apiUrl: process.env.API_URL || `http://127.0.0.1:${apiPort}`,
    aiUrl: process.env.AI_SERVICE_URL || `http://127.0.0.1:${aiPort}`,
    allowedOrigins: process.env.ALLOWED_ORIGINS || `http://localhost:${webPort},http://127.0.0.1:${webPort}`,
    e2eBaseUrl: process.env.E2E_BASE_URL || `http://127.0.0.1:${webPort}`,
  };
}
