import json
import sqlite3
from contextlib import contextmanager
from services.config import database_path


@contextmanager
def db():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version VALUES (1);
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','recruiter')),
            profile TEXT NOT NULL DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), name TEXT NOT NULL,
            content BLOB NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS resumes_user ON resumes(user_id, created_at);
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
            student_id TEXT NOT NULL REFERENCES users(id), resume_id TEXT NOT NULL REFERENCES resumes(id),
            stage TEXT NOT NULL DEFAULT 'submitted', created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, score INTEGER NOT NULL, schedule TEXT,
            UNIQUE(job_id, student_id));
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES users(id),
            question_id TEXT NOT NULL, answer TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS application_stage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            stage TEXT NOT NULL CHECK(stage IN ('submitted','reviewing','interview','offered')),
            created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS application_stage_events_stage
            ON application_stage_events(stage, application_id);
        -- Backfill existing applications once so analytics still includes rows created before this table.
        INSERT INTO application_stage_events (application_id, stage, created_at)
        SELECT a.id, 'submitted', a.created_at FROM applications a
        WHERE NOT EXISTS (SELECT 1 FROM application_stage_events e
                          WHERE e.application_id=a.id AND e.stage='submitted');
        INSERT INTO application_stage_events (application_id, stage, created_at)
        SELECT a.id, a.stage, a.updated_at FROM applications a
        WHERE a.stage != 'submitted'
          AND NOT EXISTS (SELECT 1 FROM application_stage_events e
                          WHERE e.application_id=a.id AND e.stage=a.stage);

        CREATE TABLE IF NOT EXISTS skills (
            name TEXT PRIMARY KEY, normalized_name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS skill_aliases (
            alias TEXT PRIMARY KEY, skill_name TEXT NOT NULL REFERENCES skills(name) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS candidate_skills (
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL REFERENCES skills(name), source TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1, updated_at TEXT NOT NULL,
            PRIMARY KEY(user_id, skill_name, source)
        );
        CREATE TABLE IF NOT EXISTS job_skills (
            job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL REFERENCES skills(name), source TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1, updated_at TEXT NOT NULL,
            PRIMARY KEY(job_id, skill_name, source)
        );
        CREATE TABLE IF NOT EXISTS resume_extractions (
            resume_id TEXT PRIMARY KEY REFERENCES resumes(id) ON DELETE CASCADE,
            extractor_version TEXT NOT NULL, skills_json TEXT NOT NULL,
            extracted_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_predictions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            resume_id TEXT REFERENCES resumes(id) ON DELETE SET NULL,
            model_version TEXT NOT NULL, score INTEGER NOT NULL,
            explanation TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS candidate_skills_skill ON candidate_skills(skill_name);
        CREATE INDEX IF NOT EXISTS job_skills_skill ON job_skills(skill_name);
        CREATE TABLE IF NOT EXISTS learning_plans (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            input_hash TEXT NOT NULL, data TEXT NOT NULL, progress TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL, UNIQUE(user_id,job_id,input_hash)
        );
        CREATE TABLE IF NOT EXISTS coaching_questions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            topic TEXT NOT NULL, question TEXT NOT NULL, keywords TEXT NOT NULL,
            method TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entity_metadata (
            entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
            origin TEXT NOT NULL CHECK(origin IN ('real','demo','test')),
            created_at TEXT NOT NULL, PRIMARY KEY(entity_type,entity_id)
        );
        CREATE TABLE IF NOT EXISTS resume_analysis (
            resume_id TEXT PRIMARY KEY REFERENCES resumes(id) ON DELETE CASCADE,
            data TEXT NOT NULL, confirmed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prediction_snapshots (
            application_id TEXT PRIMARY KEY REFERENCES applications(id) ON DELETE CASCADE,
            prediction TEXT NOT NULL, resume_analysis TEXT NOT NULL
        );
        ''')
        c.execute('INSERT OR IGNORE INTO schema_version VALUES (2)')
        c.execute('INSERT OR IGNORE INTO schema_version VALUES (3)')
        c.execute('INSERT OR IGNORE INTO schema_version VALUES (4)')
        _backfill_skill_index(c)
        backfill_metadata(c)
        from .resume_analysis import local_analysis
        for resume in c.execute('SELECT id,text FROM resumes WHERE id NOT IN (SELECT resume_id FROM resume_analysis)').fetchall():
            from datetime import datetime, timezone
            c.execute('INSERT INTO resume_analysis VALUES (?,?,?,?)',
                      (resume['id'], dump(local_analysis(resume['text'])), 0, datetime.now(timezone.utc).isoformat()))


def _backfill_skill_index(connection):
    """Populate normalized skill tables for old databases without changing source JSON."""
    from datetime import datetime, timezone
    from services.ai.app.engine import SKILLS, extract_skills

    timestamp = datetime.now(timezone.utc).isoformat()
    for skill, aliases in SKILLS.items():
        normalized = skill.casefold()
        connection.execute('INSERT OR IGNORE INTO skills VALUES (?,?,?)', (skill, normalized, timestamp))
        for alias in aliases:
            connection.execute('INSERT OR IGNORE INTO skill_aliases VALUES (?,?)', (alias.casefold(), skill))
    users = connection.execute("SELECT id, role, profile FROM users WHERE role='student'").fetchall()
    connection.execute("DELETE FROM candidate_skills WHERE source='profile'")
    for user in users:
        try:
            profile = json.loads(user['profile'])
        except (TypeError, ValueError):
            profile = {}
        text = ' '.join([profile.get('targetRole', ''), ' '.join(profile.get('skills', [])),
                         profile.get('projectTitle', ''), profile.get('projectSummary', '')])
        for skill in extract_skills(text):
            connection.execute('INSERT OR REPLACE INTO candidate_skills VALUES (?,?,?,?,?)',
                               (user['id'], skill, 'profile', 1, timestamp))
    jobs = connection.execute('SELECT id, data FROM jobs').fetchall()
    connection.execute("DELETE FROM job_skills WHERE source='job-requirement'")
    for row in jobs:
        try:
            job = json.loads(row['data'])
        except (TypeError, ValueError):
            job = {}
        text = ' '.join(job.get('tags', []) + job.get('requirements', []))
        for skill in extract_skills(text):
            connection.execute('INSERT OR REPLACE INTO job_skills VALUES (?,?,?,?,?)',
                               (row['id'], skill, 'job-requirement', 1, timestamp))


def index_candidate_skills(connection, user_id, text, source='profile'):
    from datetime import datetime, timezone
    from services.ai.app.engine import extract_skills
    timestamp = datetime.now(timezone.utc).isoformat()
    connection.execute('DELETE FROM candidate_skills WHERE user_id=? AND source=?', (user_id, source))
    for skill in extract_skills(text):
        connection.execute('INSERT OR REPLACE INTO candidate_skills VALUES (?,?,?,?,?)',
                           (user_id, skill, source, 1, timestamp))


def index_job_skills(connection, job_id, job, source='job-requirement'):
    from datetime import datetime, timezone
    from services.ai.app.engine import extract_skills
    timestamp = datetime.now(timezone.utc).isoformat()
    connection.execute('DELETE FROM job_skills WHERE job_id=? AND source=?', (job_id, source))
    text = ' '.join(job.get('tags', []) + job.get('requirements', []))
    for skill in extract_skills(text):
        connection.execute('INSERT OR REPLACE INTO job_skills VALUES (?,?,?,?,?)',
                           (job_id, skill, source, 1, timestamp))


def index_resume_extraction(connection, resume_id, text, extractor_version='pypdf-text-v1'):
    from datetime import datetime, timezone
    from services.ai.app.engine import extract_skills
    connection.execute('INSERT OR REPLACE INTO resume_extractions VALUES (?,?,?,?)',
                       (resume_id, extractor_version, dump(extract_skills(text)),
                        datetime.now(timezone.utc).isoformat()))


def dump(value):
    return json.dumps(value, ensure_ascii=False)


def record_origin(connection, entity_type, identifier, origin):
    from datetime import datetime, timezone
    connection.execute('INSERT OR IGNORE INTO entity_metadata VALUES (?,?,?,?)',
                       (entity_type, identifier, origin, datetime.now(timezone.utc).isoformat()))


def backfill_metadata(connection):
    from .data_quality import classify_origin
    for row in connection.execute('SELECT id,email,profile FROM users').fetchall():
        record_origin(connection, 'user', row['id'], classify_origin(json.loads(row['profile']), row['id'], row['email']))
    for row in connection.execute('SELECT id,data FROM jobs').fetchall():
        record_origin(connection, 'job', row['id'], classify_origin(json.loads(row['data']), row['id']))
