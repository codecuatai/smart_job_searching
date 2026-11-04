"""Deterministic skill extraction and explainable matching, not a trained LLM."""
import math
import re
import unicodedata
from collections import Counter

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


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower().replace('đ', 'd'))
                   if not unicodedata.combining(c))


def extract_skills(text):
    text = normalize(text)
    return sorted(skill for skill, aliases in SKILLS.items()
                  if any(re.search(r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])', text)
                         for alias in aliases))


def cosine(a, b):
    # A small bag-of-words baseline. Skill coverage carries most of the score.
    vectors = [Counter(re.findall(r'[a-z0-9+#.]{2,}', normalize(s))) for s in (a, b)]
    x, y = vectors
    denominator = math.sqrt(sum(n*n for n in x.values()) * sum(n*n for n in y.values()))
    return sum(n * y[t] for t, n in x.items()) / denominator if denominator else 0.0


def match(profile_text, job):
    # Only explicit tags/requirements define required skills; prose is used for cosine.
    required_text = ' '.join(job.get('tags', []) + job.get('requirements', []))
    required = set(extract_skills(required_text))
    owned = set(extract_skills(profile_text))
    matched = sorted(required & owned)
    missing = sorted(required - owned)
    coverage = len(matched) / len(required) if required else 0
    similarity = cosine(profile_text, required_text + ' ' + job.get('description', ''))
    score = round(100 * (0.85 * coverage + 0.15 * similarity)) if required else round(100 * similarity)
    return {'matchScore': score, 'matchedSkills': matched, 'missingSkills': missing,
            'coverage': round(coverage, 4), 'cosineSimilarity': round(similarity, 4),
            'method': 'skill-coverage-85-cosine-15-v1',
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
