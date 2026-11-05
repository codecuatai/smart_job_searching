"""Deterministic skill extraction and explainable matching, not a trained LLM."""
import math
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path
from functools import lru_cache

SKILLS = {
    'Java': ['java'], 'Spring Boot': ['spring boot', 'spring framework'],
    'Python': ['python'], 'FastAPI': ['fastapi'], 'Django': ['django'], 'Flask': ['flask'],
    'C#': ['c#', 'c sharp'], 'C++': ['c++', 'cpp'], 'PHP': ['php'], 'Ruby': ['ruby'],
    'Rust': ['rust'], 'Kotlin': ['kotlin'], 'Swift': ['swift'], 'Scala': ['scala'],
    'SQL': ['sql', 'postgresql', 'mysql', 'clickhouse', 'sql server'],
    'PostgreSQL': ['postgresql', 'postgres'], 'MySQL': ['mysql'], 'MongoDB': ['mongodb', 'mongo'],
    'SQL Server': ['sql server', 'mssql'], 'Oracle Database': ['oracle database', 'oracle sql'],
    'ClickHouse': ['clickhouse'], 'Snowflake': ['snowflake'], 'BigQuery': ['bigquery'],
    'Kafka': ['kafka'], 'Docker': ['docker', 'docker compose'],
    'Kubernetes': ['kubernetes', 'k8s'], 'Terraform': ['terraform'],
    'CI/CD': ['ci/cd', 'github actions', 'gitlab ci'], 'Linux': ['linux'],
    'AWS': ['aws', 'amazon web services'], 'Microsoft Azure': ['azure'], 'Google Cloud': ['google cloud', 'gcp'],
    'Ansible': ['ansible'], 'Helm': ['helm'], 'Prometheus': ['prometheus'], 'Grafana': ['grafana'],
    'React': ['react', 'reactjs'], 'Next.js': ['next.js', 'nextjs'], 'Node.js': ['node.js', 'nodejs'],
    'Express.js': ['express.js', 'expressjs'], 'NestJS': ['nestjs'], 'Angular': ['angular'], 'Vue.js': ['vue.js', 'vuejs'],
    'HTML': ['html', 'html5'], 'CSS': ['css', 'css3'], 'GraphQL': ['graphql'],
    'TypeScript': ['typescript'], 'JavaScript': ['javascript', 'es6'],
    'Tailwind CSS': ['tailwind', 'tailwind css'], 'Redis': ['redis'],
    'Go': ['golang', 'go'], 'Git': ['git', 'github'],
    'Star Schema': ['star schema', 'data warehouse', 'kho du lieu'],
    'Airflow': ['airflow'], 'dbt': ['dbt'], 'Apache Spark': ['apache spark', 'pyspark'],
    'Power BI': ['power bi'], 'Tableau': ['tableau'], 'Machine Learning': ['machine learning', 'hoc may', 'scikit-learn', 'sklearn'],
    'TensorFlow': ['tensorflow'], 'PyTorch': ['pytorch'], 'NLP': ['natural language processing', 'nlp'],
    'Testing': ['pytest', 'jest', 'playwright', 'unit test', 'testing'],
    'REST API': ['rest api', 'restful'], 'SOLID': ['solid'],
    # Common non-code tags from ITviec/TopCV feeds. Keeping these in the same
    # taxonomy prevents a job with "SQL + Data Analysis" from looking like a
    # one-skill job and inflating the calibrated score.
    'Data Analysis': ['data analysis', 'data analyst', 'data analytics'],
    'Business Analysis': ['business analysis', 'business analyst'],
    'English': ['english', 'tieng anh'], 'Japanese': ['japanese', 'tieng nhat'],
    'Figma': ['figma'], 'Product Management': ['product management', 'product manager'],
    'Project Management': ['project management', 'project manager'],
    'Agile': ['agile'], 'Scrum': ['scrum'], 'Cloud': ['cloud'], 'DevOps': ['devops'],
    'Database': ['database'], 'Excel': ['excel'],
    'QA/QC': ['qa qc', 'qa/qc', 'quality assurance', 'quality control'],
    'Tester': ['tester'], 'Automation Testing': ['automation test', 'automation testing'],
    'ERP': ['erp'], 'LLM': ['llm', 'large language model'],
    'Software Architecture': ['software architecture'], 'Microservices': ['microservices'],
    'Communication': ['communication', 'giao tiep'], 'Team Management': ['team management'],
    'Data Visualization': ['data visualization', 'truc quan hoa du lieu'],
}


def _load_model():
    configured = os.getenv('MATCHING_MODEL_PATH')
    folder = Path(__file__).resolve().parents[1] / 'models'
    selection = folder / 'matching-selection.json'
    selected = json.loads(selection.read_text(encoding='utf-8')).get('artifact','matching-v2.json') if selection.exists() else 'matching-v2.json'
    path = Path(configured) if configured else folder / selected
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        if payload.get('version') and isinstance(payload.get('weights'), dict):
            return payload
    except (OSError, ValueError, TypeError):
        pass
    return {'version': 'baseline-v1', 'bias': 0, 'weights': {}}


MATCHING_MODEL = _load_model()
SCORER_VERSION = 'cv-evidence-v4'


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower().replace('đ', 'd'))
                   if not unicodedata.combining(c))


def extract_skills(text):
    return list(_extracted_skills(text))


@lru_cache(maxsize=1024)
def _extracted_skills(text):
    text = normalize(text)
    def affirmative(alias):
        for found in re.finditer(r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])', text):
            prefix = text[max(0, found.start()-85):found.start()]
            prefix = re.split(r'[\n;.!?]|\bbut\b|\bnhung\b|\bhowever\b', prefix)[-1]
            if not re.search(r"do not know|don't know|never used|no experience (?:with|in)|not familiar with|khong biet|chua biet|chua co kinh nghiem|khong yeu cau", prefix):
                return True
        return False
    return tuple(sorted(skill for skill, aliases in SKILLS.items() if any(affirmative(a) for a in aliases)))


def cosine(a, b):
    # A small bag-of-words baseline. Skill coverage carries most of the score.
    vectors = [Counter(re.findall(r'[a-z0-9+#.]{2,}', normalize(s))) for s in (a, b)]
    x, y = vectors
    denominator = math.sqrt(sum(n*n for n in x.values()) * sum(n*n for n in y.values()))
    return sum(n * y[t] for t, n in x.items()) / denominator if denominator else 0.0


def requirement_quality(job, required):
    """Estimate how much of the job's visible requirements we can interpret.

    Crawled listings often contain generic/unmapped tags (for example
    ``MLOps`` or ``Robot Framework``). A match on the two mapped tags must not
    be presented as a 90% match when half of the listing is unknown to the
    taxonomy.
    """
    raw_items = [str(item).strip() for key in ('tags', 'requirements', 'mustHaveSkills', 'niceToHaveSkills')
                 for item in job.get(key, []) if str(item).strip()]
    if not raw_items:
        return 0.0
    items = {normalize(item): item for item in raw_items}
    return sum(bool(extract_skills(item)) for item in items.values()) / len(items)


def candidate_signals(profile_text, resume_text='', analysis=None):
    profile = set(extract_skills(profile_text))
    if analysis is not None:
        # A confirmed removal stays removed even if it occurs in the raw PDF.
        resume = set(extract_skills('\n'.join(s['name'] for s in analysis.get('skills', []))))
    else:
        resume = set(extract_skills(resume_text))
    return profile, resume


def matching_features(profile_text, job, resume_text='', analysis=None):
    required_text = ' '.join(job.get('tags', []) + job.get('requirements', []) + job.get('mustHaveSkills', []) + job.get('niceToHaveSkills', []))
    required = set(extract_skills(required_text))
    profile_owned, resume_owned = candidate_signals(profile_text, resume_text, analysis)
    owned = profile_owned | resume_owned
    matched = sorted(required & owned)
    missing = sorted(required - owned)
    # A CV is the primary evidence.  Profile fields are useful as a small
    # supplement (for example a skill omitted from the PDF), but cannot turn a
    # mostly-unrelated CV into a near-perfect match.
    if required:
        cv_matched = required & resume_owned
        # The supplement includes CV evidence too: a complete CV earns full
        # coverage, while an absent CV can earn at most the profile's 20%.
        coverage = (0.8 * len(cv_matched) + 0.2 * len(matched)) / len(required)
    else:
        coverage = 0
    similarity = cosine((resume_text + ' ' + profile_text).strip(), required_text + ' ' + job.get('description', ''))
    return required, matched, missing, coverage, similarity, min(len(required), 10) / 10


def tfidf_similarity(a, b, idf):
    vectors = [Counter(re.findall(r'[a-z0-9+#.]{2,}', normalize(s))) for s in (a,b)]
    weighted = [{word:count*idf.get(word, 0) for word,count in vector.items()} for vector in vectors]
    x,y = weighted
    denominator = math.sqrt(sum(v*v for v in x.values())*sum(v*v for v in y.values()))
    return sum(value*y.get(word,0) for word,value in x.items())/denominator if denominator else 0.0


def feature_values(profile_text, job, idf=None, resume_text='', analysis=None):
    required, matched, missing, coverage, similarity, ratio = matching_features(profile_text, job, resume_text, analysis)
    if idf:
        similarity = tfidf_similarity((resume_text + ' ' + profile_text).strip(), ' '.join(job.get('tags', [])+job.get('requirements', []))+' '+job.get('description',''), idf)
    must = set(extract_skills(' '.join(job.get('mustHaveSkills', [])))) or required-set(extract_skills(' '.join(job.get('niceToHaveSkills', []))))
    years = experience_years(resume_text, analysis)
    needed = job.get('minimumExperienceYears')
    experience = min(years/needed, 1) if needed and years is not None else 0
    return dict(coverage=coverage, cosineSimilarity=similarity, requiredSkillRatio=ratio,
                mustHaveCoverage=len(must.intersection(matched))/len(must) if must else coverage,
                experienceFit=experience, requirementQuality=requirement_quality(job, required))


def experience_years(resume_text, analysis=None):
    if analysis is not None:
        return analysis.get('experienceYears')
    years = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|nam)\s*(?:of )?(?:experience|kinh nghiem)', normalize(resume_text))
    return float(years[1]) if years else None


def match(profile_text, job, resume_text='', analysis=None, has_resume=None):
    # Only explicit tags/requirements define required skills; prose is used for cosine.
    required, matched, missing, coverage, similarity, required_ratio = matching_features(profile_text, job, resume_text, analysis)
    features = feature_values(profile_text, job, MATCHING_MODEL.get('idf'), resume_text, analysis)
    similarity = features['cosineSimilarity']
    profile_skills, resume_skills = candidate_signals(profile_text, resume_text, analysis)
    has_resume = bool(resume_text.strip() or analysis is not None) if has_resume is None else has_resume
    if not profile_text.strip() and not resume_text.strip() or not (profile_skills | resume_skills):
        # A blank profile/CV must never receive a non-zero recommendation score.
        score = 0
        method = MATCHING_MODEL['version']
    elif not required:
        # No recognized requirements means there is not enough evidence to
        # claim a strong match, even when generic prose happens to overlap.
        score = min(round(100 * similarity), 20)
        method = MATCHING_MODEL['version']
    elif not matched:
        score = 0
        method = MATCHING_MODEL['version']
    elif MATCHING_MODEL['weights']:
        weights = MATCHING_MODEL['weights']
        logit = MATCHING_MODEL['bias'] + sum(weights.get(key,0)*value for key,value in features.items())
        probability = 1 / (1 + math.exp(-max(-30, min(30, logit))))
        score = round(100 * probability)
        method = MATCHING_MODEL['version']
    else:
        score = round(100 * (0.85 * coverage + 0.15 * similarity))
        method = 'baseline-v1'
    raw_score = score
    adjustments = []
    def cap(limit, code, reason):
        nonlocal score
        after = min(score, max(0, round(limit)))
        if after < score:
            adjustments.append(dict(code=code, reason=reason, before=score, after=after, delta=after-score))
            score = after
    if matched:
        # Calibrate the learned probability into an explainable ranking score.
        # Coverage is deliberately bounded by the CV-first 80/20 evidence
        # policy, while low-information crawled listings receive an additional
        # quality penalty. This prevents a one- or two-tag listing from showing
        # 90% merely because the candidate has a broad CV.
        quality = requirement_quality(job, required)
        calibrated = round(100 * (0.2 + 0.8 * coverage) * (0.75 + 0.25 * quality))
        cap(calibrated, 'requirement-quality', 'Hiệu chỉnh theo độ đầy đủ của yêu cầu được nhận diện.')
        cap(100 * coverage, 'evidence-coverage', 'Giới hạn theo bằng chứng CV (80%) và tín hiệu bổ sung (20%).')
        caps = {1: 55, 2: 70, 3: 78, 4: 85}
        cap(caps.get(len(required), 92), 'sparse-requirements', 'Giới hạn độ tin cậy khi tin có ít kỹ năng được nhận diện.')
        must_skills = set(extract_skills(' '.join(job.get('mustHaveSkills', []))))
        if must_skills and not must_skills.issubset(set(matched)):
            cap(score * 0.75, 'missing-must-have', 'Còn thiếu kỹ năng bắt buộc.')
        needed = job.get('minimumExperienceYears')
        years = experience_years(resume_text, analysis)
        if needed and years is None:
            cap(70, 'unknown-experience', 'CV chưa có số năm kinh nghiệm để đối chiếu yêu cầu.')
        elif needed and years < needed:
            cap(50 + 50 * years / needed, 'experience-gap', f'CV khai báo {years:g} năm; vị trí yêu cầu {needed:g} năm.')
    if resume_text.strip() and not resume_skills and profile_skills:
        # A text-bearing CV with no recognized CV skill must not be rescued by
        # profile-only tags.  Keep it visible for review, but deliberately low.
        cap(20, 'unrecognized-cv', 'Chưa có kỹ năng nhận diện được từ CV.')
    return {'matchScore': score, 'matchedSkills': matched, 'missingSkills': missing,
            'coverage': round(coverage, 4), 'cosineSimilarity': round(similarity, 4),
            'modelVersion': MATCHING_MODEL['version'] + '+' + SCORER_VERSION, 'method': method,
            'scorerVersion': SCORER_VERSION, 'rawScore': raw_score, 'finalScore': score,
            'adjustments': adjustments, 'modelBias': MATCHING_MODEL.get('bias', 0),
            'scoreStatus': 'cv-based' if has_resume and resume_skills else 'insufficient-cv',
            'cvMatchedSkills': sorted(required & resume_skills),
            'profileOnlySkills': sorted((required & profile_skills) - resume_skills),
            'unknownRequirements': list(dict.fromkeys(item for key in ('tags','requirements') for item in job.get(key,[]) if not extract_skills(item))),
            'scoreFactors': [dict(feature=k,value=round(v,4),weight=MATCHING_MODEL.get('weights',{}).get(k,0),contribution=round(v*MATCHING_MODEL.get('weights',{}).get(k,0),4)) for k,v in features.items()],
            'missingMustHaveSkills': sorted(set(extract_skills(' '.join(job.get('mustHaveSkills', []))))-set(matched)),
            'trainingData': MATCHING_MODEL.get('dataProvenance','10 synthetic fixture pairs; not an independent quality estimate'),
            'scoreMeaning': 'Điểm xếp hạng tham khảo, không phải xác suất được tuyển.',
            'evidence': [dict(skill=s, source='cv' if s in resume_skills else 'profile', quote=next((item.get('evidence','') for item in (analysis or {}).get('skills',[]) if item['name']==s), '') or next((line.strip()[:300] for line in (resume_text if s in resume_skills else profile_text).splitlines() if s in extract_skills(line)), '')) for s in matched],
            'explanation': f"Khớp {len(matched)}/{len(required)} kỹ năng; {len(required & resume_skills)} từ CV. CV chiếm trọng số chính (80%), hồ sơ bổ sung 20%. " + ('Chưa đủ bằng chứng CV; điểm sơ bộ. ' if not resume_skills else '') + 'Điểm tham khảo, không phải xác minh năng lực.'}


QUESTIONS = [
    {'id': 'api', 'question': 'Bạn thiết kế API tạo đơn hàng thế nào để tránh xử lý trùng? Nêu ví dụ và cách kiểm thử.',
     'keywords': ['idempotency', 'unique', 'transaction', 'test', 'retry']},
    {'id': 'database', 'question': 'Một truy vấn SQL chạy chậm: bạn đo lường và tối ưu như thế nào?',
     'keywords': ['explain', 'index', 'join', 'benchmark', 'query']},
    {'id': 'project', 'question': 'Hãy mô tả một lỗi khó trong đồ án, nguyên nhân, giải pháp và kết quả đo được.',
     'keywords': ['log', 'test', 'debug', 'metric', 'monitor']},
]


def evaluate(question_id, answer):
    question = next((q for q in QUESTIONS if q['id'] == question_id), None)
    if not question:
        raise ValueError('Câu hỏi không tồn tại.')
    text = normalize(answer)
    hits = [k for k in question['keywords'] if k in text]
    length_score = min(len(answer.split()) / 100, 1) * 30
    score = min(100, round(length_score + 70 * len(hits) / len(question['keywords'])))
    return {'score': score, 'matchedConcepts': hits,
            'suggestedConcepts': [k for k in question['keywords'] if k not in hits],
            'feedback': 'Bổ sung ví dụ, đánh đổi và kết quả kiểm thử cụ thể. Điểm rubric dựa trên từ khóa và độ dài, chưa đánh giá tính đúng đắn của câu trả lời.',
            'method': 'keyword-rubric-v1'}
