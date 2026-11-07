import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from services.ai.app.cv_outline import validate_outline
from .ai_client import ai_request
from .db import db, dump
from .security import require_role
from .consultation_schemas import CreateConsultation, ConsultationEdit, RevisionInput
from .consultation_service import (build_analysis, digest, effective_gaps,
    export_markdown, make_script, readiness, timestamp)
from .resume_analysis import verify_analysis

router = APIRouter(prefix='/api', tags=['CV consultation'])
student = require_role('student')


def owned(identifier, user):
    with db() as c:
        row = c.execute('SELECT * FROM cv_consultations WHERE id=? AND user_id=?', (identifier, user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Không tìm thấy ca tư vấn.')
    return dict(row)


def result(row):
    data = json.loads(row['data'])
    return dict(id=row['id'], revision=row['revision'], createdAt=row['created_at'], updatedAt=row['updated_at'],
        snapshot=json.loads(row['snapshot']), data=data, readiness=readiness(data))


def context(row, data):
    snapshot = json.loads(row['snapshot'])
    return dict(job=snapshot['job'], sources=data['sources'], gaps=effective_gaps(data), currentOutline=data['currentOutline'])


def check_revision(row, revision):
    if row['revision'] != revision:
        raise HTTPException(409, 'Bản tư vấn đã thay đổi ở tab khác. Tải lại bản mới trước khi lưu; nội dung đang sửa vẫn được giữ trên màn hình.')


def save(row, data, revision):
    check_revision(row, revision)
    now = timestamp()
    with db() as c:
        count = c.execute('UPDATE cv_consultations SET data=?,revision=revision+1,updated_at=? WHERE id=? AND user_id=? AND revision=?',
            (dump(data), now, row['id'], row['user_id'], revision)).rowcount
        if not count:
            raise HTTPException(409, 'Bản tư vấn đã thay đổi. Tải lại trước khi lưu.')
        c.execute('INSERT INTO cv_consultation_revisions VALUES (?,?,?,?)', (row['id'], revision+1, dump(data), now))
    return result(dict(row, data=dump(data), revision=revision+1, updated_at=now))


@router.get('/resumes')
def resume_versions(user=Depends(student)):
    with db() as c:
        rows = c.execute('SELECT r.id,r.name,r.created_at,length(r.content) AS size,a.confirmed,a.data FROM resumes r '
            'LEFT JOIN resume_analysis a ON a.resume_id=r.id WHERE r.user_id=? ORDER BY r.created_at DESC', (user['id'],)).fetchall()
    return [dict(id=r['id'], name=r['name'], createdAt=r['created_at'], size=r['size'], confirmed=bool(r['confirmed']),
        analysis=json.loads(r['data']) if r['data'] else None) for r in rows]


@router.get('/resumes/{resume_id}/matches')
def resume_matches(resume_id: str, targetJobId: str = '', limit: int = Query(12, ge=1, le=50), user=Depends(student)):
    """Rank jobs against one owned CV; never substitute the latest CV or profile tags."""
    with db() as c:
        cv = c.execute('SELECT r.id,r.name,r.text,a.data,a.confirmed FROM resumes r '
            'LEFT JOIN resume_analysis a ON a.resume_id=r.id WHERE r.id=? AND r.user_id=?',
            (resume_id, user['id'])).fetchone()
        if not cv:
            raise HTTPException(404, 'Không tìm thấy CV.')
        jobs = [json.loads(r['data']) for r in c.execute('SELECT data FROM jobs').fetchall()]
    if not cv['text'].strip():
        raise HTTPException(422, 'CV chưa có văn bản để so sánh. Hãy phân tích OCR hoặc tải PDF có lớp chữ.')
    if targetJobId and not any(job['id'] == targetJobId for job in jobs):
        raise HTTPException(404, 'Không tìm thấy job đã chọn.')
    analysis = verify_analysis(json.loads(cv['data']), cv['text']) if cv['confirmed'] and cv['data'] else None
    inputs = dict(profileText='', resumeText=cv['text'][:100000], resumeAnalysis=analysis, hasResume=True)
    scored = {}
    for start in range(0, len(jobs), 500):
        scored.update({m['id']: m for m in ai_request('/match', dict(**inputs, jobs=jobs[start:start + 500]))})
    ranked = [dict(job, **{k: v for k, v in scored[job['id']].items() if k != 'id'}) for job in jobs]
    ranked.sort(key=lambda job: (-job['matchScore'], -len(job.get('matchedSkills', [])), job['title']))
    def summary(job):
        return {key: job.get(key) for key in ('id','title','company','location','workType','salary','tags',
            'matchScore','scoreStatus','matchedSkills','missingSkills','unknownRequirements','isDemo')}
    positive = [job for job in ranked if job['matchScore'] > 0]
    target = next((summary(job) for job in ranked if job['id'] == targetJobId), None)
    return dict(resumeId=cv['id'], resumeName=cv['name'], confirmed=bool(cv['confirmed']),
        evaluatedJobs=len(jobs), total=len(positive), items=[summary(job) for job in positive[:limit]], target=target)


@router.post('/cv-consultations', status_code=201)
def create(body: CreateConsultation, user=Depends(student)):
    with db() as c:
        cv = c.execute('SELECT r.*,a.data,a.confirmed FROM resumes r LEFT JOIN resume_analysis a ON a.resume_id=r.id '
            'WHERE r.id=? AND r.user_id=?', (body.resumeId, user['id'])).fetchone()
        if not cv:
            raise HTTPException(404, 'Không tìm thấy CV.')
        if not cv['text'].strip():
            raise HTTPException(409, 'CV chưa có văn bản để so sánh. Hãy phân tích OCR hoặc tải PDF có lớp chữ.')
        if body.jobId:
            job_row = c.execute('SELECT data FROM jobs WHERE id=?', (body.jobId,)).fetchone()
            if not job_row:
                raise HTTPException(404, 'Không tìm thấy JD.')
            job = json.loads(job_row['data'])
        else:
            jd = body.customJd
            job = dict(title=jd.title, company=jd.company, description=jd.text, tags=[],
                requirements=[line.strip(' •-\t') for line in jd.text.splitlines() if line.strip()],
                mustHaveSkills=jd.mustHaveSkills, niceToHaveSkills=[], sourceUrl=jd.sourceUrl, source='user-provided', category='all')
        # Only keep job fields relevant to this consultation; never recruiter/account fields.
        job = {k: job.get(k) for k in ('id', 'title', 'company', 'description', 'requirements', 'tags', 'mustHaveSkills',
            'niceToHaveSkills', 'minimumExperienceYears', 'category', 'source', 'sourceUrl') if job.get(k) is not None}
        if not str(job.get('sourceUrl', '')).lower().startswith(('https://', 'http://')):
            job.pop('sourceUrl', None)
        snapshot = dict(schemaVersion=1, resumeId=cv['id'], resumeName=cv['name'], resumeText=cv['text'],
            resumeHash=digest(bytes(cv['content'])), analysis=json.loads(cv['data']), analysisConfirmed=bool(cv['confirmed']), profileText='',
            job=job, capturedAt=timestamp())
        data = build_analysis(snapshot, c)
        identifier, now = str(uuid.uuid4()), timestamp()
        c.execute('INSERT INTO cv_consultations VALUES (?,?,?,?,?,?,?,?,?)',
            (identifier, user['id'], cv['id'], digest(dump(snapshot)), dump(snapshot), dump(data), 1, now, now))
        c.execute('INSERT INTO cv_consultation_revisions VALUES (?,?,?,?)', (identifier, 1, dump(data), now))
    return result(owned(identifier, user))


@router.get('/cv-consultations')
def listing(user=Depends(student)):
    with db() as c:
        rows = c.execute('SELECT * FROM cv_consultations WHERE user_id=? ORDER BY created_at DESC', (user['id'],)).fetchall()
    return [dict(id=r['id'], revision=r['revision'], createdAt=r['created_at'], resumeId=r['resume_id'],
        jobId=json.loads(r['snapshot'])['job'].get('id'), title=json.loads(r['snapshot'])['job']['title'],
        company=json.loads(r['snapshot'])['job']['company'], resumeName=json.loads(r['snapshot'])['resumeName']) for r in rows]


@router.get('/cv-consultations/{identifier}')
def detail(identifier: str, user=Depends(student)):
    return result(owned(identifier, user))


@router.post('/cv-consultations/{identifier}/analyze')
def analyze(identifier: str, body: RevisionInput, user=Depends(student)):
    row = owned(identifier, user)
    check_revision(row, body.revision)
    data = json.loads(row['data'])
    if data['outline']:
        return result(row)  # Repeated clicks never replace an edited Outline.
    ctx = context(row, data)
    generated = ai_request('/resume/outline', dict(context=ctx))
    try:
        data['outline'] = validate_outline(generated.get('outline', {}), ctx)
        method = generated['method']
        if not isinstance(method, str) or not method.startswith(('gemini:', 'test-fixture:')):
            raise ValueError('Missing provider metadata')
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(502, 'Outline AI không hợp lệ. Bản nháp đã được giữ lại; vui lòng thử lại.') from error
    data.update(outlineMethod=method, promptVersion=generated.get('promptVersion'), userEditedOutline=False)
    data['checklist']['outlineReviewed'] = False
    return save(row, data, body.revision)


@router.patch('/cv-consultations/{identifier}')
def edit(identifier: str, body: ConsultationEdit, user=Depends(student)):
    row = owned(identifier, user)
    check_revision(row, body.revision)
    data = json.loads(row['data'])
    eligible = {g['id'] for g in data['gaps'] if g['status'] != 'evidenced'}
    if body.selectedGapIds is not None:
        if not set(body.selectedGapIds) <= eligible:
            raise HTTPException(422, 'Chỉ chọn khoảng trống thuộc ca tư vấn này.')
        data['selectedGapIds'] = list(dict.fromkeys(body.selectedGapIds))
    if body.gapAssessments is not None:
        if not set(body.gapAssessments) <= eligible:
            raise HTTPException(422, 'Không thể thay đổi bằng chứng đã kiểm chứng.')
        data['gapAssessments'] = body.gapAssessments
    if body.outline is not None:
        if not data['outline']:
            raise HTTPException(409, 'Tạo Outline trước khi chỉnh sửa.')
        try:
            updated_outline = validate_outline(body.outline.model_dump(), context(row, data))
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        if updated_outline != data['outline']:
            data['userEditedOutline'] = True
            data['checklist']['outlineReviewed'] = False
        data['outline'] = updated_outline
    if body.currentOutline is not None:
        if any(not s.strip() or len(s) > 150 for s in body.currentOutline):
            raise HTTPException(422, 'Tiêu đề section cần có nội dung, tối đa 150 ký tự.')
        data['currentOutline'] = body.currentOutline
    if body.script is not None:
        data['script'] = body.script
    if body.checklist is not None:
        data['checklist'] = body.checklist.model_dump(mode='json')
    return save(row, data, body.revision)


@router.post('/cv-consultations/{identifier}/script')
def script(identifier: str, body: RevisionInput, user=Depends(student)):
    row = owned(identifier, user)
    check_revision(row, body.revision)
    data = json.loads(row['data'])
    if not data['outline'] or not readiness(data)['enoughGaps']:
        raise HTTPException(422, 'Cần Outline và ít nhất 3 khoảng trống đã chọn có căn cứ trước khi tạo kịch bản.')
    if not data['script']:
        data['script'] = make_script(json.loads(row['snapshot']), data)
        return save(row, data, body.revision)
    return result(row)


@router.get('/cv-consultations/{identifier}/export')
def export(identifier: str, hideContacts: bool = True, user=Depends(student)):
    case = result(owned(identifier, user))
    return Response(export_markdown(case, hideContacts), media_type='text/markdown; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="cv-consultation-{identifier}.md"'})
