import {spawnSync} from 'node:child_process';
import {ROOT, config, ensureRootEnv} from './lib/env.mjs';

ensureRootEnv(); config();
function docker(args, input) {
  const result = spawnSync('docker', ['compose', 'exec', '-T', ...args], {
    cwd: ROOT, env: process.env, input, maxBuffer: 256 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(result.stderr.toString() || 'Recovery verification failed');
  return result.stdout;
}

// Restore only temporary copies. Never stop or overwrite the live database.
const sqlite = docker(['api', 'python', '-c', `
import json, sqlite3, tempfile
from pathlib import Path
from services.config import database_path
with tempfile.TemporaryDirectory(prefix='recovery-verify-') as folder:
    source = sqlite3.connect(database_path())
    backup = sqlite3.connect(Path(folder) / 'backup.db')
    source.backup(backup)
    source.close()
    expected = {t: backup.execute('SELECT COUNT(*) FROM "' + t + '"').fetchone()[0] for t in ('users','jobs','applications','resumes')}
    restored = sqlite3.connect(Path(folder) / 'restored.db')
    restored.execute('CREATE TABLE disposable_marker (id INTEGER)')
    backup.backup(restored)
    assert restored.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert not restored.execute("SELECT name FROM sqlite_master WHERE name='disposable_marker'").fetchall()
    actual = {t: restored.execute('SELECT COUNT(*) FROM "' + t + '"').fetchone()[0] for t in expected}
    assert expected == actual
    restored.close(); backup.close()
    print(json.dumps(dict(sqlite='passed', restoredCounts=actual)))
`]);
console.log(sqlite.toString().trim());

const database = `unitalent_recovery_verify_${Date.now()}`;
const countSql = 'SELECT (SELECT COUNT(*) FROM fact_job), (SELECT COUNT(*) FROM fact_candidate_skill), (SELECT COUNT(*) FROM fact_application_stage)';
const psql = (db, query) => docker(['warehouse','psql','-U','postgres','-d',db,'-At','-c',query]).toString().trim();
const expected = psql('unitalent_analytics', countSql);
const dump = docker(['warehouse','pg_dump','-U','postgres','-Fc','unitalent_analytics']);
let created = false;
try {
  docker(['warehouse','createdb','-U','postgres',database]); created = true;
  docker(['warehouse','pg_restore','-U','postgres','--no-owner','--no-acl','--exit-on-error','-d',database], dump);
  const actual = psql(database, countSql);
  if (actual !== expected) throw new Error(`Warehouse restore counts differ: ${actual} / ${expected}`);
  console.log(JSON.stringify({postgres:'passed', restoredCounts:actual, temporaryDatabase:database}));
} finally {
  if (created) docker(['warehouse','dropdb','-U','postgres',database]);
}
