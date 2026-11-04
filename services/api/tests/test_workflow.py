import io
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from services.ai.app.main import app as ai_app
from services.api.app import main


@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'test.db'))
    monkeypatch.setenv('SEED_DEMO', 'false')
    # Exercise real AI routes while isolating transport/network in API unit tests.
    with TestClient(ai_app) as ai:
        def request(path, body=None):
            response = ai.get(path) if body is None else ai.post(path, json=body)
            response.raise_for_status()
            return response.json()
        monkeypatch.setattr(main, 'ai_request', request)
        with TestClient(main.app) as student, TestClient(main.app) as recruiter, TestClient(main.app) as outsider:
            yield student, recruiter, outsider


def register(client, email, role='student'):
    response = client.post('/api/auth/register', json=dict(name='Test User', email=email, password='test12345', role=role))
    assert response.status_code == 201, response.text
    return response.json()


def new_job(client):
    response = client.post('/api/jobs', json=dict(title='Python Engineer', location='HCM', category='backend',
                           description='Build a Python API with SQL.', tags=['Python', 'SQL', 'Docker'], requirements=['Python', 'SQL']))
    assert response.status_code == 201, response.text
    return response.json()


def pdf():
    stream = io.BytesIO()
    writer = PdfWriter(); writer.add_blank_page(width=100, height=100); writer.write(stream)
    return stream.getvalue()


def test_real_application_lifecycle_access_and_resume_snapshot(clients):
    student, recruiter, outsider = clients
    register(student, 'student@example.test')
    register(recruiter, 'recruiter@example.test', 'recruiter')
    register(outsider, 'outsider@example.test', 'recruiter')
    job = new_job(recruiter)
    assert student.post('/api/jobs', json={}).status_code in (403, 422)
    assert recruiter.get('/api/profile').status_code == 403
    assert student.post('/api/applications', json={'jobId': job['id']}).status_code == 422
    assert student.put('/api/profile', json={'skills': ['Python', 'SQL']}).status_code == 200
    jobs = student.get('/api/jobs').json()
    assert jobs[0]['matchScore'] > 0 and 'Docker' in jobs[0]['missingSkills']
    original = pdf()
    assert student.post('/api/resumes', files={'file': ('cv.pdf', original, 'application/pdf')}).status_code == 201
    submitted = student.post('/api/applications', json={'jobId': job['id']})
    assert submitted.status_code == 201, submitted.text
    identifier = submitted.json()['id']
    assert student.post('/api/applications', json={'jobId': job['id']}).status_code == 409
    # A later upload must not replace the CV attached to a previous application.
    assert student.post('/api/resumes', files={'file': ('new.pdf', pdf(), 'application/pdf')}).status_code == 201
    assert recruiter.get(f'/api/applications/{identifier}/resume').content == original
    assert outsider.get('/api/candidates').json() == []
    assert outsider.get(f'/api/candidates/{identifier}').status_code == 404
    assert outsider.get(f'/api/applications/{identifier}/resume').status_code == 404
    assert outsider.patch(f'/api/applications/{identifier}', json={'stage': 'offered'}).status_code == 404
    schedule = dict(date='2026-11-01', time='09:30', format='Office', interviewer='Tech Lead')
    assert recruiter.patch(f'/api/applications/{identifier}', json={'stage': 'interview'}).status_code == 422
    assert recruiter.patch(f'/api/applications/{identifier}', json={'stage': 'interview', 'interviewSchedule': dict(schedule, date='2026-99-99')}).status_code == 422
    changed = recruiter.patch(f'/api/applications/{identifier}', json={'stage': 'interview', 'interviewSchedule': schedule})
    assert changed.status_code == 200
    tracked = student.get('/api/applications').json()[0]
    assert tracked['stage'] == 'interview' and tracked['interviewSchedule'] == schedule
    assert recruiter.get('/api/candidates').json()[0]['id'] == identifier
    assert recruiter.get('/api/analytics').json()['totalJobs'] == 1


def test_auth_validation_upload_limits_and_logout(clients):
    student, recruiter, _ = clients
    assert student.get('/api/jobs').status_code == 401
    register(student, 'auth@example.test')
    assert recruiter.post('/api/auth/register', json=dict(name='Other', email='auth@example.test', password='test12345', role='student')).status_code == 409
    assert recruiter.post('/api/auth/login', json=dict(email='auth@example.test', password='wrongpass')).status_code == 401
    assert student.post('/api/resumes', files={'file': ('fake.pdf', b'not a PDF')}).status_code == 422
    assert student.post('/api/resumes', files={'file': ('big.pdf', b'%PDF-' + b'0' * (5 * 1024 * 1024))}).status_code == 413
    assert student.post('/api/auth/logout', headers={'origin': 'https://evil.test'}).status_code == 403
    assert student.post('/api/auth/logout').status_code == 204
    assert student.get('/api/auth/me').status_code == 401
    login = student.post('/api/auth/login', json=dict(email='auth@example.test', password='test12345'))
    assert login.status_code == 200
    assert 'HttpOnly' in login.headers['set-cookie']
    assert student.put('/api/profile', json={'projectRepo': 'javascript:alert(1)'}).status_code == 422


def test_interview_history_and_missing_resources(clients):
    student, recruiter, _ = clients
    register(student, 'interview@example.test')
    register(recruiter, 'hr@example.test', 'recruiter')
    assert student.get('/api/jobs/missing').status_code == 404
    assert student.get('/api/skill-gap').status_code == 404
    questions = student.get('/api/interview/questions').json()
    assert len(questions) == 3
    result = student.post('/api/interview/evaluate', json={'questionId': 'api', 'answer': 'Use idempotency with unique transaction and test retry.'})
    assert result.status_code == 200
    assert student.get('/api/interview/history').json()[0]['result'] == result.json()
    assert recruiter.get('/api/interview/history').status_code == 403
    assert recruiter.get('/api/analytics').json()['marketStats'] == []


def test_health_reports_ai_outage(clients, monkeypatch):
    from fastapi import HTTPException
    student, _, _ = clients
    def unavailable(*_args, **_kwargs):
        raise HTTPException(503, 'AI unavailable')
    monkeypatch.setattr(main, 'ai_request', unavailable)
    assert student.get('/api/health').json()['status'] == 'degraded'
