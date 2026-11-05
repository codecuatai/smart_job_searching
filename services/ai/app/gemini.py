"""Small Gemini REST client used by the AI service.

The deterministic matcher remains local so a job list can be ranked without
one network request per job. Gemini is used for generative tasks (currently
interview feedback and CV extraction). Generative failures are reported to
the caller; deterministic fixtures are restricted to explicit test deployments.
"""

from __future__ import annotations

import json
import os
import re
import time
import logging
from typing import Any

import httpx

GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'


def fixture_enabled():
    enabled = os.getenv('AI_TEST_FIXTURES') == 'true'
    if enabled and os.getenv('APP_ENV') != 'test':
        raise RuntimeError('AI_TEST_FIXTURES requires APP_ENV=test')
    return enabled


def generation_method():
    return 'test-fixture:offline-v1' if fixture_enabled() else f'gemini:{settings()["model"]}'


def settings() -> dict[str, Any]:
    enabled = os.getenv('GEMINI_ENABLED', 'true').strip().lower() in {'1', 'true', 'yes', 'on'}
    key = os.getenv('GEMINI_API_KEY', '').strip()
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip() or 'gemini-3.5-flash-lite'
    try:
        # Gemini generation (especially PDF/OCR prompts) can legitimately take
        # longer than a normal API request. Keep the timeout bounded but avoid
        # returning a misleading 503 while the provider is still processing.
        timeout = float(os.getenv('GEMINI_TIMEOUT_SECONDS', '60'))
    except ValueError:
        timeout = 60.0
    return {'enabled': enabled, 'configured': bool(key), 'model': model, 'timeout': max(3.0, timeout), 'key': key}


def status() -> dict[str, Any]:
    config = settings()
    return {'provider': 'gemini', 'model': config['model'], 'enabled': config['enabled'],
            'configured': config['configured']}


def _text_from_response(payload: dict[str, Any]) -> str:
    candidates = payload.get('candidates') or []
    if not candidates:
        raise RuntimeError('Gemini không trả về candidate.')
    parts = ((candidates[0].get('content') or {}).get('parts') or [])
    text = ''.join(str(part.get('text', '')) for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise RuntimeError('Gemini trả về nội dung rỗng.')
    return text


def generate_text(prompt: str, *, json_mode: bool = False) -> str:
    config = settings()
    if not config['enabled'] or not config['configured']:
        raise RuntimeError('Gemini chưa được bật hoặc chưa có GEMINI_API_KEY.')
    body: dict[str, Any] = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 4096},
    }
    if json_mode:
        body['generationConfig']['responseMimeType'] = 'application/json'
    url = GEMINI_ENDPOINT.format(model=config['model'])
    deadline=time.monotonic()+config['timeout']
    for attempt in range(2):
        try:
            with httpx.Client(timeout=max(1,deadline-time.monotonic())) as client:
                response = client.post(url, params={'key': config['key']}, json=body)
                response.raise_for_status()
                return _text_from_response(response.json())
        except (httpx.HTTPError,RuntimeError) as error:
            status=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else None
            # Never log exception strings/URLs: the upstream URL contains the key.
            logging.getLogger(__name__).warning('Gemini failure type=%s status=%s attempt=%s',type(error).__name__,status,attempt+1)
            if attempt or (status is not None and status not in (429,500,502,503,504)) or deadline-time.monotonic()<2:
                raise
            time.sleep(0.4)


def generate_json(prompt: str) -> dict[str, Any]:
    if fixture_enabled():
        from .fixture_provider import generate
        return generate(prompt)
    raw = generate_text(prompt, json_mode=True)
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.I)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError('Gemini JSON phải là object.')
    return value


def evaluate_interview(question: str, answer: str, keywords: list[str]) -> dict[str, Any]:
    prompt = f'''Bạn là trợ lý đánh giá phỏng vấn kỹ thuật bằng tiếng Việt.
Đánh giá câu trả lời dựa trên tính đúng đắn, cấu trúc, ví dụ, trade-off và kiểm thử.
Không bịa thông tin và không đánh giá ngoại hình, giới tính, tuổi hay trường học.
Trả về duy nhất JSON hợp lệ với schema:
{{"score": number từ 0 đến 100, "matchedConcepts": [string],
"suggestedConcepts": [string], "feedback": string}}

Câu hỏi: {question}
Các khái niệm tham chiếu: {', '.join(keywords)}
Câu trả lời ứng viên: {answer}
'''
    result = generate_json(prompt)
    score = max(0, min(100, int(float(result.get('score', 0)))))
    matched = [str(item) for item in result.get('matchedConcepts', []) if str(item).strip()][:12]
    suggested = [str(item) for item in result.get('suggestedConcepts', []) if str(item).strip()][:12]
    feedback = str(result.get('feedback', '')).strip()[:2000]
    if not feedback:
        raise ValueError('Gemini thiếu feedback.')
    return {'score': score, 'matchedConcepts': matched, 'suggestedConcepts': suggested,
            'feedback': feedback, 'method': generation_method()}


def extract_skills(text: str) -> list[str]:
    prompt = f'''Trích xuất kỹ năng kỹ thuật xuất hiện rõ ràng trong văn bản CV sau.
Chỉ trả về JSON dạng {{"skills": ["Python", "SQL"]}}. Không suy đoán kỹ năng không có trong văn bản.
CV: {text[:60000]}'''
    result = generate_json(prompt)
    return list(dict.fromkeys(str(item).strip() for item in result.get('skills', [])
                              if str(item).strip()))[:80]
