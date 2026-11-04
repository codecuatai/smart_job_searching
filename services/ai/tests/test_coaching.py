import pytest
from services.ai.app import coaching


def test_plan_requires_ordered_unique_weeks(monkeypatch):
    step = dict(week=1, timeRange='Week 1', focusTitle='Docker', milestones=['Build a container'], curatedResource='Docker docs')
    monkeypatch.setattr(coaching, 'generate_json', lambda prompt: dict(summary='Practice Docker', roadmap=[step, step]))
    with pytest.raises(ValueError):
        coaching.generate_plan({'recognizedSkills': ['Python']}, ['Docker'], 6)


def test_generated_questions_require_all_topics(monkeypatch):
    q = dict(topic='api', question='Explain idempotency and give an example.', keywords=['idempotency'])
    monkeypatch.setattr(coaching, 'generate_json', lambda prompt: {'questions': [q, q, q]})
    with pytest.raises(ValueError):
        coaching.generate_questions({})
