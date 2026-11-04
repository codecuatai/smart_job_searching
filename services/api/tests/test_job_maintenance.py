import hashlib
import json
import sqlite3

import pytest

from services.api.app.db import db, dump, init_db
from services.api.app.job_maintenance import cleanup_e2e, import_jobs


@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'test.db'))
    init_db()
    with db() as connection:
        for identifier, email, role in [('owner', 'recruitment@vng.com.vn', 'recruiter'),
                                        ('fixture', 'recruiter-1234abcd@example.test', 'recruiter'),
                                        ('student', 'student@example.test', 'student')]:
            connection.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',
                               (identifier, email, identifier, 'unused', role, '{}'))
    return tmp_path / 'test.db'


def test_cleanup_only_deletes_proven_fixture_jobs_and_their_applications(database):
    with db() as connection:
        for identifier, owner, company in [('fixture-job', 'fixture', 'E2E Company deadbeef'),
                                           ('real-job', 'owner', 'E2E Company deadbeef'),
                                           ('other-job', 'fixture', 'Actual Company')]:
            connection.execute('INSERT INTO jobs VALUES (?,?,?)',
                               (identifier, owner, dump(dict(title='E2E Python SQL deadbeef', company=company))))
        connection.execute('INSERT INTO resumes VALUES (?,?,?,?,?,?)', ('resume', 'student', 'cv.pdf', b'pdf', '', '2026-11-04'))
        connection.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?)',
                           ('app', 'fixture-job', 'student', 'resume', 'submitted', 'now', 'now', 10, None))
        connection.execute('INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
                           ('app', 'submitted', 'now'))
        connection.execute('INSERT INTO model_predictions VALUES (?,?,?,?,?,?,?,?)',
                           ('prediction', 'student', 'fixture-job', 'resume', 'v1', 10, '{}', 'now'))
        connection.execute('INSERT INTO job_skills VALUES (?,?,?,?,?)',
                           ('fixture-job', 'Python', 'job-requirement', 1, 'now'))
    assert cleanup_e2e()['matchedJobs'] == 1
    assert cleanup_e2e()['removedJobs'] == 0
    result = cleanup_e2e(apply=True)
    assert result['removedJobs'] == result['linkedApplications'] == 1
    with sqlite3.connect(result['backup']) as snapshot:
        assert snapshot.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 3
        assert snapshot.execute('SELECT COUNT(*) FROM applications').fetchone()[0] == 1
    with db() as connection:
        assert {row['id'] for row in connection.execute('SELECT id FROM jobs')} == {'real-job', 'other-job'}
        for table in ('applications', 'application_stage_events', 'model_predictions', 'job_skills'):
            assert connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0
        assert connection.execute('SELECT COUNT(*) FROM resumes').fetchone()[0] == 1
        assert connection.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 3
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_import_is_idempotent_updates_skills_and_preserves_applications(database):
    url = 'https://itviec.com/viec-lam-it/python-engineer-1234'
    job = dict(title='Python engineer', company='Company', source='itviec', sourceUrl=url,
               id='malicious-internal-id', tags=['Python'], requirements=['Python'])
    result = import_jobs({'jobs': [job, job]})
    assert result['importedJobs'] == 1
    identifier = 'external-itviec-' + hashlib.sha256(url.encode()).hexdigest()[:24]
    with db() as connection:
        assert connection.execute('SELECT owner_id FROM jobs WHERE id=?', (identifier,)).fetchone()[0] == 'owner'
        connection.execute('INSERT INTO resumes VALUES (?,?,?,?,?,?)', ('resume', 'student', 'cv.pdf', b'pdf', '', 'now'))
        connection.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?)',
                           ('app', identifier, 'student', 'resume', 'submitted', 'now', 'now', 10, None))
    import_jobs([dict(job, title='Updated title', tags=['SQL'], requirements=['SQL'])],
                owner_email='recruiter-1234abcd@example.test')
    with db() as connection:
        stored = connection.execute('SELECT * FROM jobs').fetchone()
        assert stored['id'] == identifier and stored['owner_id'] == 'owner'
        assert json.loads(stored['data'])['title'] == 'Updated title'
        assert connection.execute('SELECT COUNT(*) FROM applications').fetchone()[0] == 1
        assert [row[0] for row in connection.execute('SELECT skill_name FROM job_skills')] == ['SQL']
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_import_rejects_unrelated_source_before_writing(database):
    with pytest.raises(ValueError):
        import_jobs([dict(title='Fake', company='Fake', source='itviec', sourceUrl='https://example.com/fake')])
    with db() as connection:
        assert connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] == 0

