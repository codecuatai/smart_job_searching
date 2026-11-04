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


def test_negation_preserves_affirmative_context_and_alias_boundaries():
    assert extract_skills('Tôi chưa biết Java; đã xây API Python và SQL.') == ['Python','SQL']
    assert extract_skills('I do not know Java or Docker. Built Python projects.') == ['Python']
    assert 'Python' in extract_skills('Not only Python but also SQL')
    assert match('I have no experience with Java.',dict(tags=['Java'],requirements=[],description=''))['matchScore'] == 0


def test_must_have_and_experience_are_explicit_features():
    result=match('Python 2 years experience',dict(tags=['Python','SQL'],requirements=[],description='',mustHaveSkills=['SQL'],niceToHaveSkills=['Python'],minimumExperienceYears=4))
    assert result['missingMustHaveSkills'] == ['SQL']
    factors={f['feature']:f for f in result['scoreFactors']}
    assert factors['mustHaveCoverage']['value'] == 0
    assert factors['experienceFit']['value'] == .5
    assert factors['experienceFit']['weight'] == 0  # Baseline does not pretend to use a new feature.


def test_sparse_crawled_tags_do_not_inflate_one_skill_match():
    job = {'id': 'sparse', 'tags': ['Data Analysis', 'SQL'], 'requirements': [], 'description': ''}
    result = match('SQL', job)
    assert result['matchedSkills'] == ['SQL']
    assert result['missingSkills'] == ['Data Analysis']
    assert result['matchScore'] < 70


def test_blank_profile_stays_zero_even_for_single_tag_job():
    result = match('', {'id': 'single', 'tags': ['SQL'], 'requirements': [], 'description': 'SQL reporting'})
    assert result['matchScore'] == 0
