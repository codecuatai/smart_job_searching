import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import net from 'node:net';
import { config, WEB_DIR } from './lib/env.mjs';
const root = fileURLToPath(new URL('..', import.meta.url));
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
if (!existsSync(python)) throw new Error('Chạy npm run setup trước.');
const settings = config();
for (const port of [settings.webPort, settings.apiPort, settings.aiPort]) {
  await new Promise((ok, fail) => {
    const server = net.createServer().once('error', () => fail(new Error(`Cổng ${port} đã được sử dụng. Dừng tiến trình cũ trước khi chạy.`)));
    server.listen(port, '127.0.0.1', () => server.close(ok));
  });
}
const children = [];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (process.platform === 'win32' && child.pid) spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' });
    else child.kill('SIGTERM');
  }
  process.exitCode = code;
}
function start(command, args, cwd = root, env = process.env) {
  const child = spawn(command, args, { cwd, env, stdio: 'inherit', windowsHide: true });
  children.push(child);
  child.once('error', error => { console.error(error.message); stop(1); });
  child.once('exit', code => { if (!stopping) stop(code || 0); });
}
process.on('SIGINT', () => stop()); process.on('SIGTERM', () => stop());
start(python, ['-m', 'services.run', 'ai']);
start(python, ['-m', 'services.run', 'api'], root, { ...process.env, AI_SERVICE_URL: settings.aiUrl, ALLOWED_ORIGINS: settings.allowedOrigins });
start(process.execPath, [resolve(WEB_DIR, 'node_modules/next/dist/bin/next'), 'dev', '--hostname', '127.0.0.1', '--port', String(settings.webPort)], WEB_DIR, { ...process.env, NEXT_DIST_DIR: '.next-dev', API_URL: settings.apiUrl });
console.log(`UniTalent: http://localhost:${settings.webPort} | API: http://127.0.0.1:${settings.apiPort}/docs | AI: http://127.0.0.1:${settings.aiPort}/docs`);
