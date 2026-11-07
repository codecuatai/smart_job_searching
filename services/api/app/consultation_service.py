"""Pure snapshot analysis and exports; no writes or provider calls here."""
import hashlib
import re
from datetime import datetime, timezone
from services.ai.app.engine import extract_skills, normalize, match
from .analytics import market_dataset
from .resume_analysis import verify_analysis


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def contains_contact(text):
    return bool(re.search(r'\S+@\S+|https?://|(?:\+?\d[\s().-]*){9,}', text))


def requirement_quote(skill, rows):
    for row in rows:
        if skill not in extract_skills(row):
            continue
        if len(row) <= 700:
            return row
        for start in range(0, len(row), 500):
            quote = row[max(0, start-100):start+600]
            if skill in extract_skills(quote):
                return quote
    return skill


def build_analysis(snapshot, connection):
    text, analysis, job = snapshot['resumeText'], snapshot['analysis'], snapshot['job']
    sources = []
    def add_source(quote):
        quote = quote.strip()
        if not quote or len(quote) > 700 or contains_contact(quote) or normalize(quote) not in normalize(text):
            return None
        old = next((s for s in sources if s['quote'] == quote), None)
        if old:
            return old['id']
        identifier = f'cv-{len(sources)+1}'
        sources.append(dict(id=identifier, quote=quote))
        return identifier

    confirmed = {s['name']: s for s in analysis.get('skills', [])}
    rows = job.get('requirements', []) + job.get('tags', []) + job.get('mustHaveSkills', []) + job.get('niceToHaveSkills', [])
    required = sorted(set(extract_skills(' '.join(rows))))
    must = set(extract_skills(' '.join(job.get('mustHaveSkills', []))))
    nice = set(extract_skills(' '.join(job.get('niceToHaveSkills', []))))
    declared = set(extract_skills(snapshot['profileText']))
    gaps = []
    for skill in required:
        item = confirmed.get(skill)
        quote = item.get('evidence', '') if item else ''
        if quote and (normalize(quote) not in normalize(text) or skill not in extract_skills(quote)):
            quote = ''
        source_id = add_source(quote) if quote else None
        status = 'evidenced' if source_id else 'self-declared' if item or skill in declared else 'not-evidenced'
        gaps.append(dict(id='skill-' + digest(skill)[:12], skill=skill,
            jdQuote=requirement_quote(skill, rows),
            priority='must-have' if skill in must else 'nice-to-have' if skill in nice else 'unspecified',
            status=status, sourceId=source_id, cvQuote=quote if source_id else '',
            action='Đưa bằng chứng liên quan lên trước.' if source_id else
                   'Bổ sung minh chứng dự án/kinh nghiệm nếu đã có; nếu chưa có, học và thực hành trước khi ghi vào CV.'))
    for raw in job.get('requirements', []):
        if raw.strip() and not extract_skills(raw):
            gaps.append(dict(id='unknown-' + digest(raw)[:12], skill='Yêu cầu cần kiểm tra', jdQuote=raw,
                priority='unspecified', status='unknown', sourceId=None, cvQuote='',
                action='JD chưa ánh xạ yêu cầu này vào kỹ năng chuẩn; hãy rà soát thủ công trước khi kết luận.'))
    gaps = list({g['id']: g for g in gaps}.values())
    gaps.sort(key=lambda g: (g['status'] == 'evidenced', g['priority'] != 'must-have', g['skill']))
    for field in ('projects', 'education'):
        for quote in analysis.get(field, []):
            add_source(quote)
    headings = []
    for line in text.splitlines():
        if len(line.strip()) <= 70 and re.fullmatch(r'(?:\d[.)]?\s*)?(summary|profile|skills|projects|experience|education|certifications|technical skills|học vấn|kỹ năng|dự án|kinh nghiệm|chứng chỉ|mục tiêu nghề nghiệp)\s*[:：]?', line.strip(), re.I):
            headings.append(line.strip())
    # Only job aggregates are exposed to students; do not calculate or return candidate/funnel data.
    jobs, _ = market_dataset(connection, dataset='real', category=job.get('category'), include_candidates=False)
    total = len(jobs)
    bi = dict(totalJobs=total, dataset='real', category=job.get('category') or 'all', observedAt=timestamp(),
        sources=sorted({j.get('source', '') for j in jobs if j.get('source')}),
        postedFrom=min((j['postedDate'] for j in jobs if j.get('postedDate')), default=None),
        postedTo=max((j['postedDate'] for j in jobs if j.get('postedDate')), default=None),
        smallSample=total < 30,
        skills=[dict(skill=s, jobCount=sum(s in j['skills'] for j in jobs),
            percentage=round(100*sum(s in j['skills'] for j in jobs)/total, 1) if total else None) for s in required])
    verified_skills = [s for s in analysis.get('skills', []) if any(g['skill'] == s['name'] and g['status'] == 'evidenced' for g in gaps)]
    # Self-confirmed tags without quotes remain profile signals rather than CV evidence.
    matching_analysis = dict(analysis, skills=verified_skills)
    matching_analysis['experienceYears'] = verify_analysis(dict(analysis), text).get('experienceYears')
    return dict(gaps=gaps, sources=sources, currentOutline=list(dict.fromkeys(headings))[:20], bi=bi,
        matching=match(snapshot['profileText'], job, text, matching_analysis, True),
        selectedGapIds=[g['id'] for g in gaps if g['status'] in ('not-evidenced', 'self-declared')][:3],
        gapAssessments={}, outline=None, outlineMethod=None, script='', checklist={})


def effective_gaps(data):
    return [dict(g, status=data.get('gapAssessments', {}).get(g['id'], g['status'])) for g in data['gaps']]


def readiness(data):
    selected = set(data['selectedGapIds'])
    count = sum(g['id'] in selected and g['status'] in ('not-evidenced', 'self-declared', 'learning-needed') for g in effective_gaps(data))
    c = data.get('checklist', {})
    seconds = c.get('videoSeconds')
    return dict(gapCount=count, enoughGaps=count >= 3, hasOutline=bool(data.get('outline')),
        reviewed=bool(data.get('outline') and c.get('outlineReviewed')),
        videoValid=seconds is not None and 120 <= seconds <= 180,
        cvPermission=bool(c.get('cvPermission')), submitted=bool(c.get('submitted')))


def make_script(snapshot, data):
    chosen = [g for g in effective_gaps(data) if g['id'] in data['selectedGapIds'] and g['status'] not in ('evidenced', 'unknown')]
    lines = ['Xin chào, tôi là [tên của bạn], hôm nay tôi đóng vai chuyên gia tư vấn nghề nghiệp.',
        f"Tôi đối chiếu CV đã chọn với vị trí {snapshot['job']['title']} tại {snapshot['job']['company']}.",
        'Tôi dùng AI để hỗ trợ đọc và tổ chức CV, đồng thời dùng BI để tham khảo nhu cầu kỹ năng trong dữ liệu hệ thống. Điểm matching chỉ là tham khảo.']
    for i, g in enumerate(chosen, 1):
        finding = 'Người dùng xác nhận cần học và thực hành thêm.' if g['status'] == 'learning-needed' else 'CV chưa có minh chứng đã được kiểm chứng cho yêu cầu này; điều đó chưa chứng minh ứng viên thiếu năng lực.'
        lines.append(f"Khoảng trống {i}: {g['skill']}. JD ghi: {g['jdQuote']}. {finding} {g['action']}")
    sections = (data.get('outline') or {}).get('sections', [])
    lines.append('Tôi đề xuất bố cục CV: ' + ' → '.join(s['title'] for s in sections) + '.')
    lines.append('Đưa bằng chứng liên quan lên trước, viết rõ vai trò và kết quả có thật. Kỹ năng chưa có cần học và làm dự án trước khi bổ sung vào CV.')
    bi = data['bi']
    if bi['totalJobs']:
        lines.append(f"BI tham khảo {bi['totalJobs']} tin trong dataset hệ thống; mẫu này không đại diện toàn thị trường.")
    lines.append('Tôi sẽ kiểm tra lại bản CV đã chỉnh và đọc thử kịch bản để video nằm trong 2 đến 3 phút.')
    return '\n\n'.join(lines)


def export_markdown(case, hide_contacts=True):
    s, d = case['snapshot'], case['data']
    def safe(value):
        value = str(value)
        if hide_contacts:
            value = re.sub(r'\S+@\S+|https?://\S+|(?:\+?\d[\s().-]*){9,}', '[ẩn liên hệ]', value)
        value = value.replace('<', '&lt;').replace('>', '&gt;')
        return re.sub(r'([\\`!\[\]])', r'\\\1', value)
    out = ['# Tư vấn CV theo JD', f"Ngày tạo: {case['createdAt']}; revision: {case['revision']}",
        f"CV: {safe(s['resumeName'])}", f"Vị trí: {safe(s['job']['title'])} — {safe(s['job']['company'])}",
        f"Nguồn JD: {safe(s['job'].get('sourceUrl') or 'JD riêng/người dùng cung cấp')}",
        f"Matching: {d['matching']['matchScore']}/100 — điểm tham khảo, không phải xác suất tuyển.",
        '## Đối chiếu yêu cầu']
    labels = {'evidenced':'Có minh chứng trong CV', 'self-declared':'Chỉ tự khai báo',
        'not-evidenced':'Chưa thấy minh chứng', 'learning-needed':'Người dùng xác nhận cần học thêm', 'unknown':'Chưa đủ dữ liệu đánh giá'}
    priorities = {'must-have':'Bắt buộc', 'nice-to-have':'Ưu tiên', 'unspecified':'Chưa phân loại'}
    for g in effective_gaps(d):
        out += [f"### {safe(g['skill'])} ({labels[g['status']]}; {priorities[g['priority']]})", f"JD: {safe(g['jdQuote'])}",
            f"CV: {safe(g['cvQuote']) if g['cvQuote'] else 'Chưa có trích dẫn được kiểm chứng.'}", safe(g['action'])]
    out += ['## Outline hiện tại (người dùng cần kiểm tra)'] + [safe(h) for h in d['currentOutline']]
    out += ['## Outline đề xuất', f"Nguồn tạo: {safe(d.get('outlineMethod') or 'Chưa tạo')}; gợi ý đã chỉnh bởi người dùng: {bool(d.get('userEditedOutline'))}"]
    source_map = {x['id']: x['quote'] for x in d['sources']}
    for section in (d.get('outline') or {}).get('sections', []):
        out += [f"### {safe(section['title'])}", safe(section['reason'])]
        out += [f"- {safe(source_map[i])}" for i in section['sourceIds']]
        out += [f"Gợi ý chỉnh: {safe(section['advice'])}"]
    out += ['## Cần học/thực hành trước khi bổ sung']
    out += [f"- {safe(a['action'])}" for a in (d.get('outline') or {}).get('learningActions', [])]
    out += ['## BI tham khảo', f"Dataset real; {d['bi']['totalJobs']} tin; chụp lúc {d['bi']['observedAt']}; không đại diện toàn thị trường."]
    out += [f"- {safe(x['skill'])}: {x['jobCount']}/{d['bi']['totalJobs']} tin; " + (f"{x['percentage']}%" if x['percentage'] is not None else 'chưa có dữ liệu để tính tỷ lệ') for x in d['bi']['skills']]
    return '\n\n'.join(out)
