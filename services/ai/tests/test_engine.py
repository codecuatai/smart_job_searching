from services.ai.app.engine import evaluate, extract_skills, match


def test_skill_aliases_boundaries_and_vietnamese():
    skills = extract_skills('Javascript TypeScript Spring Boot 3.3 PostgreSQL kho dữ liệu Next.js k8s Django')
    assert 'Java' not in skills  # JavaScript must never imply Java.
    assert 'Go' not in skills  # Django must never imply Go.
    assert {'JavaScript', 'TypeScript', 'Spring Boot', 'SQL', 'PostgreSQL', 'Star Schema', 'Next.js', 'Kubernetes'} <= set(skills)


def test_common_ai_cloud_and_web_skills_are_extracted():
    skills = extract_skills('Django, Node.js, C++, AWS, Power BI, PyTorch and Vue.js')
    assert {'Django', 'Node.js', 'C++', 'AWS', 'Power BI', 'PyTorch', 'Vue.js'} <= set(skills)


def test_profile_changes_recompute_score_and_explanation():
    job = {'id': '1', 'tags': ['Python', 'SQL', 'Docker'], 'requirements': [], 'description': ''}
    empty = match('', job)
    partial = match('Python SQL', job)
    complete = match('Python SQL Docker', job)
    assert empty['matchScore'] == 0
    assert empty['missingSkills'] == ['Docker', 'Python', 'SQL']
    assert 0 < partial['matchScore'] < complete['matchScore'] <= 100
    assert partial['matchedSkills'] == ['Python', 'SQL']
    assert partial['missingSkills'] == ['Docker']


def test_rubric_not_constant_for_different_answers():
    low = evaluate('api', 'Tôi chưa biết.')
    high = evaluate('api', 'idempotency unique transaction test retry ' * 20)
    assert low['score'] < high['score']
    assert low['suggestedConcepts']
    assert high['score'] == 100
