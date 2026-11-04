import {spawnSync} from 'node:child_process';
import {mkdirSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {ROOT,config,ensureRootEnv} from './lib/env.mjs';

ensureRootEnv();config();
function docker(args,options={}) {
  const result=spawnSync('docker',['compose',...args],{cwd:ROOT,env:process.env,maxBuffer:256*1024*1024,...options});
  if(result.error)throw result.error;
  if(result.status!==0)throw new Error(result.stderr?.toString()||`Docker exited ${result.status}`);
  return result.stdout;
}
const command=process.argv[2];
if(command==='backup'){
  const folder=resolve(ROOT,'var/backups',new Date().toISOString().replaceAll(':','-'));
  mkdirSync(folder,{recursive:true});
  docker(['exec','-T','api','python','-c',"import sqlite3; from services.config import database_path; a=sqlite3.connect(database_path()); b=sqlite3.connect('/tmp/unitalent-backup.db'); a.backup(b); b.close(); a.close()"]);
  docker(['cp','api:/tmp/unitalent-backup.db',resolve(folder,'unitalent.db')]);
  for(const database of ['metabase','unitalent_analytics']){
    writeFileSync(resolve(folder,`${database}.dump`),docker(['exec','-T','warehouse','pg_dump','-U','postgres','-Fc',database]));
  }
  console.log(`Backup SQLite + PostgreSQL: ${folder}`);
}else if(command==='restore'){
  const input=resolve(process.argv[3]||'');
  if(!process.argv[3]||!existsSync(input))throw new Error('Usage: npm run db:restore -- <absolute-or-relative-backup.db>');
  const bytes=readFileSync(input);
  if(bytes.subarray(0,16).toString()!=='SQLite format 3\0')throw new Error('Not a SQLite backup.');
  // Stop all OLTP writers/readers. Keep a consistent pre-restore backup on the volume.
  docker(['stop','web','bi','api']);
  const code="import sys,sqlite3; from pathlib import Path; from services.config import database_path; p=Path('/tmp/restore.db'); p.write_bytes(sys.stdin.buffer.read()); source=sqlite3.connect(p); assert source.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; assert source.execute('SELECT MAX(version) FROM schema_version').fetchone()[0]<=4; target=sqlite3.connect(database_path()); previous=sqlite3.connect(str(database_path())+'.pre-restore'); target.backup(previous); previous.close(); source.backup(target); target.close(); source.close(); print('SQLite restored; previous database saved as .pre-restore')";
  const output=docker(['run','--rm','-T','--no-deps','api','python','-c',code],{input:bytes});
  console.log(output.toString());
  docker(['up','-d','--wait','--wait-timeout','360','api','web','bi']);
  console.log('Restored. The BI worker rebuilds the mart from SQLite. PostgreSQL dumps are retained for disaster recovery.');
}else if(command==='refresh'){
  console.log(docker(['exec','-T','bi','python','-m','services.bi.main','--skip-metabase']).toString());
}else if(command==='verify'){
  console.log(docker(['exec','-T','bi','python','-m','services.bi.verify']).toString());
}else throw new Error('Use db:backup, db:restore or bi:refresh.');
