import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('..', import.meta.url));
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const result = spawnSync(python, ['-m', 'pytest', '-q'], { cwd: root, stdio: 'inherit' });
if (result.error) console.error('Chạy npm run setup trước.', result.error.message);
process.exitCode = result.status || (result.error ? 1 : 0);
