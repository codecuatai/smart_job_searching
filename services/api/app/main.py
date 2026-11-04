import io
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from .db import db, dump, init_db
from services.config import allowed_origins
from .security import current_user, hash_password, require_role, token_hash, verify_password
from .schemas import Answer, ApplyInput, JobInput, Login, Profile, Register, StageInput
from .seed import seed_demo
from .ai_client import ai_request

student_only = require_role('student')
recruiter_only = require_role('recruiter')


@asynccontextmanager
async def lifespan(_app):
    init_db()
    seed_demo()
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
    text = str(value or '').strip().lower()
    has_million_unit = any(unit in text for unit in ('triệu', 'tr'))
    tokens = re.findall(r'\d+(?:[.,]\d+)*', text)
    if not tokens:
        return None
    numbers = []
    for token in tokens[:2]:
        if has_million_unit:
            numbers.append(float(token.replace(',', '.')) * 1_000_000)
        else:
            numbers.append(float(token.replace('.', '').replace(',', '')))
    if not has_million_unit and numbers and max(numbers) < 1000:
        numbers = [number * 1_000_000 for number in numbers]
    return (min(numbers), max(numbers))


def public_user(user):
    return {k: user[k] for k in ('id', 'email', 'name', 'role')}


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
    latest = connection.execute('SELECT text FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
    return ' '.join([p.get('targetRole', ''), ' '.join(p.get('skills', [])), p.get('projectTitle', ''),
                     p.get('projectSummary', ''), latest['text'] if latest else ''])[:100000]


def job_data(job_id, connection):
    row = connection.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy tin tuyển dụng.')
    return row, json.loads(row['data'])


def candidate_data(user, application=None, job=None):
    p = json.loads(user['profile'])
    return dict(id=application['id'] if application else user['id'], name=user['name'], email=user['email'],
                avatarText=user['name'][:1], university=p.get('university', ''), major=p.get('major', ''),
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
    return body.model_dump()


@app.get('/api/jobs')
def jobs(user=Depends(current_user)):
    with db() as c:
        rows = c.execute('SELECT * FROM jobs ORDER BY rowid DESC').fetchall()
        data = [json.loads(row['data']) for row in rows]
        text = profile_text(user, c) if user['role'] == 'student' else ''
    if user['role'] == 'student' and data:
        matches = {m['id']: m for m in ai_request('/match', dict(profileText=text, jobs=data))}
        data = [dict(job, **{k: v for k, v in matches[job['id']].items() if k != 'id'}) for job in data]
        data.sort(key=lambda job: job['matchScore'], reverse=True)
    return data


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
    return job


@app.get('/api/resumes/current')
def current_resume(user=Depends(student_only)):
    with db() as c:
        row = c.execute('SELECT id,name,length(content) AS size FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
    return dict(row) if row else None


@app.post('/api/resumes', status_code=201)
def upload_resume(file: UploadFile, user=Depends(student_only)):
    content = file.file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, 'CV tối đa 5 MB.')
    name = (file.filename or 'cv.pdf').replace('\\', '/').split('/')[-1][:200]
    if not name.lower().endswith('.pdf') or not content.startswith(b'%PDF-'):
        raise HTTPException(422, 'Vui lòng chọn tệp PDF hợp lệ.')
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted or len(reader.pages) > 30:
            raise ValueError('Encrypted or too many pages')
        text = '\n'.join((page.extract_text() or '')[:10000] for page in reader.pages)[:60000]
    except Exception as error:
        raise HTTPException(422, 'Không đọc được PDF. Dùng PDF không khóa, tối đa 30 trang.') from error
    identifier = uid()
    with db() as c:
        c.execute('INSERT INTO resumes VALUES (?,?,?,?,?,?)', (identifier, user['id'], name, content, text, now()))
    return {'id': identifier, 'name': name, 'size': len(content), 'textExtracted': bool(text.strip())}


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
    score = ai_request('/match', dict(profileText=text, jobs=[job]))[0]['matchScore']
    identifier, timestamp = uid(), now()
    try:
        with db() as c:
            c.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?,?)',
                      (identifier, body.jobId, user['id'], resume['id'], 'submitted', timestamp, timestamp, score, None))
            c.execute('INSERT INTO application_stage_events (application_id,stage,created_at) VALUES (?,?,?)',
                      (identifier, 'submitted', timestamp))
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, 'Bạn đã ứng tuyển vị trí này.') from error
    return {'id': identifier, 'stage': 'submitted'}


def application_rows(user):
    with db() as c:
        field = 'a.student_id' if user['role'] == 'student' else 'j.owner_id'
        rows = c.execute(f'''SELECT a.*, j.data AS job, u.name AS applicant_name,
            r.name AS resume_name, length(r.content) AS size FROM applications a
            JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.student_id
            JOIN resumes r ON r.id=a.resume_id WHERE {field}=? ORDER BY a.created_at DESC''', (user['id'],)).fetchall()
    return [dict(id=r['id'], jobId=r['job_id'], jobTitle=json.loads(r['job'])['title'],
                 company=json.loads(r['job'])['company'], applicantName=r['applicant_name'], resumeName=r['resume_name'],
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


@app.get('/api/candidates/{application_id}')
def candidate(application_id: str, user=Depends(recruiter_only)):
    row = authorized_application(application_id, user)
    with db() as c:
        applicant = c.execute('SELECT * FROM users WHERE id=?', (row['student_id'],)).fetchone()
        _, job = job_data(row['job_id'], c)
    return candidate_data(applicant, row, job)


@app.get('/api/skill-gap')
def skill_gap(jobId: str | None = None, user=Depends(student_only)):
    recommendations = jobs(user)
    job = next((j for j in recommendations if j['id'] == jobId), None) if jobId else next(iter(recommendations), None)
    if not job:
        raise HTTPException(404, 'Chưa có vị trí mục tiêu.')
    missing = job.get('missingSkills', [])
    return dict(targetJobTitle=job['title'], company=job['company'], currentScore=job['matchScore'],
                projectedScore=100, explanation=job.get('explanation'),
                gaps=[dict(skill=s, currentLevel='Chưa nhận diện trong hồ sơ', requiredLevel='Theo yêu cầu tin tuyển dụng',
                           importance='recommended', gapDescription='Bổ sung dự án hoặc minh chứng kỹ năng này.') for s in missing],
                roadmap=[dict(week=i+1, timeRange=f'Chặng {i+1}', focusTitle=s,
                              milestones=[f'Ôn tập nền tảng {s}', f'Xây dựng ví dụ {s} có kiểm thử', 'Cập nhật minh chứng vào hồ sơ'],
                              curatedResource=f'Tài liệu chính thức {s}') for i, s in enumerate(missing)])


@app.get('/api/analytics')
def analytics(user=Depends(recruiter_only)):
    from collections import Counter, defaultdict
    with db() as c:
        all_jobs = [json.loads(r['data']) for r in c.execute('SELECT data FROM jobs')]
        profiles = [json.loads(r['profile']) for r in c.execute("SELECT profile FROM users WHERE role='student'")]
        applications = c.execute('''SELECT COUNT(*) AS total FROM applications a
            JOIN jobs j ON j.id=a.job_id WHERE j.owner_id=?''', (user['id'],)).fetchone()['total']
        reached = {row['stage']: row['count'] for row in c.execute('''SELECT e.stage, COUNT(DISTINCT e.application_id) AS count
            FROM application_stage_events e JOIN applications a ON a.id=e.application_id
            JOIN jobs j ON j.id=a.job_id WHERE j.owner_id=? GROUP BY e.stage''', (user['id'],))}
    categories = Counter(j['category'] for j in all_jobs)
    demand = Counter(s for j in all_jobs for s in set(j.get('tags', [])))
    supply = Counter(s for p in profiles for s in set(p.get('skills', [])))
    market = []
    for skill, count in demand.most_common(10):
        d = round(100 * count / len(all_jobs))
        s = round(100 * supply[skill] / len(profiles)) if profiles else 0
        market.append(dict(skill=skill, demandPercentage=d, supplyPercentage=s, shortagePercentage=max(0, d-s)))
    salaries = defaultdict(lambda: [0, 0])
    salary_counts = Counter()
    for job in all_jobs:
        bounds = salary_range(job.get('salary'))
        if bounds:
            salaries[job['category']][0] += bounds[0]
            salaries[job['category']][1] += bounds[1]
            salary_counts[job['category']] += 1
    salary_stats = [dict(category=category, sampleSize=salary_counts[category],
                         averageMinimumVnd=round(salaries[category][0] / salary_counts[category]),
                         averageMaximumVnd=round(salaries[category][1] / salary_counts[category]))
                    for category in sorted(salary_counts)]
    funnel = []
    previous_count = applications
    for stage, label in [('submitted', 'Đã nộp'), ('reviewing', 'Đang xem xét'),
                         ('interview', 'Phỏng vấn'), ('offered', 'Đề nghị')]:
        count = applications if stage == 'submitted' else reached.get(stage, 0)
        funnel.append(dict(stage=stage, label=label, count=count,
                           reachedPercentage=round(count / applications * 100) if applications else 0,
                           conversionFromPreviousPercentage=round(count / previous_count * 100) if previous_count else 0))
        previous_count = count
    return dict(totalJobs=len(all_jobs), totalStudents=len(profiles), updatedAt=now(), marketStats=market,
                categoryDistribution=[dict(category=k, jobCount=v, percentage=round(v/len(all_jobs)*100)) for k, v in categories.items()],
                salaryStats=salary_stats, hiringFunnel=funnel, totalApplications=applications,
                scope='Dữ liệu trong ứng dụng; kỹ năng thống kê theo nhãn chính xác, không đại diện thị trường lao động.')


@app.get('/api/interview/questions')
def interview_questions(user=Depends(student_only)):
    return ai_request('/interview/questions')


@app.post('/api/interview/evaluate')
def interview_evaluate(body: Answer, user=Depends(student_only)):
    result = ai_request('/interview/evaluate', body.model_dump())
    with db() as c:
        c.execute('INSERT INTO interviews VALUES (?,?,?,?,?,?)', (uid(), user['id'], body.questionId, body.answer, dump(result), now()))
    return result


@app.get('/api/interview/history')
def interview_history(user=Depends(student_only)):
    with db() as c:
        return [dict(id=r['id'], questionId=r['question_id'], answer=r['answer'], result=json.loads(r['result']), createdAt=r['created_at'])
                for r in c.execute('SELECT * FROM interviews WHERE student_id=? ORDER BY created_at DESC LIMIT 50', (user['id'],))]
