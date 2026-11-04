import io
import hashlib
import csv
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from .db import db, dump, index_candidate_skills, index_job_skills, index_resume_extraction, init_db, record_origin
from services.config import allowed_origins
from .security import current_user, hash_password, require_role, token_hash, verify_password
from .schemas import Answer, ApplyInput, JobInput, Login, Profile, Register, StageInput
from .seed import seed_demo
from .ai_client import ai_request
from .job_maintenance import delete_job
from .resume_pdf import MAX_RESUME_BYTES, read_resume_pdf
from .schemas import CoachingRequest, ProgressRequest
from .schemas import AnalysisConfirmation
from .data_quality import parse_salary, classify_origin, canonical_skills
from .resume_analysis import local_analysis, verify_analysis, ocr_pdf

student_only = require_role('student')
recruiter_only = require_role('recruiter')


@asynccontextmanager
async def lifespan(_app):
    init_db()
    seed_demo()
    from .db import backfill_metadata
    with db() as connection:
        backfill_metadata(connection)
    yield


app = FastAPI(title='UniTalent API', version='1.0.0', lifespan=lifespan)


@app.middleware('http')
async def same_origin(request: Request, call_next):
    # Cookie-based mutations accept only configured browser origins. CLI has no Origin.
    origin = request.headers.get('origin')
    allowed = allowed_origins()
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin and origin not in allowed:
        return Response('Origin không được phép.', status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


def salary_range(value):
    """Parse common Vietnamese salary strings into VND bounds; ignore negotiable/unparseable values."""
    salary = parse_salary(value)
    if salary['status'] != 'parsed' or salary['currency'] != 'VND' or salary['period'] != 'MONTH':
        return None
    if salary['minimum'] is None or salary['maximum'] is None:
        return None
    return salary['minimum'], salary['maximum']


def public_user(user):
    return {k: user[k] for k in ('id', 'email', 'name', 'role')} | {'avatarUrl': avatar_url(user)}


def avatar_url(user):
    """Return a local, privacy-safe avatar asset for a user profile."""
    profile_value = user['profile'] if 'profile' in user.keys() else user.get('profile')
    role = user['role'] if 'role' in user.keys() else user.get('role')
    try:
        profile = json.loads(profile_value or '{}')
    except (TypeError, ValueError):
        profile = {}
    return profile.get('avatarUrl') or (
        '/avatars/default-recruiter.svg' if role == 'recruiter' else '/avatars/default-student.svg'
    )


def create_session(user, response):
    token = secrets.token_urlsafe(32)
    with db() as c:
        c.execute('DELETE FROM sessions WHERE expires_at<?', (time.time(),))
        c.execute('INSERT INTO sessions VALUES (?,?,?)', (token_hash(token), user['id'], time.time() + 86400))
    response.set_cookie('unitalent_session', token, httponly=True, samesite='lax', max_age=86400,
                        secure=os.getenv('COOKIE_SECURE', 'false').lower() == 'true', path='/')
    return public_user(user)


def profile_text(user, connection):
    p = json.loads(user['profile'])
    latest = connection.execute('SELECT r.text,a.data,a.confirmed FROM resumes r LEFT JOIN resume_analysis a ON a.resume_id=r.id WHERE r.user_id=? ORDER BY r.created_at DESC LIMIT 1', (user['id'],)).fetchone()
    resume_text = latest['text'] if latest else ''
    if latest and latest['confirmed'] and latest['data']:
        analysis = json.loads(latest['data'])
        resume_text = ' '.join([s['name'] for s in analysis['skills']])
        if analysis.get('experienceYears') is not None:
            resume_text += f' {analysis["experienceYears"]} years experience'
    return ' '.join([p.get('targetRole', ''), ' '.join(p.get('skills', [])), p.get('projectTitle', ''),
                     p.get('projectSummary', ''), resume_text])[:100000]


def job_data(job_id, connection):
    row = connection.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy tin tuyển dụng.')
    return row, json.loads(row['data'])


def candidate_data(user, application=None, job=None):
    p = json.loads(user['profile'])
    return dict(id=application['id'] if application else user['id'], name=user['name'], email=user['email'],
                avatarText=user['name'][:1], avatarUrl=avatar_url(user), university=p.get('university', ''), major=p.get('major', ''),
                year=p.get('year', ''), gpa=p.get('gpa', 0), targetRole=job['title'] if job else p.get('targetRole', ''),
                matchScore=application['score'] if application else 0,
                status=application['stage'] if application else 'submitted',
                appliedDate=application['created_at'] if application else now(),
                astAudit=dict(cleanCodeScore=0, solidCompliance=0, plagiarismPercentage=0,
                              cyclomaticComplexity='Chưa đánh giá', securityVulnerabilities=0, verifiedCommitCount=0),
                featuredProject=dict(title=p.get('projectTitle', ''), summary=p.get('projectSummary', ''),
                                     repo=p.get('projectRepo', ''), techStack=p.get('skills', []), score=0),
                voiceAiAssessment=dict(overallScore=0, technicalDepth=0, problemSolving=0, communication=0,
                                       feedbackSummary='Chưa có đánh giá giọng nói.', completedAt=''),
                skillsRadar=[dict(skill=s, candidateScore=0, marketBenchmark=0) for s in p.get('skills', [])],
                profile=p, interviewSchedule=json.loads(application['schedule']) if application and application['schedule'] else None)


@app.get('/api/health')
def health():
    with db() as c:
        c.execute('SELECT 1')
    try:
        ai = ai_request('/health')
    except HTTPException:
        ai = {'status': 'unavailable'}
    return {'status': 'ok' if ai['status'] == 'ok' else 'degraded', 'database': 'ok', 'ai': ai}


@app.post('/api/auth/register', status_code=201)
def register(body: Register, response: Response):
    user = dict(id=uid(), email=body.email, name=body.name.strip(), role=body.role)
    if len(user['name']) < 2:
        raise HTTPException(422, 'Tên cần ít nhất 2 ký tự.')
    try:
        with db() as c:
            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',
                      (user['id'], user['email'], user['name'], hash_password(body.password), body.role, '{}'))
            record_origin(c, 'user', user['id'], classify_origin({}, user['id'], user['email']))
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, 'Email đã được đăng ký.') from error
    return create_session(user, response)


@app.post('/api/auth/login')
def login(body: Login, response: Response):
    with db() as c:
        user = c.execute('SELECT * FROM users WHERE email=?', (body.email,)).fetchone()
    if not user or not verify_password(body.password, user['password_hash']):
        raise HTTPException(401, 'Email hoặc mật khẩu không đúng.')
    return create_session(dict(user), response)


@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return public_user(user)


@app.post('/api/auth/logout', status_code=204)
def logout(request: Request, response: Response):
    with db() as c:
        c.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(request.cookies.get('unitalent_session', '')),))
    response.delete_cookie('unitalent_session', path='/')


@app.get('/api/profile')
def profile(user=Depends(student_only)):
    return candidate_data(user)


@app.put('/api/profile')
def update_profile(body: Profile, user=Depends(student_only)):
    with db() as c:
        c.execute('UPDATE users SET profile=? WHERE id=?', (dump(body.model_dump()), user['id']))
        index_candidate_skills(c, user['id'], ' '.join([body.targetRole, *body.skills, body.projectTitle, body.projectSummary]))
    return body.model_dump()


@app.get('/api/jobs')
def jobs(user=Depends(current_user)):
    with db() as c:
        rows = c.execute('SELECT * FROM jobs ORDER BY rowid DESC').fetchall()
        data = [json.loads(row['data']) for row in rows]
        text = profile_text(user, c) if user['role'] == 'student' else ''
    if user['role'] == 'student' and data:
        # The AI service accepts at most 500 jobs per request. Imported sources
        # can exceed that limit; score every batch before globally sorting.
        matches = {}
        for start in range(0, len(data), 500):
            matches.update({m['id']: m for m in ai_request('/match', dict(profileText=text, jobs=data[start:start + 500]))})
        data = [dict(job, **{k: v for k, v in matches[job['id']].items() if k != 'id'}) for job in data]
        data.sort(key=lambda job: job['matchScore'], reverse=True)
    return data


@app.get('/api/jobs/search')
def search_jobs(q: str = '', category: str = 'all', page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), user=Depends(current_user)):
    term = q.strip().casefold()
    result = [j for j in jobs(user) if (category == 'all' or j.get('category') == category) and
              (not term or term in ' '.join([j['title'],j['company'],*j.get('tags',[])]).casefold())]
    return dict(items=result[(page-1)*pageSize:page*pageSize], total=len(result), page=page, pageSize=pageSize)


@app.get('/api/jobs/{job_id}')
def get_job(job_id: str, user=Depends(current_user)):
    with db() as c:
        _, job = job_data(job_id, c)
        text = profile_text(user, c)
    if user['role'] == 'student':
        result = ai_request('/match', dict(profileText=text, jobs=[job]))[0]
        job.update({k: v for k, v in result.items() if k != 'id'})
    return job


@app.post('/api/jobs', status_code=201)
def post_job(body: JobInput, user=Depends(recruiter_only)):
    job = dict(body.model_dump(), id=uid(), company=user['name'], logoText=user['name'][:3].upper(),
               postedAt=now(), matchScore=0, astCleanCodeScore=0, isDemo=False)
    with db() as c:
        c.execute('INSERT INTO jobs VALUES (?,?,?)', (job['id'], user['id'], dump(job)))
        record_origin(c, 'job', job['id'], classify_origin(job, job['id'], user['email']))
        index_job_skills(c, job['id'], job)
    return job


@app.delete('/api/jobs/{job_id}', status_code=204)
def remove_job(job_id: str, user=Depends(recruiter_only)):
    with db() as c:
        row, _ = job_data(job_id, c)
        if row['owner_id'] != user['id']:
            raise HTTPException(404, 'Không tìm thấy tin tuyển dụng.')
        delete_job(c, job_id)
    return Response(status_code=204)


@app.get('/api/resumes/current')
def current_resume(user=Depends(student_only)):
    with db() as c:
        row = c.execute('SELECT id,name,length(content) AS size FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
    if not row:
        return None
    with db() as c:
        extraction = c.execute('SELECT data,confirmed FROM resume_analysis WHERE resume_id=?', (row['id'],)).fetchone()
    return dict(row, analysis=dict(**json.loads(extraction['data']), confirmed=bool(extraction['confirmed'])) if extraction else None)


@app.post('/api/resumes', status_code=201)
def upload_resume(file: UploadFile, user=Depends(student_only)):
    content = file.file.read(MAX_RESUME_BYTES + 1)
    name = (file.filename or 'cv.pdf').replace('\\', '/').split('/')[-1][:200]
    text, warning = read_resume_pdf(content, name)
    identifier = uid()
    with db() as c:
        c.execute('INSERT INTO resumes VALUES (?,?,?,?,?,?)', (identifier, user['id'], name, content, text, now()))
        index_resume_extraction(c, identifier, text)
        index_candidate_skills(c, user['id'], text, 'resume')
        c.execute('INSERT INTO resume_analysis VALUES (?,?,?,?)', (identifier, dump(local_analysis(text)), 0, now()))
    return {'id': identifier, 'name': name, 'size': len(content), 'textExtracted': bool(text.strip()), 'warning': warning,
            'analysis': dict(local_analysis(text), confirmed=False)}


def owned_resume(resume_id, user):
    with db() as c:
        row = c.execute('SELECT * FROM resumes WHERE id=? AND user_id=?', (resume_id, user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy CV.')
    return row


@app.post('/api/resumes/{resume_id}/analyze')
def analyze_resume(resume_id: str, force: bool = False, user=Depends(student_only)):
    row = owned_resume(resume_id, user)
    with db() as c:
        existing = c.execute('SELECT data,confirmed FROM resume_analysis WHERE resume_id=?', (resume_id,)).fetchone()
    expected = 'gemini:' + os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite')
    if existing and not force and json.loads(existing['data']).get('method') == expected and json.loads(existing['data']).get('schemaVersion') == 1:
        return dict(id=resume_id, analysis=dict(**json.loads(existing['data']), confirmed=bool(existing['confirmed'])))
    text = row['text']
    partial = False
    if not text.strip():
        text, partial = ocr_pdf(row['content'])
        if not text.strip():
            raise HTTPException(422, 'CV đã lưu nhưng OCR không nhận được chữ. Hãy nhập kỹ năng thủ công hoặc chọn bản rõ hơn.')
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    if not force:
        with db() as c:
            prior = c.execute('SELECT a.data FROM resume_analysis a JOIN resumes r ON r.id=a.resume_id WHERE r.user_id=? AND a.confirmed=0 ORDER BY a.updated_at DESC', (user['id'],)).fetchall()
        for cached in prior:
            data = json.loads(cached['data'])
            if data.get('method') == expected and data.get('schemaVersion') == 1 and data.get('textHash') == text_hash:
                with db() as c:
                    c.execute('INSERT OR REPLACE INTO resume_analysis VALUES (?,?,?,?)', (resume_id,dump(data),0,now()))
                return dict(id=resume_id,analysis=dict(data,confirmed=False))
    result = verify_analysis(ai_request('/resume/analyze', dict(text=text)), text)
    result.update(ocrUsed=not bool(row['text'].strip()), ocrPartial=partial)
    with db() as c:
        c.execute('UPDATE resumes SET text=? WHERE id=?', (text, resume_id))
        c.execute('INSERT OR REPLACE INTO resume_analysis VALUES (?,?,?,?)', (resume_id, dump(result), 0, now()))
        index_resume_extraction(c, resume_id, text, 'gemini-evidence-v1')
    return dict(id=resume_id, analysis=dict(result, confirmed=False))


@app.patch('/api/resumes/{resume_id}/analysis')
def confirm_analysis(resume_id: str, body: AnalysisConfirmation, user=Depends(student_only)):
    row = owned_resume(resume_id, user)
    with db() as c:
        saved = c.execute('SELECT data FROM resume_analysis WHERE resume_id=?', (resume_id,)).fetchone()
        data = json.loads(saved['data']) if saved else local_analysis(row['text'])
        evidence = {s['name']: s.get('evidence', '') for s in data['skills']}
        data['skills'] = [dict(name=s, evidence=evidence.get(s, ''), source='user-confirmed') for s in canonical_skills(body.skills)]
        if data.get('experienceYears') != body.experienceYears:
            data['experienceEvidence'] = ''
        data['experienceYears'] = body.experienceYears
        data['experienceSource'] = 'user-confirmed'
        c.execute('INSERT OR REPLACE INTO resume_analysis VALUES (?,?,?,?)', (resume_id, dump(data), 1, now()))
        latest = c.execute('SELECT id FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
        if latest['id'] == resume_id:
            index_candidate_skills(c, user['id'], ' '.join(s['name'] for s in data['skills']), 'resume')
    return dict(id=resume_id, analysis=dict(data, confirmed=True))


def pdf_response(row):
    from urllib.parse import quote
    return StreamingResponse(io.BytesIO(row['content']), media_type='application/pdf',
                             headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(row['name'], safe='')}"})


@app.get('/api/resumes/{resume_id}/download')
def download_resume(resume_id: str, user=Depends(student_only)):
    with db() as c:
        row = c.execute('SELECT * FROM resumes WHERE id=? AND user_id=?', (resume_id, user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy CV.')
    return pdf_response(row)


@app.post('/api/applications', status_code=201)
def apply(body: ApplyInput, user=Depends(student_only)):
    with db() as c:
        _, job = job_data(body.jobId, c)
        resume = c.execute('SELECT id FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
        if not resume:
            raise HTTPException(422, 'Tải CV PDF lên trước khi nộp đơn.')
        text = profile_text(user, c)
        extraction = c.execute('SELECT data,confirmed FROM resume_analysis WHERE resume_id=?',(resume['id'],)).fetchone()
        frozen_analysis = dict(**json.loads(extraction['data']),confirmed=bool(extraction['confirmed'])) if extraction else {}
    prediction = ai_request('/match', dict(profileText=text, jobs=[job]))[0]
    score = prediction['matchScore']
    identifier, timestamp = uid(), now()
    try:
        with db() as c:
            c.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?)',
                      (identifier, body.jobId, user['id'], resume['id'], 'submitted', timestamp, timestamp, score, None))
            c.execute('INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
                      (identifier, 'submitted', timestamp))
            c.execute('INSERT INTO model_predictions VALUES (?,?,?,?,?,?,?,?)',
                      (uid(), user['id'], body.jobId, resume['id'], prediction.get('modelVersion', prediction.get('method', 'baseline-v1')),
                       score, prediction.get('explanation', ''), timestamp))
            c.execute('INSERT INTO prediction_snapshots VALUES (?,?,?)', (identifier, dump(prediction), dump(frozen_analysis)))
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, 'Bạn đã ứng tuyển vị trí này.') from error
    return {'id': identifier, 'stage': 'submitted'}


def application_rows(user):
    with db() as c:
        field = 'a.student_id' if user['role'] == 'student' else 'j.owner_id'
        rows = c.execute(f'''SELECT a.*, j.data AS job, u.name AS applicant_name, u.profile AS applicant_profile,
            r.name AS resume_name, length(r.content) AS size FROM applications a
            JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.student_id
            JOIN resumes r ON r.id=a.resume_id WHERE {field}=? ORDER BY a.created_at DESC''', (user['id'],)).fetchall()
    return [dict(id=r['id'], jobId=r['job_id'], jobTitle=json.loads(r['job'])['title'],
                 company=json.loads(r['job'])['company'], applicantName=r['applicant_name'], resumeName=r['resume_name'],
                 applicantAvatarUrl=json.loads(r['applicant_profile'] or '{}').get('avatarUrl', '/avatars/default-student.svg'),
                 size=r['size'], submittedAt=r['created_at'], updatedAt=r['updated_at'], stage=r['stage'],
                 matchScore=r['score'], note='Điểm phù hợp được tính tại thời điểm nộp hồ sơ.',
                 interviewSchedule=json.loads(r['schedule']) if r['schedule'] else None) for r in rows]


@app.get('/api/applications')
def applications(user=Depends(current_user)):
    return application_rows(user)


def authorized_application(application_id, user):
    with db() as c:
        row = c.execute('SELECT a.*, j.owner_id FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.id=?', (application_id,)).fetchone()
    if not row or (user['id'] != row['student_id'] and user['id'] != row['owner_id']):
        raise HTTPException(404, 'Không tìm thấy đơn ứng tuyển.')
    return row


@app.get('/api/applications/{application_id}/resume')
def application_resume(application_id: str, user=Depends(current_user)):
    application = authorized_application(application_id, user)
    with db() as c:
        row = c.execute('SELECT * FROM resumes WHERE id=?', (application['resume_id'],)).fetchone()
    return pdf_response(row)


@app.patch('/api/applications/{application_id}')
def update_application(application_id: str, body: StageInput, user=Depends(recruiter_only)):
    application = authorized_application(application_id, user)
    schedule = dump(body.interviewSchedule.model_dump()) if body.interviewSchedule else None
    with db() as c:
        c.execute('UPDATE applications SET stage=?, schedule=COALESCE(?,schedule), updated_at=? WHERE id=?',
                  (body.stage, schedule, now(), application_id))
        if application['stage'] != body.stage:
            c.execute('INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
                      (application_id, body.stage, now()))
    return {'id': application_id, **body.model_dump()}


@app.get('/api/candidates')
def candidates(user=Depends(recruiter_only)):
    result = []
    with db() as c:
        rows = c.execute('SELECT a.* FROM applications a JOIN jobs j ON j.id=a.job_id WHERE j.owner_id=? ORDER BY a.created_at DESC', (user['id'],)).fetchall()
        for row in rows:
            applicant = c.execute('SELECT * FROM users WHERE id=?', (row['student_id'],)).fetchone()
            _, job = job_data(row['job_id'], c)
            result.append(candidate_data(applicant, row, job))
    return result


@app.get('/api/candidates/search')
def search_candidates(q: str = '', role: str = 'all', stage: str = 'all', minMatch: int = Query(0, ge=0, le=100), sort: str = 'match', page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), user=Depends(recruiter_only)):
    roles = {'backend':['backend','java','go'], 'data':['data','analyst','bi'], 'frontend':['frontend','react'], 'devops':['devops','cloud','sre']}
    term = q.strip().casefold()
    result = [c for c in candidates(user) if (stage == 'all' or c['status'] == stage) and c['matchScore'] >= minMatch
              and (role == 'all' or any(k in c['targetRole'].casefold() for k in roles.get(role,[role])))
              and (not term or term in ' '.join([c['name'],c['university'],c['targetRole'],c['featuredProject']['title'],*c['featuredProject']['techStack']]).casefold())]
    result.sort(key=lambda c: c['appliedDate'] if sort == 'recent' else c['matchScore'], reverse=True)
    return dict(items=result[(page-1)*pageSize:page*pageSize],total=len(result),page=page,pageSize=pageSize)


@app.get('/api/candidates/{application_id}')
def candidate(application_id: str, user=Depends(recruiter_only)):
    row = authorized_application(application_id, user)
    with db() as c:
        applicant = c.execute('SELECT * FROM users WHERE id=?', (row['student_id'],)).fetchone()
        _, job = job_data(row['job_id'], c)
    return candidate_data(applicant, row, job)


def coaching_target(user, job_id=None):
    if job_id:
        return get_job(job_id, user)
    recommendations = jobs(user)
    job = next(iter(recommendations), None)
    if not job:
        raise HTTPException(404, 'Chưa có vị trí mục tiêu.')
    return job


def coaching_context(user, job):
    from services.ai.app.engine import extract_skills
    profile = json.loads(user['profile'])
    with db() as c:
        skills = extract_skills(profile_text(user, c))
    return dict(recognizedSkills=skills, targetRole=profile.get('targetRole', ''),
                projectTitle=profile.get('projectTitle', ''), projectSummary=profile.get('projectSummary', '')[:1500],
                job={k: job.get(k) for k in ('id', 'title', 'tags', 'requirements', 'description')})


def plan_fingerprint(context, hours):
    return hashlib.sha256(dump(dict(context=context, hoursPerWeek=hours)).encode()).hexdigest()


def plan_result(row):
    return dict(**json.loads(row['data']), planId=row['id'], completedTasks=json.loads(row['progress']))


@app.get('/api/skill-gap')
def skill_gap(jobId: str | None = None, hoursPerWeek: int = 6, user=Depends(student_only)):
    job = coaching_target(user, jobId)
    missing = job.get('missingSkills', [])
    fingerprint = plan_fingerprint(coaching_context(user, job), hoursPerWeek)
    with db() as c:
        saved = c.execute('SELECT * FROM learning_plans WHERE user_id=? AND job_id=? AND input_hash=?',
                          (user['id'], job['id'], fingerprint)).fetchone()
    if saved:
        result = plan_result(saved)
        result['currentScore'] = job['matchScore']
        return result
    return dict(targetJobTitle=job['title'], company=job['company'], currentScore=job['matchScore'],
                method='not-generated', planId=None, completedTasks={}, hoursPerWeek=hoursPerWeek,
                summary='Chọn số giờ học mỗi tuần và tạo lộ trình bằng Gemini.',
                gaps=[dict(skill=s, currentLevel='Chưa nhận diện trong hồ sơ', requiredLevel='Theo yêu cầu tin tuyển dụng',
                           importance='recommended', gapDescription='Bổ sung dự án hoặc minh chứng kỹ năng này.') for s in missing],
                roadmap=[])


@app.post('/api/skill-gap')
def generate_skill_gap(body: CoachingRequest, user=Depends(student_only)):
    job = coaching_target(user, body.jobId)
    context = coaching_context(user, job)
    fingerprint = plan_fingerprint(context, body.hoursPerWeek)
    with db() as c:
        existing = c.execute('SELECT * FROM learning_plans WHERE user_id=? AND job_id=? AND input_hash=?',
                             (user['id'], job['id'], fingerprint)).fetchone()
    if existing:
        return plan_result(existing)
    generated = ai_request('/roadmap', dict(context=context, missingSkills=job.get('missingSkills', []), hoursPerWeek=body.hoursPerWeek))
    from services.ai.app.coaching import Plan
    plan = Plan.model_validate(generated).model_dump()
    base = skill_gap(job['id'], body.hoursPerWeek, user)
    data = {k: v for k, v in base.items() if k not in ('planId', 'completedTasks')}
    data.update(plan, method=generated['method'])
    with db() as c:
        c.execute('INSERT OR IGNORE INTO learning_plans (id,user_id,job_id,input_hash,data,created_at) VALUES (?,?,?,?,?,?)',
                  (uid(), user['id'], job['id'], fingerprint, dump(data), now()))
        saved = c.execute('SELECT * FROM learning_plans WHERE user_id=? AND job_id=? AND input_hash=?',
                          (user['id'], job['id'], fingerprint)).fetchone()
    return plan_result(saved)


@app.patch('/api/skill-gap/{plan_id}/progress')
def save_plan_progress(plan_id: str, body: ProgressRequest, user=Depends(student_only)):
    with db() as c:
        row = c.execute('SELECT * FROM learning_plans WHERE id=? AND user_id=?', (plan_id, user['id'])).fetchone()
        if row is None:
            raise HTTPException(404, 'Không tìm thấy lộ trình.')
        data = json.loads(row['data'])
        allowed = {f'w{step["week"]}-{index}' for step in data['roadmap'] for index in range(len(step['milestones']))}
        if not set(body.completedTasks) <= allowed:
            raise HTTPException(422, 'Cột mốc không thuộc lộ trình này.')
        c.execute('UPDATE learning_plans SET progress=? WHERE id=?', (dump(body.completedTasks), plan_id))
    return {'completedTasks': body.completedTasks}


@app.get('/api/analytics')
def analytics(category: str | None = None, dataset: str | None = None, location: str | None = None,
              source: str | None = None, dateFrom: str | None = None, dateTo: str | None = None,
              funnelFrom: str | None = None, funnelTo: str | None = None,
              user=Depends(recruiter_only)):
    from .analytics import report
    dataset = dataset or os.getenv('ANALYTICS_DATASET', 'real')
    if dataset not in ('real', 'demo', 'test'):
        raise HTTPException(422, 'Nguồn dữ liệu không hợp lệ.')
    for date in (dateFrom, dateTo,funnelFrom,funnelTo):
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError as error:
                raise HTTPException(422, 'Ngày lọc cần có dạng YYYY-MM-DD.') from error
    if dateFrom and dateTo and dateFrom > dateTo:
        raise HTTPException(422, 'Ngày bắt đầu phải trước ngày kết thúc.')
    if funnelFrom and funnelTo and funnelFrom > funnelTo:
        raise HTTPException(422,'Ngày bắt đầu cohort phải trước ngày kết thúc.')
    with db() as c:
        result = report(c, user['id'], dataset, category=category, location=location,
                        source=source, date_from=dateFrom, date_to=dateTo,funnel_from=funnelFrom,funnel_to=funnelTo)
    result['biUrl'] = os.getenv('BI_PUBLIC_URL', 'http://127.0.0.1:3001')
    return result


@app.get('/api/analytics/export.csv')
def analytics_export(category: str | None = None, dataset: str | None = None, location: str | None = None,
                     source: str | None = None, dateFrom: str | None = None, dateTo: str | None = None,
                     funnelFrom: str | None = None, funnelTo: str | None = None,
                     user=Depends(recruiter_only)):
    result = analytics(category,dataset,location,source,dateFrom,dateTo,funnelFrom,funnelTo,user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['metric', 'category', 'value', 'sample_size', 'currency', 'period'])
    for skill in result['marketStats']:
        writer.writerow(['candidate_count', skill['skill'], skill['candidateCount'], result['totalStudents'], '', ''])
        writer.writerow(['job_demand', skill['skill'], skill['jobCount'], result['totalJobs'], '', ''])
    for salary in result['salaryTrends']:
        writer.writerow(['salary_median', salary['month'], salary['median'], salary['sampleSize'], salary['currency'], salary['period']])
    return StreamingResponse(iter([output.getvalue()]), media_type='text/csv; charset=utf-8',
                             headers={'Content-Disposition': 'attachment; filename="unitalent-analytics.csv"'})


@app.get('/api/analytics/warehouse')
def warehouse_status(user=Depends(recruiter_only)):
    host = os.getenv('WAREHOUSE_HOST')
    if not host:
        return {'status': 'not-configured', 'biUrl': os.getenv('BI_PUBLIC_URL', 'http://127.0.0.1:3001')}
    try:
        import psycopg
        with psycopg.connect(host=host, dbname='unitalent_analytics', user='bi_reader', password=os.getenv('BI_READER_PASSWORD','Local-BI-Reader-4829'), connect_timeout=3) as connection:
            row = connection.execute('SELECT refreshed_at,job_count,candidate_count FROM refresh_status WHERE id=1').fetchone()
        return dict(status='ok', refreshedAt=row[0].isoformat() if row else None,
                    jobCount=row[1] if row else 0, candidateCount=row[2] if row else 0,
                    biUrl=os.getenv('BI_PUBLIC_URL', 'http://127.0.0.1:3001'))
    except Exception:
        return {'status': 'unavailable', 'biUrl': os.getenv('BI_PUBLIC_URL', 'http://127.0.0.1:3001')}


@app.get('/api/interview/questions')
def interview_questions(user=Depends(student_only)):
    with db() as c:
        rows = c.execute('SELECT id,topic,question,method FROM coaching_questions WHERE user_id=? ORDER BY rowid', (user['id'],)).fetchall()
    return [dict(row) for row in rows] or [dict(q, topic=q['id'], method='question-bank') for q in ai_request('/interview/questions')]


@app.post('/api/interview/questions')
def create_interview_questions(body: CoachingRequest, user=Depends(student_only)):
    job = coaching_target(user, body.jobId)
    result = ai_request('/interview/questions', dict(context=coaching_context(user, job)))
    from services.ai.app.coaching import QuestionSet
    questions = QuestionSet.model_validate(result).questions
    with db() as c:
        c.execute('DELETE FROM coaching_questions WHERE user_id=?', (user['id'],))
        for q in questions:
            c.execute('INSERT INTO coaching_questions VALUES (?,?,?,?,?,?,?)',
                      (uid(), user['id'], q.topic, q.question, dump(q.keywords), result['method'], now()))
    return interview_questions(user)


@app.post('/api/interview/evaluate')
def interview_evaluate(body: Answer, user=Depends(student_only)):
    with db() as c:
        custom = c.execute('SELECT * FROM coaching_questions WHERE id=? AND user_id=?', (body.questionId, user['id'])).fetchone()
    payload = body.model_dump()
    if custom:
        payload.update(question=custom['question'], keywords=json.loads(custom['keywords']))
    elif body.questionId not in ('api', 'database', 'project'):
        raise HTTPException(404, 'Không tìm thấy câu hỏi trong tài khoản của bạn.')
    result = ai_request('/interview/evaluate', payload)
    result['question'] = custom['question'] if custom else body.questionId
    with db() as c:
        c.execute('INSERT INTO interviews VALUES (?,?,?,?,?,?)', (uid(), user['id'], body.questionId, body.answer, dump(result), now()))
    return result


@app.get('/api/interview/history')
def interview_history(user=Depends(student_only)):
    with db() as c:
        return [dict(id=r['id'], questionId=r['question_id'], answer=r['answer'], result=json.loads(r['result']), createdAt=r['created_at'])
                for r in c.execute('SELECT * FROM interviews WHERE student_id=? ORDER BY created_at DESC LIMIT 50', (user['id'],))]
