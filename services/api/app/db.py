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
        ''')


def dump(value):
    return json.dumps(value, ensure_ascii=False)
