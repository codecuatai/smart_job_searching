import httpx
import os
import hashlib
import json
import threading
import time
from collections import OrderedDict
from copy import deepcopy
from fastapi import HTTPException
from services.config import ai_url

_matches = OrderedDict()
_lock = threading.Lock()


def ai_request(path, body=None):
    cache_key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() if path == '/match' else None
    if cache_key:
        with _lock:
            saved = _matches.get(cache_key)
            if saved and time.monotonic()-saved[0] < 60:
                return deepcopy(saved[1])
    try:
        try:
            timeout = max(35, float(os.getenv('GEMINI_TIMEOUT_SECONDS', '25')) + 10)
        except ValueError:
            timeout = 35
        result = None
        for attempt in range(1):
            try:
                with httpx.Client(base_url=ai_url(), timeout=timeout) as client:
                    response = client.get(path) if body is None else client.post(path, json=body)
                    response.raise_for_status()
                    result = response.json()
                    break
            except httpx.HTTPStatusError as error:
                raise
            except httpx.HTTPError:
                # The AI service owns the bounded Gemini retry. Retrying a
                # timed-out upstream call here can exceed the web proxy timeout
                # and turn a clean 503 into a socket reset.
                raise
        if result is None:
            raise ValueError('AI returned no result')
        if cache_key:
            with _lock:
                _matches[cache_key] = (time.monotonic(), deepcopy(result))
                _matches.move_to_end(cache_key)
                while len(_matches) > 16:
                    _matches.popitem(last=False)
        return result
    except httpx.HTTPStatusError as error:
        if 400 <= error.response.status_code < 500:
            raise HTTPException(error.response.status_code, 'Yêu cầu AI không hợp lệ hoặc câu hỏi không tồn tại.') from error
        raise HTTPException(503, 'Dịch vụ AI trả lỗi. Vui lòng thử lại.') from error
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(503, 'Dịch vụ AI chưa sẵn sàng. Hãy kiểm tra địa chỉ AI_SERVICE_URL và tiến trình AI.') from error
