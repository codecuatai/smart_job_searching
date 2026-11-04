import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { config, ensureRootEnv } from './lib/env.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));

function run(args, env = process.env) {
  const result = spawnSync('docker', args, { cwd: root, stdio: 'inherit', env, shell: process.platform === 'win32' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

function volumeExists(name) {
  const result = spawnSync('docker', ['volume', 'inspect', name], { cwd: root, stdio: 'ignore', shell: process.platform === 'win32' });
  return result.status === 0;
}

ensureRootEnv();
config();
const volumeName = process.env.DATA_VOLUME || 'unitalent_data';
const dockerEnv = { ...process.env };
if ((process.env.DATA_VOLUME_EXTERNAL || '').toLowerCase() === 'true' && !volumeExists(volumeName)) {
  console.warn(`Docker volume ${volumeName} chưa tồn tại; dùng volume nội bộ unitalent_data cho lần chạy này.`);
  dockerEnv.DATA_VOLUME = 'unitalent_data';
  dockerEnv.DATA_VOLUME_EXTERNAL = 'false';
}

const command = process.argv[2] || 'up';
if (!['up', 'down', 'test', 'logs', 'ps'].includes(command)) {
  console.error('Dùng: npm run docker:up | docker:test | docker:down | docker:logs | docker:ps');
  process.exit(2);
}

if (command === 'up') run(['compose', 'up', '--build', '-d', '--wait', '--wait-timeout', '360'], dockerEnv);
if (command === 'down') run(['compose', 'down'], dockerEnv);
if (command === 'logs') run(['compose', 'logs', '-f'], dockerEnv);
if (command === 'ps') run(['compose', 'ps'], dockerEnv);
if (command === 'test') {
  dockerEnv.COMPOSE_PROJECT_NAME = process.env.E2E_PROJECT_NAME || 'unitalent-test';
  dockerEnv.DATA_VOLUME = dockerEnv.COMPOSE_PROJECT_NAME + '_api_data';
  dockerEnv.DATA_VOLUME_EXTERNAL = 'false';
  dockerEnv.WEB_PORT = process.env.E2E_WEB_PORT || '3100';
  dockerEnv.API_PORT = '8100'; dockerEnv.AI_PORT = '8101';
  dockerEnv.BI_PORT = process.env.E2E_BI_PORT || '3101';
  dockerEnv.ANALYTICS_DATASET = 'test';
  delete dockerEnv.API_URL; delete dockerEnv.AI_SERVICE_URL; delete dockerEnv.ALLOWED_ORIGINS;
  // The test project is disposable by design. Reset only its own app,
  // warehouse and Metabase volumes so failed E2E fixtures cannot pollute the
  // next run; the production compose project/volume is untouched.
  run(['compose', 'down', '--volumes', '--remove-orphans'], dockerEnv);
  run(['compose', 'up', '--build', '-d', '--wait', '--wait-timeout', '360'], dockerEnv);
  run(['compose', '--profile', 'e2e', 'run', '--rm', 'e2e'], dockerEnv);
}

if (command === 'up') console.log(`UniTalent Docker đang chạy: http://127.0.0.1:${dockerEnv.WEB_PORT || 3000} | Metabase: http://127.0.0.1:${dockerEnv.BI_PORT || 3001}`);
