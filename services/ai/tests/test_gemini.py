import httpx
import pytest
from services.ai.app import gemini


def test_transient_retry_is_bounded_and_never_logs_key(monkeypatch,caplog):
    monkeypatch.setenv('GEMINI_API_KEY','private-test-key-not-real')
    monkeypatch.setenv('GEMINI_ENABLED','true')
    real_client=httpx.Client
    calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(503) if len(calls)==1 else httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'{"ok":true}'}]}}]})
    monkeypatch.setattr(gemini.httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(handle),**kwargs))
    monkeypatch.setattr(gemini.time,'sleep',lambda seconds:None)
    assert gemini.generate_json('test') == {'ok':True}
    assert len(calls)==2
    assert 'private-test-key-not-real' not in caplog.text


def test_nontransient_error_is_not_retried(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','fake-key')
    monkeypatch.setenv('GEMINI_ENABLED','true')
    real_client=httpx.Client;calls=[]
    def handle(request):
        calls.append(request);return httpx.Response(403)
    monkeypatch.setattr(gemini.httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(handle),**kwargs))
    with pytest.raises(httpx.HTTPStatusError):gemini.generate_text('test')
    assert len(calls)==1
