import httpx
import pytest
from fastapi import HTTPException
from services.api.app import ai_client


@pytest.mark.parametrize('status,expected', [(404, 404), (500, 503)])
def test_ai_http_errors_are_mapped_without_silent_mock_fallback(monkeypatch, status, expected):
    class Client:
        def __init__(self, **_):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_):
            pass
        def post(self, path, json):
            return httpx.Response(status, request=httpx.Request('POST', 'http://ai' + path))
    monkeypatch.setattr(ai_client.httpx, 'Client', Client)
    with pytest.raises(HTTPException) as error:
        ai_client.ai_request('/interview/evaluate', {'questionId': 'invalid'})
    assert error.value.status_code == expected
