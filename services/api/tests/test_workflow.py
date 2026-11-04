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
    monkeypatch.setenv('GEMINI_ENABLED', 'false')
    monkeypatch.setenv('ANALYTICS_DATASET', 'test')
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


def test_ai_learning_plan_cache_progress_and_ownership(clients, monkeypatch):
    student, recruiter, other = clients
    register(student, 'learner@example.test')
    register(recruiter, 'learning-hr@example.test', 'recruiter')
    register(other, 'other-learner@example.test')
    job = new_job(recruiter)
    original_request = main.ai_request
    generated = []
    def request(path, body=None):
        if path == '/roadmap':
            generated.append(body)
            return dict(summary='Học Docker qua triển khai dự án API có kiểm thử.',
                        method='gemini:test-model', roadmap=[dict(week=1, timeRange='Tuần 1', focusTitle='Docker',
                        milestones=['Viết Dockerfile và kiểm thử API trong container'], curatedResource='Docker documentation')])
        return original_request(path, body)
    monkeypatch.setattr(main, 'ai_request', request)
    initial = student.get('/api/skill-gap', params={'jobId': job['id']}).json()
    assert initial['method'] == 'not-generated' and initial['roadmap'] == []
    assert 'projectedScore' not in initial
    payload = dict(jobId=job['id'], hoursPerWeek=6)
    response = student.post('/api/skill-gap', json=payload)
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan['method'] == 'gemini:test-model' and plan['roadmap'][0]['focusTitle'] == 'Docker'
    assert generated[0]['hoursPerWeek'] == 6
    assert 'email' not in generated[0]['context'] and 'name' not in generated[0]['context']
    progress_url = f'/api/skill-gap/{plan["planId"]}/progress'
    assert other.patch(progress_url, json={'completedTasks': {'w1-0': True}}).status_code == 404
    assert student.patch(progress_url, json={'completedTasks': {'w99-0': True}}).status_code == 422
    assert student.patch(progress_url, json={'completedTasks': {'w1-0': True}}).status_code == 200
    restored = student.get('/api/skill-gap', params={'jobId': job['id']}).json()
    assert restored['completedTasks'] == {'w1-0': True}
    assert student.post('/api/skill-gap', json=payload).json()['planId'] == plan['planId']
    assert len(generated) == 1
    assert student.post('/api/skill-gap', json=dict(payload, hoursPerWeek=10)).json()['planId'] != plan['planId']
    assert student.put('/api/profile', json={'skills': ['Python']}).status_code == 200
    changed = student.get('/api/skill-gap', params={'jobId': job['id']}).json()
    assert changed['planId'] is None
    assert recruiter.post('/api/skill-gap', json=payload).status_code == 403


def test_ai_generated_interview_questions_and_evaluation_scope(clients, monkeypatch):
    from services.ai.app import main as ai_main
    student, recruiter, other = clients
    register(student, 'practice@example.test')
    register(recruiter, 'practice-hr@example.test', 'recruiter')
    register(other, 'practice-other@example.test')
    job = new_job(recruiter)
    original_request = main.ai_request
    def request(path, body=None):
        if path == '/interview/questions' and body is not None:
            return dict(method='gemini:test-model', questions=[dict(topic=topic, question=f'Explain {topic} for this Python project and test it.', keywords=['Python']) for topic in ('api', 'database', 'project')])
        return original_request(path, body)
    monkeypatch.setattr(main, 'ai_request', request)
    evaluated = []
    def evaluate(question, answer, keywords):
        evaluated.append(question)
        return dict(score=80, feedback='Add a measurable test.', matchedConcepts=['Python'], suggestedConcepts=['metrics'], method='gemini:test-model')
    monkeypatch.setattr(ai_main, 'gemini_evaluate_interview', evaluate)
    response = student.post('/api/interview/questions', json={'jobId': job['id']})
    assert response.status_code == 200, response.text
    questions = response.json()
    assert len(questions) == 3 and all(q['method'] == 'gemini:test-model' for q in questions)
    assert student.get('/api/interview/questions').json() == questions
    question = questions[0]
    answer = dict(questionId=question['id'], answer='Python project with tests')
    assert other.post('/api/interview/evaluate', json=answer).status_code == 404
    response = student.post('/api/interview/evaluate', json=answer)
    assert response.status_code == 200, response.text
    assert evaluated == [question['question']]
    assert response.json()['question'] == question['question']
    assert student.get('/api/interview/history').json()[0]['result'] == response.json()


def test_coaching_outage_is_not_reported_as_ai_success(clients, monkeypatch):
    from fastapi import HTTPException
    student, recruiter, _ = clients
    register(student, 'outage-learner@example.test')
    register(recruiter, 'outage-hr@example.test', 'recruiter')
    job = new_job(recruiter)
    original_request = main.ai_request
    def request(path, body=None):
        if path == '/roadmap' or (path == '/interview/questions' and body):
            raise HTTPException(503, 'Gemini unavailable')
        return original_request(path, body)
    monkeypatch.setattr(main, 'ai_request', request)
    for endpoint in ['/api/skill-gap', '/api/interview/questions']:
        assert student.post(endpoint, json={'jobId': job['id']}).status_code == 503
    assert student.get('/api/skill-gap', params={'jobId': job['id']}).json()['planId'] is None


def new_job(client):
    response = client.post('/api/jobs', json=dict(title='Python Engineer', location='HCM', category='backend',
                           salary='15.000.000 - 20.000.000 VNĐ', description='Build a Python API with SQL.',
                           tags=['Python', 'SQL', 'Docker'], requirements=['Python', 'SQL']))
    assert response.status_code == 201, response.text
    return response.json()


def pdf():
    stream = io.BytesIO()
    writer = PdfWriter(); writer.add_blank_page(width=100, height=100); writer.write(stream)
    return stream.getvalue()


def test_pdf_export_variants_and_password_errors(clients):
    student, _, _ = clients
    register(student, 'pdf-variants@example.test')
    prefixed = b'\xef\xbb\xbf\r\n' + pdf()
    uploaded = student.post('/api/resumes', files={'file': ('export.PDF', prefixed, 'application/pdf')})
    assert uploaded.status_code == 201, uploaded.text
    original_id = uploaded.json()['id']
    assert student.get(f'/api/resumes/{original_id}/download').content == prefixed

    for password, expected in [('', 201), ('secret-opening-password', 422)]:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt(user_password=password, owner_password='owner-password')
        output = io.BytesIO()
        writer.write(output)
        response = student.post('/api/resumes', files={'file': ('restricted.pdf', output.getvalue(), 'application/pdf')})
        assert response.status_code == expected, response.text
        if expected == 422:
            assert 'mật khẩu' in response.json()['detail']
        else:
            original_id = response.json()['id']
    assert student.get('/api/resumes/current').json()['id'] == original_id


def test_pdf_page_limit_has_specific_error(clients):
    student, _, _ = clients
    register(student, 'pdf-pages@example.test')
    writer = PdfWriter()
    for _ in range(31):
        writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    response = student.post('/api/resumes', files={'file': ('pages.pdf', output.getvalue(), 'application/pdf')})
    assert response.status_code == 422
    assert '31 trang' in response.json()['detail']
    assert student.get('/api/resumes/current').json() is None


def test_text_extraction_error_still_saves_readable_pdf(clients, monkeypatch):
    from pypdf._page import PageObject
    student, _, _ = clients
    register(student, 'pdf-fonts@example.test')
    def broken_font(*args, **kwargs):
        raise ValueError('Unsupported font mapping')
    monkeypatch.setattr(PageObject, 'extract_text', broken_font)
    content = pdf()
    response = student.post('/api/resumes', files={'file': ('fonts.pdf', content, 'application/pdf')})
    assert response.status_code == 201, response.text
    assert response.json()['textExtracted'] is False
    assert 'chưa đọc được toàn bộ' in response.json()['warning']
    identifier = response.json()['id']
    assert student.get(f'/api/resumes/{identifier}/download').content == content


def test_corrupt_and_empty_pdf_do_not_replace_saved_cv(clients):
    student, _, _ = clients
    register(student, 'pdf-invalid@example.test')
    original = student.post('/api/resumes', files={'file': ('good.pdf', pdf(), 'application/pdf')}).json()
    for content, detail in [(b'', 'rỗng'), (b'%PDF-1.4\nnot a document', 'cấu trúc')]:
        response = student.post('/api/resumes', files={'file': ('invalid.pdf', content, 'application/pdf')})
        assert response.status_code == 422
        assert detail in response.json()['detail']
        assert student.get('/api/resumes/current').json()['id'] == original['id']


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
    assert recruiter.patch(f'/api/applications/{identifier}', json={'stage': 'reviewing'}).status_code == 200
    changed = recruiter.patch(f'/api/applications/{identifier}', json={'stage': 'interview', 'interviewSchedule': schedule})
    assert changed.status_code == 200
    tracked = student.get('/api/applications').json()[0]
    assert tracked['stage'] == 'interview' and tracked['interviewSchedule'] == schedule
    assert recruiter.get('/api/candidates').json()[0]['id'] == identifier
    analytics = recruiter.get('/api/analytics').json()
    assert analytics['totalJobs'] == 1
    assert analytics['salaryStats'] == [dict(category='backend', sampleSize=1, averageMinimumVnd=15_000_000, averageMaximumVnd=20_000_000)]
    funnel = {item['stage']: item for item in analytics['hiringFunnel']}
    assert funnel['submitted']['count'] == 1
    assert funnel['reviewing']['count'] == 1 and funnel['reviewing']['conversionFromPreviousPercentage'] == 100
    assert funnel['interview']['count'] == 1 and funnel['interview']['reachedPercentage'] == 100
    assert analytics['totalApplications'] == 1


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


def test_delete_job_requires_owner_and_cleans_linked_test_application(clients):
    student, recruiter, outsider = clients
    register(student, 'delete-student@example.test')
    register(recruiter, 'delete-owner@example.test', 'recruiter')
    register(outsider, 'delete-outsider@example.test', 'recruiter')
    job = new_job(recruiter)
    other_job = new_job(outsider)
    assert student.post('/api/resumes', files={'file': ('cv.pdf', pdf(), 'application/pdf')}).status_code == 201
    application = student.post('/api/applications', json={'jobId': job['id']})
    assert application.status_code == 201
    assert student.delete(f'/api/jobs/{job["id"]}').status_code == 403
    assert outsider.delete(f'/api/jobs/{job["id"]}').status_code == 404
    assert recruiter.delete(f'/api/jobs/{job["id"]}').status_code == 204
    assert student.get(f'/api/jobs/{job["id"]}').status_code == 404
    assert student.get('/api/applications').json() == []
    assert student.get('/api/resumes/current').json() is not None
    assert student.get(f'/api/jobs/{other_job["id"]}').status_code == 200


def test_job_list_scores_more_than_500_jobs_without_losing_or_misranking_them(clients, monkeypatch):
    from services.api.app.db import db, dump

    student, recruiter, _ = clients
    register(student, 'batch-student@example.test')
    owner = register(recruiter, 'batch-owner@example.test', 'recruiter')
    with db() as connection:
        for index in range(501):
            job = dict(id=f'batch-{index}', title=f'Position {index}', matchScore=0)
            connection.execute('INSERT INTO jobs VALUES (?,?,?)', (job['id'], owner['id'], dump(job)))
    sizes = []

    def score(path, body):
        assert path == '/match'
        sizes.append(len(body['jobs']))
        assert len(body['jobs']) <= 500
        return [dict(id=job['id'], matchScore=100 if job['id'] == 'batch-0' else 1) for job in body['jobs']]

    monkeypatch.setattr(main, 'ai_request', score)
    response = student.get('/api/jobs')
    assert response.status_code == 200
    rows = response.json()
    assert sizes == [500, 1]
    assert len(rows) == 501 and len({row['id'] for row in rows}) == 501
    assert rows[0]['id'] == 'batch-0'


def test_cv_analysis_evidence_confirmation_cache_and_snapshot(clients, monkeypatch):
    from services.api.app.db import db
    student, recruiter, other = clients
    register(student, 'extraction@example.test')
    register(recruiter, 'extraction-hr@example.test', 'recruiter')
    register(other, 'extraction-other@example.test')
    job = new_job(recruiter)
    uploaded = student.post('/api/resumes', files={'file': ('cv.pdf',pdf(),'application/pdf')}).json()
    resume_id = uploaded['id']
    calls = []
    original = main.ai_request
    def request(path, body=None):
        if path == '/resume/analyze':
            calls.append(body)
            return dict(method='gemini:gemini-3.5-flash-lite',skills=[dict(name='Python',evidence='Python'),dict(name='Docker',evidence='imaginary Docker project')],experienceYears=9,experienceEvidence='invented',projects=[],education=[],unknown=[])
        return original(path,body)
    monkeypatch.setattr(main,'ai_request',request)
    monkeypatch.setattr(main,'ocr_pdf',lambda content: ('Python SQL Docker',False))
    route=f'/api/resumes/{resume_id}/analyze'
    assert other.post(route).status_code == 404
    assert recruiter.post(route).status_code == 403
    result=student.post(route)
    assert result.status_code == 200,result.text
    analysis=result.json()['analysis']
    assert analysis['skills'] == [dict(name='Python',evidence='Python')]
    assert analysis['experienceYears'] is None
    assert student.post(route).status_code == 200 and len(calls) == 1
    assert student.patch(f'/api/resumes/{resume_id}/analysis',json=dict(skills=['Python'],experienceYears=2)).status_code == 200
    before=student.get(f'/api/jobs/{job["id"]}').json()
    assert before['matchedSkills'] == ['Python']
    assert student.post('/api/applications',json=dict(jobId=job['id'])).status_code == 201
    assert recruiter.get('/api/analytics?funnelFrom=2999-01-01').json()['totalApplications'] == 0
    assert recruiter.get('/api/analytics?funnelFrom=2026-12-31&funnelTo=2026-01-01').status_code == 422
    with db() as c:
        snapshot=c.execute('SELECT * FROM prediction_snapshots').fetchone()
        original_snapshot=snapshot['prediction'],snapshot['resume_analysis']
    student.patch(f'/api/resumes/{resume_id}/analysis',json=dict(skills=['SQL','Docker'],experienceYears=None))
    assert 'Python' not in student.get(f'/api/jobs/{job["id"]}').json()['matchedSkills']
    with db() as c:
        snapshot=c.execute('SELECT * FROM prediction_snapshots').fetchone()
        assert (snapshot['prediction'],snapshot['resume_analysis']) == original_snapshot
        assert c.execute("SELECT COUNT(*) FROM candidate_skills WHERE source='resume' AND skill_name='Python'").fetchone()[0] == 0


def test_real_bi_excludes_test_and_pagination_validates(clients):
    student,recruiter,other=clients
    register(student,'supply@example.test')
    register(recruiter,'supply-hr@example.test','recruiter')
    register(other,'real.person@university.edu')
    student.put('/api/profile',json={'skills':['postgres','PostgreSQL']})
    other.put('/api/profile',json={'skills':['postgres','PostgreSQL']})
    for _ in range(3): new_job(recruiter)
    test_report=recruiter.get('/api/analytics?dataset=test').json()
    real_report=recruiter.get('/api/analytics?dataset=real').json()
    assert next(s for s in real_report['marketStats'] if s['skill']=='PostgreSQL')['candidateCount'] == 1
    assert len(test_report['salaryStats']) == 1 and real_report['salaryStats'] == []
    first=student.get('/api/jobs/search?pageSize=2').json()
    second=student.get('/api/jobs/search?pageSize=2&page=2').json()
    assert first['total'] == 3 and len(first['items']) == 2 and len(second['items']) == 1
    assert student.get('/api/jobs/search?pageSize=1001').status_code == 422
    assert student.get('/api/candidates/search').status_code == 403
    assert recruiter.get('/api/candidates/search').json()['total'] == 0


def test_ocr_failure_retains_uploaded_cv(clients,monkeypatch):
    from fastapi import HTTPException
    student,_,_=clients
    register(student,'ocr@example.test')
    writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    output=io.BytesIO();writer.write(output)
    uploaded=student.post('/api/resumes',files={'file':('scan.pdf',output.getvalue(),'application/pdf')}).json()
    def fail(_content): raise HTTPException(422,'OCR failed')
    monkeypatch.setattr(main,'ocr_pdf',fail)
    assert student.post(f'/api/resumes/{uploaded["id"]}/analyze').status_code == 422
    assert student.get('/api/resumes/current').json()['id'] == uploaded['id']


def test_migration_is_idempotent_and_replaces_stale_profile_skill_index(clients):
    from services.api.app.db import db,init_db
    student,_,_=clients
    user=register(student,'migration@example.test')
    student.put('/api/profile',json=dict(skills=['Python']))
    cv=student.post('/api/resumes',files={'file':('cv.pdf',pdf(),'application/pdf')}).json()
    student.put('/api/profile',json=dict(skills=['SQL']))
    init_db();init_db()
    with db() as connection:
        skills=[r[0] for r in connection.execute("SELECT skill_name FROM candidate_skills WHERE user_id=? AND source='profile'",(user['id'],))]
        assert skills == ['SQL']
        assert connection.execute('SELECT MAX(version) FROM schema_version').fetchone()[0] == 4
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    assert student.get('/api/resumes/current').json()['id'] == cv['id']
