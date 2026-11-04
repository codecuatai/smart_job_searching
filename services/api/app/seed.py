import json
import os
from datetime import datetime, timezone
from .db import db, dump
from services.config import ROOT
from .security import hash_password
from .resume_analysis import local_analysis


DEMO_RESUME_PDF = (
    b'%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n'
    b'2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n'
    b'3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
    b'/Resources << >> /Contents 4 0 R >>endobj\n'
    b'4 0 obj<< /Length 0 >>stream\nendstream\nendobj\n'
    b'trailer<< /Root 1 0 R >>\n%%EOF\n'
)


def _seed_application(connection, student, job, stage, score, schedule=None):
    """Create a small, idempotent demo funnel with a downloadable CV per applicant."""
    timestamp = datetime.now(timezone.utc).isoformat()
    resume_id = f"demo-resume-{student['id']}"
    application_id = f"demo-application-{student['id']}-{job['id']}"
    profile = student['featuredProject']
    resume_text = ' '.join([
        student['name'], student['targetRole'], student['university'], student['major'],
        ' '.join(profile['techStack']), profile['title'], profile['summary'],
    ])
    connection.execute(
        'INSERT OR IGNORE INTO resumes (id,user_id,name,content,text,created_at) VALUES (?,?,?,?,?,?)',
        (resume_id, student['id'], f"{student['id']}-cv-demo.pdf", DEMO_RESUME_PDF, resume_text, timestamp),
    )
    analysis = dump(local_analysis(resume_text))
    connection.execute(
        'INSERT OR IGNORE INTO resume_analysis (resume_id,data,confirmed,updated_at) VALUES (?,?,?,?)',
        (resume_id, analysis, 0, timestamp),
    )
    connection.execute(
        '''INSERT OR IGNORE INTO applications
           (id,job_id,student_id,resume_id,stage,created_at,updated_at,score,schedule)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (application_id, job['id'], student['id'], resume_id, stage, timestamp, timestamp, score,
         dump(schedule) if schedule else None),
    )
    existing = connection.execute(
        'SELECT 1 FROM application_stage_events WHERE application_id=? AND stage=?',
        (application_id, 'submitted'),
    ).fetchone()
    if not existing:
        connection.execute(
            'INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
            (application_id, 'submitted', timestamp),
        )
    if stage != 'submitted':
        existing = connection.execute(
            'SELECT 1 FROM application_stage_events WHERE application_id=? AND stage=?',
            (application_id, stage),
        ).fetchone()
        if not existing:
            connection.execute(
                'INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
                (application_id, stage, timestamp),
            )
    connection.execute(
        '''INSERT OR IGNORE INTO model_predictions
           (id,user_id,job_id,resume_id,model_version,score,explanation,created_at)
           VALUES (?,?,?,?,?,?,?,?)''',
        (f"demo-prediction-{student['id']}-{job['id']}", student['id'], job['id'], resume_id,
         'matching-v2.json', score, 'Dữ liệu mẫu để minh họa luồng matching và tuyển dụng.', timestamp),
    )
    connection.execute(
        '''INSERT OR IGNORE INTO prediction_snapshots (application_id,prediction,resume_analysis)
           VALUES (?,?,?)''',
        (application_id, dump({'matchScore': score, 'modelVersion': 'matching-v2.json'}), analysis),
    )


def seed_demo():
    """Idempotent opt-in fixtures, never overwrite an existing profile/job."""
    if os.getenv('SEED_DEMO', 'true').lower() != 'true':
        return
    source = json.loads((ROOT / 'services/api/seed/demo.json').read_text(encoding='utf-8'))
    password = os.getenv('DEMO_PASSWORD', 'demo12345')
    with db() as c:
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)',
                  ('demo-recruiter', 'recruitment@vng.com.vn', 'VNG Talent (Demo)', hash_password(password), 'recruiter',
                   dump({'company': 'VNG Corporation', 'avatarUrl': '/avatars/vng-talent.svg', 'demo': True})))
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)',
                  ('demo-recruiter-fpt', 'talent@fptsoftware.com', 'FPT Software Talent (Demo)', hash_password(password), 'recruiter',
                   dump({'company': 'FPT Software', 'avatarUrl': '/avatars/default-recruiter.svg', 'demo': True})))
        for recruiter_id, avatar in (('demo-recruiter', '/avatars/vng-talent.svg'), ('demo-recruiter-fpt', '/avatars/default-recruiter.svg')):
            existing = c.execute('SELECT profile FROM users WHERE id=?', (recruiter_id,)).fetchone()
            current_profile = json.loads(existing['profile'] or '{}') if existing else {}
            if not current_profile.get('avatarUrl'):
                c.execute('UPDATE users SET profile=? WHERE id=?',
                          (dump({**current_profile, 'avatarUrl': avatar, 'demo': True}), recruiter_id))
        for student in source['students']:
            profile = {k: student[k] for k in ('university', 'major', 'year', 'gpa', 'targetRole')}
            project = student['featuredProject']
            profile.update(skills=project['techStack'], projectTitle=project['title'],
                           avatarUrl=student.get('avatarUrl', '/avatars/default-student.svg'),
                           projectSummary=project['summary'], projectRepo=project['repo'], demo=True)
            c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)',
                      (student['id'], student['email'].lower(), student['name'], hash_password(password), 'student', dump(profile)))
            existing = c.execute('SELECT profile FROM users WHERE id=?', (student['id'],)).fetchone()
            current_profile = json.loads(existing['profile'] or '{}') if existing else {}
            if not current_profile.get('avatarUrl'):
                c.execute('UPDATE users SET profile=? WHERE id=?',
                          (dump({**current_profile, 'avatarUrl': student.get('avatarUrl', '/avatars/default-student.svg')}), student['id']))
        for job in source['jobs']:
            job.update(isDemo=True, astCleanCodeScore=0, matchScore=0)
            c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?,?)', (job['id'], 'demo-recruiter', dump(job)))
        demo_jobs = {row['id']: json.loads(row['data']) for row in c.execute('SELECT id,data FROM jobs WHERE id LIKE \'job-%\'').fetchall()}
        fpt_job = dict(demo_jobs['job-04'], id='job-demo-fpt-frontend', postedAt='Hôm nay', isDemo=True, matchScore=0)
        c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?,?)', (fpt_job['id'], 'demo-recruiter-fpt', dump(fpt_job)))
        demo_jobs[fpt_job['id']] = fpt_job
        applications = [
            (source['students'][0], demo_jobs['job-01'], 'interview', 94,
             {'date': '2026-11-12', 'time': '14:30', 'format': 'Google Meet', 'interviewer': 'Vũ Hoàng · Engineering Manager'}),
            (source['students'][1], demo_jobs['job-02'], 'reviewing', 91, None),
            (source['students'][2], demo_jobs['job-03'], 'submitted', 87, None),
            (source['students'][2], demo_jobs['job-demo-fpt-frontend'], 'submitted', 84, None),
        ]
        for student, job, stage, score, schedule in applications:
            _seed_application(c, student, job, stage, score, schedule)
