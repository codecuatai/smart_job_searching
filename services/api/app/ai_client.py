import httpx
from fastapi import HTTPException
from services.config import ai_url


def ai_request(path, body=None):
    try:
        with httpx.Client(base_url=ai_url(), timeout=15) as client:
            response = client.get(path) if body is None else client.post(path, json=body)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as error:
        if 400 <= error.response.status_code < 500:
            raise HTTPException(error.response.status_code, 'Yêu cầu AI không hợp lệ hoặc câu hỏi không tồn tại.') from error
        raise HTTPException(503, 'Dịch vụ AI trả lỗi. Vui lòng thử lại.') from error
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(503, 'Dịch vụ AI chưa sẵn sàng. Hãy kiểm tra địa chỉ AI_SERVICE_URL và tiến trình AI.') from error
