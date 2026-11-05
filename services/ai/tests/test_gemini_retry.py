import httpx
import pytest
from services.ai.app import gemini


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'private-test-key')
    monkeypatch.setenv('GEMINI_ENABLED', 'true')
    monkeypatch.setenv('GEMINI_TIMEOUT_SECONDS', '60')
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL', '')
    calls, sleeps = [], []
    clock = [0.0]
    monkeypatch.setattr(gemini.time, 'monotonic', lambda: clock[0])
    def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds
    monkeypatch.setattr(gemini.time, 'sleep', sleep)
    monkeypatch.setattr(gemini.random, 'uniform', lambda a,b: 0)
    real_client = httpx.Client
    def install(responses):
        def handle(request):
            calls.append(request)
            item = responses[min(len(calls)-1, len(responses)-1)]
            if isinstance(item, Exception):
                raise item
            status, body, headers = item
            return httpx.Response(status, json=body, headers=headers)
        monkeypatch.setattr(gemini.httpx, 'Client', lambda: real_client(transport=httpx.MockTransport(handle)))
    return install, calls, sleeps


SUCCESS = (200, {'candidates':[{'content':{'parts':[{'text':'{"ok":true}'}]}}]}, {})
BUSY = (503, {'error':{'status':'UNAVAILABLE','message':'high demand'}}, {})


def test_recovers_after_more_than_two_busy_responses(provider):
    install, calls, sleeps = provider
    install([BUSY, BUSY, BUSY, SUCCESS])
    assert gemini.generate_text('public synthetic prompt') == '{"ok":true}'
    assert len(calls) == 4 and sleeps == [1,2,4]


def test_persistent_outage_stops_after_bounded_attempts(provider):
    install, calls, sleeps = provider
    install([BUSY])
    with pytest.raises(httpx.HTTPStatusError):
        gemini.generate_text('synthetic')
    assert len(calls) == gemini.MAX_ATTEMPTS == 6
    assert sleeps == [1,2,4,8,16] and sum(sleeps) < 60


@pytest.mark.parametrize('status',[400,401,403,404])
def test_invalid_key_or_model_is_not_retried(provider,status):
    install, calls, sleeps = provider
    install([(status, {'error':{'message':'invalid configuration'}}, {})])
    with pytest.raises(httpx.HTTPStatusError):
        gemini.generate_text('synthetic')
    assert len(calls) == 1 and sleeps == []


def test_retry_after_beyond_deadline_does_not_trigger_another_call(provider):
    install, calls, sleeps = provider
    install([(429, {'error':{}}, {'Retry-After':'120'})])
    with pytest.raises(httpx.HTTPStatusError):
        gemini.generate_text('synthetic')
    assert len(calls) == 1 and sleeps == []


def test_quota_retry_respects_google_retry_info(provider):
    install, calls, sleeps = provider
    install([(429, {'error':{'details':[{'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'7.5s'}]}}, {}),SUCCESS])
    assert gemini.generate_text('synthetic')
    assert sleeps == [7.5] and len(calls) == 2


def test_rate_limit_without_hint_does_not_spin(provider):
    install, calls, sleeps = provider
    install([(429, {'error':{}}, {}),SUCCESS])
    assert gemini.generate_text('synthetic')
    assert sleeps == [30] and len(calls) == 2


def test_fallback_provenance_is_per_result_and_cannot_be_spoofed(provider,monkeypatch):
    install, calls, sleeps = provider
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL','gemini-3.1-flash-lite')
    spoofed=(200,{'candidates':[{'content':{'parts':[{'text':'{"model":"spoofed"}'}]}}]}, {})
    install([BUSY,BUSY,spoofed,SUCCESS])
    fallback = gemini.generate_json('synthetic')
    primary = gemini.generate_json('another synthetic')
    assert [r.url.path.split('/')[-1] for r in calls] == [
        'gemini-3.5-flash-lite:generateContent','gemini-3.5-flash-lite:generateContent',
        'gemini-3.1-flash-lite:generateContent','gemini-3.5-flash-lite:generateContent']
    assert gemini.generation_method(fallback) == 'gemini:gemini-3.1-flash-lite'
    assert gemini.generation_method(primary) == 'gemini:gemini-3.5-flash-lite'
    assert fallback['model'] == 'spoofed'


@pytest.mark.parametrize('status',[403,404,429])
def test_fallback_does_not_mask_bad_configuration_or_bypass_quota(provider,monkeypatch,status):
    install, calls, sleeps = provider
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL','gemini-3.1-flash-lite')
    install([(status,{'error':{}},{'Retry-After':'120'})])
    with pytest.raises(httpx.HTTPStatusError):
        gemini.generate_json('synthetic')
    assert len(calls)==1 and 'gemini-3.5-flash-lite:' in calls[0].url.path


def test_primary_timeout_leaves_room_for_fallback(provider,monkeypatch):
    install, calls, sleeps = provider
    monkeypatch.setenv('GEMINI_FALLBACK_MODEL','gemini-3.1-flash-lite')
    install([httpx.ReadTimeout('private transport details'),SUCCESS])
    result=gemini.generate_json('synthetic')
    assert len(calls)==2 and gemini.generation_method(result)=='gemini:gemini-3.1-flash-lite'
    assert calls[0].extensions['timeout']['read'] == 20
