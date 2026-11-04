import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const root = fileURLToPath(new URL('..', import.meta.url));
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
const args = process.argv.slice(2);
const option = (name, fallback) => {
  const inline = args.find(value => value.startsWith(`${name}=`));
  const index = args.indexOf(name);
  return inline ? inline.slice(name.length + 1) : index >= 0 ? args[index + 1] : fallback;
};
const importDb = args.includes('--import-db');
const target = option('--target', 'auto');
const crawlArgs = args.filter((value, index) => value !== '--import-db' && value !== '--target'
  && !value.startsWith('--target=') && args[index - 1] !== '--target');
const result = spawnSync(python, [resolve(root, 'scripts/crawl_jobs.py'), ...crawlArgs], {
  cwd: root,
  stdio: 'inherit',
});
if (result.error) console.error('Chạy npm run setup trước.', result.error.message);
process.exitCode = result.status || (result.error ? 1 : 0);
if (!process.exitCode && importDb) {
  const imported = spawnSync(process.execPath, [resolve(root, 'scripts/manage-jobs.mjs'), 'import',
    '--target', target, '--input', option('--output', 'var/data/crawled-jobs.json'),
    '--owner-email', option('--owner-email', 'recruitment@vng.com.vn')], { cwd: root, stdio: 'inherit' });
  process.exitCode = imported.status ?? 1;
}
