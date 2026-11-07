import pytest
from services.ai.app import cv_outline


def test_outline_keeps_facts_as_source_ids_and_real_provenance(monkeypatch):
    context=dict(sources=[dict(id='cv-1',quote='Python project')],gaps=[dict(id='gap-1',status='not-evidenced')])
    raw=dict(sections=[dict(title='Projects',reason='Show relevant work',sourceIds=['cv-1'],gapIds=['gap-1'])],learningActions=[])
    monkeypatch.setattr(cv_outline,'generate_json',lambda p:raw)
    monkeypatch.setattr(cv_outline,'generation_method',lambda r:'gemini:actual-provider')
    result=cv_outline.generate_outline(context)
    assert result['method']=='gemini:actual-provider'
    assert result['sections'][0]['sourceIds']==['cv-1']
    raw['sections'][0]['sourceIds']=['hallucinated']
    with pytest.raises(ValueError): cv_outline.generate_outline(context)


def test_outline_does_not_accept_invented_bullet_or_completed_skill_as_gap():
    ctx=dict(sources=[],gaps=[dict(id='done',status='evidenced')])
    with pytest.raises(ValueError):
        cv_outline.validate_outline(dict(sections=[dict(title='Fake',reason='Fake',bullets=['Increased revenue 80%'])]),ctx)
    with pytest.raises(ValueError):
        cv_outline.validate_outline(dict(sections=[dict(title='Fake',reason='Fake',gapIds=['done'])]),ctx)
