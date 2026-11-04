import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const root = fileURLToPath(new URL('..', import.meta.url));
const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    target: { type: 'string', default: 'auto' },
    input: { type: 'string', default: 'var/data/crawled-jobs.json' },
    'owner-email': { type: 'string', default: 'recruitment@vng.com.vn' },
    apply: { type: 'boolean', default: false },
  },
});
const action = positionals[0];
if (!['import', 'cleanup-e2e'].includes(action) || !['auto', 'local', 'docker'].includes(values.target)) {
  console.error('Dùng: manage-jobs.mjs import|cleanup-e2e --target auto|local|docker [--input FILE] [--apply]');
  process.exit(2);
}
let container = '';
if (values.target !== 'local') {
  const probe = spawnSync('docker', ['compose', 'ps', '--status', 'running', '-q', 'api'], { cwd: root, encoding: 'utf8' });
  container = probe.status === 0 ? probe.stdout.trim().split(/\s+/)[0] : '';
  if (values.target === 'docker' && !container) {
    console.error('API Docker chưa chạy. Không chuyển sang database local khi đã chọn --target docker.');
    process.exit(2);
  }
}
const options = [action, '--owner-email', values['owner-email'], ...(values.apply ? ['--apply'] : [])];
const input = action === 'import' ? readFileSync(resolve(root, values.input)) : undefined;
const executable = container ? 'docker' : resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const args = container
  ? ['exec', '-i', container, 'python', '-m', 'services.api.app.job_maintenance', ...options]
  : ['-m', 'services.api.app.job_maintenance', ...options];
console.error(`Database target: ${container ? 'docker (API đang phục vụ giao diện)' : 'local'}`);
const result = spawnSync(executable, args, { cwd: root, input, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
if (result.error) console.error(result.error.message);
process.exitCode = result.status ?? 1;
