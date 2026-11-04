import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { config, WEB_DIR } from './lib/env.mjs';

const settings = config();
const [command = 'dev', ...args] = process.argv.slice(2);
if (!['dev', 'build', 'start'].includes(command)) throw new Error('Expected dev, build or start.');
const options = command === 'build' ? [] : ['--hostname', process.env.WEB_HOST || '127.0.0.1', '--port', String(settings.webPort)];
const child = spawn(process.execPath, [resolve(WEB_DIR, 'node_modules/next/dist/bin/next'), command, ...options, ...args], {
  cwd: WEB_DIR, stdio: 'inherit', windowsHide: true,
  env: { ...process.env, API_URL: settings.apiUrl, ...(command === 'dev' ? { NEXT_DIST_DIR: '.next-dev' } : {}) },
});
child.once('error', error => { console.error(error.message); process.exitCode = 1; });
child.once('exit', code => { process.exitCode = code || 0; });
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
