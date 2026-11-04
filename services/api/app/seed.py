import json
import os
from .db import db, dump
from services.config import ROOT
from .security import hash_password


def seed_demo():
    """Idempotent opt-in fixtures, never overwrite an existing profile/job."""
    if os.getenv('SEED_DEMO', 'true').lower() != 'true':
        return
    source = json.loads((ROOT / 'services/api/seed/demo.json').read_text(encoding='utf-8'))
    password = os.getenv('DEMO_PASSWORD', 'demo12345')
    with db() as c:
        c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)',
                  ('demo-recruiter', 'recruitment@vng.com.vn', 'VNG Talent (Demo)', hash_password(password), 'recruiter', '{}'))
        for student in source['students']:
            profile = {k: student[k] for k in ('university', 'major', 'year', 'gpa', 'targetRole')}
            project = student['featuredProject']
            profile.update(skills=project['techStack'], projectTitle=project['title'],
                           projectSummary=project['summary'], projectRepo=project['repo'], demo=True)
            c.execute('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?)',
                      (student['id'], student['email'].lower(), student['name'], hash_password(password), 'student', dump(profile)))
        for job in source['jobs']:
            job.update(isDemo=True, astCleanCodeScore=0, matchScore=0)
            c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?,?)', (job['id'], 'demo-recruiter', dump(job)))
