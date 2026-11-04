"""Deterministic skill extraction and explainable matching, not a trained LLM."""
import math
import json
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

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


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower().replace('đ', 'd'))
                   if not unicodedata.combining(c))


def extract_skills(text):
    text = normalize(text)
    def affirmative(alias):
        for found in re.finditer(r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])', text):
            prefix = text[max(0, found.start()-85):found.start()]
            prefix = re.split(r'[\n;.!?]|\bbut\b|\bnhung\b|\bhowever\b', prefix)[-1]
            if not re.search(r"do not know|don't know|never used|no experience (?:with|in)|not familiar with|khong biet|chua biet|chua co kinh nghiem|khong yeu cau", prefix):
                return True
        return False
    return sorted(skill for skill, aliases in SKILLS.items() if any(affirmative(a) for a in aliases))


def cosine(a, b):
    # A small bag-of-words baseline. Skill coverage carries most of the score.
    vectors = [Counter(re.findall(r'[a-z0-9+#.]{2,}', normalize(s))) for s in (a, b)]
    x, y = vectors
    denominator = math.sqrt(sum(n*n for n in x.values()) * sum(n*n for n in y.values()))
    return sum(n * y[t] for t, n in x.items()) / denominator if denominator else 0.0


def matching_features(profile_text, job):
    required_text = ' '.join(job.get('tags', []) + job.get('requirements', []) + job.get('mustHaveSkills', []) + job.get('niceToHaveSkills', []))
    required = set(extract_skills(required_text))
    owned = set(extract_skills(profile_text))
    matched = sorted(required & owned)
    missing = sorted(required - owned)
    coverage = len(matched) / len(required) if required else 0
    similarity = cosine(profile_text, required_text + ' ' + job.get('description', ''))
    return required, matched, missing, coverage, similarity, min(len(required), 10) / 10


def tfidf_similarity(a, b, idf):
    vectors = [Counter(re.findall(r'[a-z0-9+#.]{2,}', normalize(s))) for s in (a,b)]
    weighted = [{word:count*idf.get(word, 0) for word,count in vector.items()} for vector in vectors]
    x,y = weighted
    denominator = math.sqrt(sum(v*v for v in x.values())*sum(v*v for v in y.values()))
    return sum(value*y.get(word,0) for word,value in x.items())/denominator if denominator else 0.0


def feature_values(profile_text, job, idf=None):
    required, matched, missing, coverage, similarity, ratio = matching_features(profile_text, job)
    if idf:
        similarity = tfidf_similarity(profile_text, ' '.join(job.get('tags', [])+job.get('requirements', []))+' '+job.get('description',''), idf)
    must = set(extract_skills(' '.join(job.get('mustHaveSkills', [])))) or required-set(extract_skills(' '.join(job.get('niceToHaveSkills', []))))
    years = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|nam)\s*(?:of )?(?:experience|kinh nghiem)', normalize(profile_text))
    needed = job.get('minimumExperienceYears')
    experience = min(float(years[1])/needed, 1) if needed and years else 0
    return dict(coverage=coverage, cosineSimilarity=similarity, requiredSkillRatio=ratio,
                mustHaveCoverage=len(must.intersection(matched))/len(must) if must else coverage,
                experienceFit=experience)


def match(profile_text, job):
    # Only explicit tags/requirements define required skills; prose is used for cosine.
    required, matched, missing, coverage, similarity, required_ratio = matching_features(profile_text, job)
    features = feature_values(profile_text, job, MATCHING_MODEL.get('idf'))
    similarity = features['cosineSimilarity']
    if not required:
        score = round(100 * similarity)
        method = 'baseline-v1'
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
    return {'matchScore': score, 'matchedSkills': matched, 'missingSkills': missing,
            'coverage': round(coverage, 4), 'cosineSimilarity': round(similarity, 4),
            'modelVersion': MATCHING_MODEL['version'], 'method': method,
            'scoreFactors': [dict(feature=k,value=round(v,4),weight=MATCHING_MODEL.get('weights',{}).get(k,0),contribution=round(v*MATCHING_MODEL.get('weights',{}).get(k,0),4)) for k,v in features.items()],
            'missingMustHaveSkills': sorted(set(extract_skills(' '.join(job.get('mustHaveSkills', []))))-set(matched)),
            'trainingData': MATCHING_MODEL.get('dataProvenance','10 synthetic fixture pairs; not an independent quality estimate'),
            'scoreMeaning': 'Điểm xếp hạng tham khảo, không phải xác suất được tuyển.',
            'evidence': [dict(skill=s,quote=next((line.strip()[:300] for line in profile_text.splitlines() if s in extract_skills(line)), '') ) for s in matched],
            'explanation': f'Khớp {len(matched)}/{len(required)} kỹ năng nhận diện được. Điểm tham khảo, không phải xác minh năng lực.'}


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
