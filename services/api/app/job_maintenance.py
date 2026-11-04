"""Import external jobs and remove proven E2E fixtures from the selected DB."""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

from services.config import database_path
from .db import db, dump, index_job_skills, init_db, record_origin
from .data_quality import canonical_url, normalized_job


def backup_database(label):
    path = database_path()
    folder = path.parent / 'backups'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target = folder / f'{label}-{stamp}-{uuid4().hex[:8]}.sqlite3'
    with sqlite3.connect(path) as source, sqlite3.connect(target) as snapshot:
        source.backup(snapshot)
    return str(target)


def delete_job(connection, job_id):
    # Applications do not cascade from jobs. Their stage events do cascade.
    connection.execute('DELETE FROM applications WHERE job_id=?', (job_id,))
    connection.execute('DELETE FROM jobs WHERE id=?', (job_id,))


def cleanup_e2e(*, apply=False):
    with db() as connection:
        matches = []
        for row in connection.execute('SELECT j.id,j.data,u.email FROM jobs j JOIN users u ON u.id=j.owner_id'):
            job = json.loads(row['data'])
            token = re.fullmatch(r'E2E Python SQL ([0-9a-f]{8})', job.get('title', ''))
            if (token and job.get('company') == f'E2E Company {token[1]}'
                    and re.fullmatch(r'recruiter-[0-9a-f]{8}@example\.test', row['email'])):
                matches.append(row['id'])
        applications = sum(connection.execute('SELECT COUNT(*) FROM applications WHERE job_id=?', (identifier,)).fetchone()[0]
                           for identifier in matches)
    backup = backup_database('before-e2e-cleanup') if apply and matches else None
    if apply:
        with db() as connection:
            for identifier in matches:
                delete_job(connection, identifier)
    return dict(database=str(database_path()), matchedJobs=len(matches),
                removedJobs=len(matches) if apply else 0, linkedApplications=applications,
                applied=apply, backup=backup)


def import_jobs(payload, owner_email='recruitment@vng.com.vn'):
    jobs = payload.get('jobs') if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        raise ValueError('File nhập phải là danh sách job hoặc JSON có trường jobs.')
    unique = {}
    hosts = {'itviec': {'itviec.com', 'www.itviec.com'}, 'topcv': {'topcv.vn', 'www.topcv.vn'}}
    for item in jobs:
        if not isinstance(item, dict):
            raise ValueError('Job không hợp lệ.')
        job = dict(item)
        source, url = job.get('source'), job.get('sourceUrl', '')
        parsed = urlparse(url)
        if source not in hosts or parsed.scheme != 'https' or parsed.hostname not in hosts[source]:
            raise ValueError('Job phải có source/sourceUrl HTTPS thuộc TopCV hoặc ITviec.')
        if not job.get('title') or not job.get('company'):
            raise ValueError('Job thiếu title hoặc company.')
        url = canonical_url(url)
        job['sourceUrl'] = url
        job['importedAt'] = datetime.now(timezone.utc).isoformat()
        # Never permit a supplied ID to overwrite an internal/recruiter job.
        job['id'] = f'external-{source}-' + hashlib.sha256(url.encode()).hexdigest()[:24]
        job['normalized'] = normalized_job(job)
        job['isDemo'] = False
        unique[job['id']] = job
    if not unique:
        return dict(database=str(database_path()), importedJobs=0, sources={})
    with db() as connection:
        owner = connection.execute('SELECT id FROM users WHERE email=? AND role=?',
                                   (owner_email.lower(), 'recruiter')).fetchone()
        if owner is None:
            raise ValueError(f'Không tìm thấy recruiter {owner_email}.')
        owner_id = owner['id']
    backup = backup_database('before-job-import')
    with db() as connection:
        for job in unique.values():
            # REPLACE would delete the old row and can break existing applications.
            connection.execute('''INSERT INTO jobs (id,owner_id,data) VALUES (?,?,?)
                ON CONFLICT(id) DO UPDATE SET data=excluded.data''', (job['id'], owner_id, dump(job)))
            connection.execute('DELETE FROM job_skills WHERE job_id=?', (job['id'],))
            index_job_skills(connection, job['id'], job)
            record_origin(connection, 'job', job['id'], 'real')
    return dict(database=str(database_path()), importedJobs=len(unique),
                sources=dict(Counter(job['source'] for job in unique.values())), backup=backup,
                sourceErrors=payload.get('errors', {}) if isinstance(payload, dict) else {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('cleanup-e2e', 'import'))
    parser.add_argument('--apply', action='store_true', help='Xóa E2E; mặc định chỉ liệt kê số lượng.')
    parser.add_argument('--owner-email', default='recruitment@vng.com.vn')
    args = parser.parse_args()
    init_db()
    result = (cleanup_e2e(apply=args.apply) if args.action == 'cleanup-e2e'
              else import_jobs(json.loads(sys.stdin.buffer.read().decode('utf-8')), args.owner_email))
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
