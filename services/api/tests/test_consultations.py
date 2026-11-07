import copy
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from services.api.app import main, consultations
from services.api.app.db import db, init_db, dump, record_origin
from services.api.app.resume_analysis import local_analysis
from services.ai.app.main import app as ai_app


@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path/'consultations.db'))
    monkeypatch.setenv('SEED_DEMO', 'false')
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('AI_TEST_FIXTURES', 'true')
    with TestClient(ai_app) as ai:
        def transport(path, body=None):
            response = ai.post(path, json=body) if body is not None else ai.get(path)
            assert response.status_code == 200, response.text
            return response.json()
        monkeypatch.setattr(consultations, 'ai_request', transport)
        with TestClient(main.app) as owner, TestClient(main.app) as other:
            for client, name in ((owner, 'owner'), (other, 'other')):
                assert client.post('/api/auth/register', json=dict(name=name, email=f'{name}@example.test', password='test12345', role='student')).status_code == 201
            yield owner, other


def add_cv(client, identifier='cv-old', text='PROJECTS\nPython API project\nEDUCATION\nBSc Computer Science', confirmed=True):
    user = client.get('/api/auth/me').json()
    analysis = local_analysis(text)
    with db() as c:
        c.execute('INSERT INTO resumes VALUES (?,?,?,?,?,?)', (identifier,user['id'],identifier+'.pdf',b'PDF-test',text,'2026-11-06T12:00:00'+identifier))
        c.execute('INSERT INTO resume_analysis VALUES (?,?,?,?)', (identifier,dump(analysis),int(confirmed),'2026-11-06'))
    return identifier


def create_case(client, resume='cv-old', text='Python required\nSQL required\nDocker required\nGit required\nTeam culture expectations'):
    return client.post('/api/cv-consultations', json=dict(resumeId=resume, customJd=dict(title='Backend Developer',company='Example',text=text,mustHaveSkills=['SQL'])))


def test_snapshot_gaps_bi_outline_edit_export_and_ownership(clients):
    owner, other = clients
    add_cv(owner)
    add_cv(owner, 'cv-new', 'SQL Docker Git Python advanced project')
    response = create_case(owner)
    assert response.status_code == 201, response.text
    case = response.json(); url = '/api/cv-consultations/'+case['id']
    assert case['snapshot']['resumeId'] == 'cv-old'
    assert case['readiness']['gapCount'] == 3
    gaps = {g['skill']: g for g in case['data']['gaps']}
    assert gaps['Python']['status'] == 'evidenced'
    assert gaps['SQL']['status'] == 'not-evidenced' and gaps['SQL']['priority'] == 'must-have'
    assert gaps['Yêu cầu cần kiểm tra']['status'] == 'unknown'
    assert case['data']['bi']['totalJobs'] == 0
    for suffix in ('', '/export'):
        assert other.get(url+suffix).status_code == 404
    assert other.post(url+'/analyze', json={'revision':1}).status_code == 404
    assert other.patch(url,json={'revision':1,'script':'steal'}).status_code == 404
    assert other.get('/api/resumes').json() == []
    assert owner.get('/api/analytics').status_code == 403
    old_snapshot=copy.deepcopy(case['snapshot'])
    with db() as c:
        c.execute('UPDATE resumes SET text=? WHERE id=?',('Changed CV','cv-old'))
    generated = owner.post(url+'/analyze',json={'revision':1})
    assert generated.status_code == 200, generated.text
    case=generated.json()
    assert case['snapshot'] == old_snapshot
    assert case['data']['outlineMethod'].startswith('test-fixture:')
    assert case['revision']==2
    outline=case['data']['outline']; outline['sections'][0]['title']='My projects'
    edited=owner.patch(url,json={'revision':2,'outline':outline,'script':'Hello <img src="x"> me@example.com +84912345678','checklist':{'cvPermission':True,'outlineReviewed':True,'videoSeconds':150}})
    assert edited.status_code==200, edited.text
    assert edited.json()['readiness']['reviewed']
    assert edited.json()['readiness']['videoValid']
    assert owner.patch(url,json={'revision':2,'script':'stale'}).status_code==409
    # Idempotent generation preserves all manual work.
    repeated=owner.post(url+'/analyze',json={'revision':3}).json()
    assert repeated['data']['outline']['sections'][0]['title']=='My projects' and repeated['revision']==3
    export=owner.get(url+'/export')
    assert export.status_code==200 and 'text/markdown' in export.headers['content-type']
    assert 'me@example.com' not in export.text and '+84912345678' not in export.text and '<img' not in export.text
    assert 'Python API project' in export.text
    assert 'Checklist' not in export.text and 'Kịch bản video' not in export.text and 'Hạn nộp' not in export.text
    with db() as c:
        assert c.execute('select count(*) from cv_consultation_revisions where consultation_id=?',(case['id'],)).fetchone()[0]==3


def test_unconfirmed_cv_insufficient_gaps_and_invalid_references(clients):
    owner, other=clients
    add_cv(owner,confirmed=False)
    assert create_case(owner).status_code==201
    assert create_case(other).status_code==404
    with db() as c: c.execute('update resume_analysis set confirmed=1')
    case=create_case(owner,text='Python required\nSQL required').json()
    assert case['readiness']['gapCount']==1
    url='/api/cv-consultations/'+case['id']
    assert owner.post(url+'/script',json={'revision':1}).status_code==422
    assert owner.patch(url,json={'revision':1,'selectedGapIds':['fiction']}).status_code==422
    assert owner.patch(url,json={'revision':1,'gapAssessments':{'fiction':'learning-needed'}}).status_code==422
    assert owner.patch(url,json={'revision':1,'snapshot':{}}).status_code==422
    r=owner.post(url+'/analyze',json={'revision':1}); assert r.status_code==200,r.text
    outline=r.json()['data']['outline']; outline['sections'][0]['sourceIds']=['fiction']
    assert owner.patch(url,json={'revision':2,'outline':outline}).status_code==422


def test_job_matches_are_scored_for_the_selected_cv_only(clients):
    owner, other = clients
    add_cv(owner, 'cv-python', 'Python API project', confirmed=True)
    add_cv(owner, 'cv-sql', 'SQL database project', confirmed=False)
    user_id = owner.get('/api/auth/me').json()['id']
    with db() as c:
        c.execute('UPDATE users SET profile=? WHERE email=?', (dump({'skills':['SQL']}), 'owner@example.test'))
        for identifier, skill in [('python-job', 'Python'), ('sql-job', 'SQL')]:
            job = dict(id=identifier, title=f'{skill} Engineer', company='Example', tags=[skill],
                requirements=[f'{skill} required'], description=f'{skill} role', category='backend')
            c.execute('INSERT INTO jobs VALUES (?,?,?)', (identifier, user_id, dump(job)))
    old = owner.get('/api/resumes/cv-python/matches?targetJobId=sql-job').json()
    assert old['resumeId'] == 'cv-python' and old['items'][0]['id'] == 'python-job'
    assert 'SQL' in old['target']['missingSkills'] and old['target']['matchScore'] == 0
    case = owner.post('/api/cv-consultations', json={'resumeId':'cv-python','jobId':'sql-job'}).json()
    assert case['snapshot']['resumeId'] == 'cv-python'
    assert case['data']['matching']['matchScore'] == old['target']['matchScore']
    newer = owner.get('/api/resumes/cv-sql/matches').json()
    assert newer['items'][0]['id'] == 'sql-job' and newer['confirmed'] is False
    assert other.get('/api/resumes/cv-python/matches').status_code == 404
    assert owner.get('/api/resumes/cv-python/matches?targetJobId=unknown').status_code == 404


def test_provider_failure_keeps_draft_and_forged_output_is_rejected(clients,monkeypatch):
    from fastapi import HTTPException
    owner,_=clients
    add_cv(owner)
    case=create_case(owner).json(); url='/api/cv-consultations/'+case['id']
    def fail(*args,**kwargs): raise HTTPException(503,'provider unavailable')
    monkeypatch.setattr(consultations,'ai_request',fail)
    assert owner.post(url+'/analyze',json={'revision':1}).status_code==503
    assert owner.get(url).json()['revision']==1
    monkeypatch.setattr(consultations,'ai_request',lambda *a,**k:dict(outline={'sections':[dict(title='Fake',reason='Fake',sourceIds=['invented'])]},method='gemini:mock'))
    assert owner.post(url+'/analyze',json={'revision':1}).status_code==502
    assert owner.get(url).json()['data']['outline'] is None


def test_script_and_truthful_gap_assessments(clients):
    owner,_=clients; add_cv(owner)
    case=create_case(owner).json(); url='/api/cv-consultations/'+case['id']
    case=owner.post(url+'/analyze',json={'revision':1}).json()
    selected=case['data']['selectedGapIds']
    case=owner.patch(url,json={'revision':2,'gapAssessments':{selected[0]:'learning-needed'}}).json()
    scripted=owner.post(url+'/script',json={'revision':3})
    assert scripted.status_code==200,scripted.text
    text=scripted.json()['data']['script']
    assert 'Backend Developer' in text and 'SQL required' in text and 'xác nhận cần học' in text
    assert owner.post(url+'/script',json={'revision':4}).json()['revision']==4


def test_bi_excludes_test_demo_and_never_returns_candidates(clients):
    owner,_=clients; add_cv(owner)
    user=owner.get('/api/auth/me').json()
    with db() as c:
        for ident,origin in [('real1','real'),('real2','real'),('demo1','demo'),('test1','test')]:
            job=dict(id=ident,title='Backend Python',company='Company',tags=['SQL'] if ident!='real2' else ['Docker'],requirements=[],description='Backend role',category='backend',source='test-source')
            c.execute('insert into jobs values (?,?,?)',(ident,user['id'],dump(job)))
            record_origin(c,'job',ident,origin)
    case=create_case(owner).json(); bi=case['data']['bi']
    assert bi['totalJobs']==2
    assert next(s for s in bi['skills'] if s['skill']=='SQL')['percentage']==50
    assert 'candidates' not in bi and 'email' not in json.dumps(bi)


def test_v5_migration_preserves_legacy_data_and_is_idempotent(tmp_path,monkeypatch):
    path=tmp_path/'legacy.db'; monkeypatch.setenv('DATABASE_PATH',str(path))
    c=sqlite3.connect(path)
    c.executescript("CREATE TABLE users (id TEXT PRIMARY KEY,email TEXT UNIQUE,name TEXT,password_hash TEXT,role TEXT,profile TEXT); INSERT INTO users VALUES ('old','old@example.test','Old','hash','student','{}');")
    c.commit();c.close()
    init_db();init_db()
    with db() as c:
        assert c.execute('select name from users where id=?',('old',)).fetchone()[0]=='Old'
        assert c.execute('select max(version) from schema_version').fetchone()[0]==5
        assert c.execute('select count(*) from cv_consultations').fetchone()[0]==0


def test_self_declared_skills_are_not_cv_evidence_or_invented_years(clients):
    owner,_=clients; add_cv(owner)
    with db() as c:
        analysis=local_analysis('Python API project')
        analysis['skills'].append(dict(name='SQL',evidence=''))
        analysis.update(experienceYears=8,experienceEvidence='Python API project')
        c.execute('update resume_analysis set data=?',(dump(analysis),))
    response=create_case(owner)
    assert response.status_code==201,response.text
    data=response.json()['data']
    sql=next(g for g in data['gaps'] if g['skill']=='SQL')
    assert sql['status']=='self-declared' and sql['sourceId'] is None
    assert 'SQL' not in data['matching']['cvMatchedSkills']


def test_jd_must_be_explicit_and_must_have_must_exist_in_jd(clients):
    owner,_=clients; add_cv(owner)
    assert owner.post('/api/cv-consultations',json={'resumeId':'cv-old'}).status_code==422
    invalid=dict(resumeId='cv-old',customJd=dict(title='Role',company='Example',text='Python project experience required',mustHaveSkills=['SQL']))
    assert owner.post('/api/cv-consultations',json=invalid).status_code==422


def test_unchanged_outline_does_not_claim_user_edited_it(clients):
    owner,_=clients;add_cv(owner)
    case=create_case(owner).json(); url='/api/cv-consultations/'+case['id']
    case=owner.post(url+'/analyze',json={'revision':1}).json()
    saved=owner.patch(url,json={'revision':2,'outline':case['data']['outline'],'checklist':{'outlineReviewed':True}})
    assert saved.status_code==200,saved.text
    assert saved.json()['data']['userEditedOutline'] is False
    assert saved.json()['readiness']['reviewed']
