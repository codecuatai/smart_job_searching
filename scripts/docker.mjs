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
const settings = config();
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

if (command === 'up') run(['compose', 'up', '--build', '-d', '--wait'], dockerEnv);
if (command === 'down') run(['compose', 'down'], dockerEnv);
if (command === 'logs') run(['compose', 'logs', '-f'], dockerEnv);
if (command === 'ps') run(['compose', 'ps'], dockerEnv);
if (command === 'test') {
  run(['compose', 'up', '--build', '-d', '--wait'], dockerEnv);
  run(['compose', '--profile', 'e2e', 'run', '--rm', 'e2e'], dockerEnv);
}

if (command === 'up') console.log(`UniTalent Docker đang chạy: http://127.0.0.1:${settings.webPort}`);
