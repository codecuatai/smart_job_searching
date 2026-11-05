"""Safe public errors: no prompts, upstream URLs or keys cross this boundary."""
import logging
import uuid
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from .gemini import settings


def unavailable(error):
    request_id = uuid.uuid4().hex[:12]
    code, message, retryable = 'provider-unavailable', 'Dịch vụ Gemini đang bận. Vui lòng thử lại sau.', True
    if not settings()['configured'] or not settings()['enabled']:
        code, message, retryable = 'ai-not-configured', 'Chưa cấu hình hoặc chưa bật Gemini. Kiểm tra GEMINI_API_KEY.', False
    elif isinstance(error, httpx.TimeoutException):
        code, message = 'provider-timeout', 'Gemini xử lý quá thời gian. Nội dung của bạn vẫn được giữ; hãy thử lại.'
    elif isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status == 429:
            code, message = 'provider-quota', 'Gemini đang giới hạn lượt gọi hoặc hết hạn mức. Vui lòng thử lại sau.'
        elif status in (400, 401, 403, 404):
            code, message, retryable = 'provider-configuration', 'Gemini từ chối cấu hình key/model. Kiểm tra cấu hình dịch vụ.', False
    elif isinstance(error, (ValueError, ValidationError)):
        code, message = 'provider-invalid-output', 'Kết quả AI chưa đúng định dạng. Vui lòng thử lại.'
    logging.getLogger(__name__).warning('AI request=%s code=%s', request_id, code)
    return HTTPException(503, dict(code=code, message=message, retryable=retryable, requestId=request_id),
                         headers={'Retry-After':'5'} if retryable else None)
