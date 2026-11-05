import httpx
import pytest
from services.ai.app.gemini import fixture_enabled, generate_json, generation_method
from services.ai.app.provider_errors import unavailable


def test_offline_fixture_cannot_be_enabled_in_production(monkeypatch):
    monkeypatch.setenv('AI_TEST_FIXTURES', 'true')
    monkeypatch.setenv('APP_ENV', 'production')
    with pytest.raises(RuntimeError):
        fixture_enabled()
    monkeypatch.setenv('APP_ENV', 'test')
    assert generation_method().startswith('test-fixture:')
    result = generate_json('Phân tích văn bản CV. CV: Python SQL projects. I do not know Java.')
    assert {s['name'] for s in result['skills']} == {'Python','SQL'}


@pytest.mark.parametrize('status,code', [(429,'provider-quota'),(503,'provider-unavailable'),(403,'provider-configuration')])
def test_safe_provider_errors_have_traceable_category_without_secrets(monkeypatch,status,code):
    monkeypatch.setenv('GEMINI_API_KEY','secret-test-key')
    monkeypatch.setenv('GEMINI_ENABLED','true')
    request = httpx.Request('POST','https://provider.invalid/?key=secret-test-key')
    error = httpx.HTTPStatusError('sensitive provider body',request=request,response=httpx.Response(status,request=request))
    public = unavailable(error)
    assert public.status_code == 503
    assert public.detail['code'] == code and public.detail['requestId']
    assert 'secret-test-key' not in str(public.detail)


def test_timeout_and_invalid_json_are_distinct(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','fake-key')
    monkeypatch.setenv('GEMINI_ENABLED','true')
    assert unavailable(httpx.ReadTimeout('private prompt')).detail['code'] == 'provider-timeout'
    assert unavailable(ValueError('private prompt')).detail['code'] == 'provider-invalid-output'


def test_missing_key_reports_configuration_and_no_retry(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','')
    public = unavailable(RuntimeError('private configuration'))
    assert public.detail['code'] == 'ai-not-configured'
    assert public.detail['retryable'] is False
