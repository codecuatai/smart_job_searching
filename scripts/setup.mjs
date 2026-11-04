import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { ensureRootEnv, WEB_DIR } from './lib/env.mjs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('..', import.meta.url));
function run(command, args, cwd = root) {
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell: process.platform === 'win32' && command === 'npm' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
if (!existsSync(python)) run(process.platform === 'win32' ? 'python' : 'python3', ['-m', 'venv', '.venv']);
run(python, ['-m', 'pip', 'install', '-r', 'requirements.lock.txt']);
run('npm', ['ci'], WEB_DIR);
ensureRootEnv();
if (existsSync(resolve(root, '.git'))) run('git', ['config', 'core.hooksPath', '.githooks']);
console.log('Setup hoàn tất. Chạy npm run dev tại thư mục gốc.');
