"""Validate uploaded PDFs independently from optional text extraction."""
import io
import logging

from fastapi import HTTPException
from pypdf import PdfReader

logger = logging.getLogger(__name__)
MAX_RESUME_BYTES = 5 * 1024 * 1024


def read_resume_pdf(content: bytes, name: str) -> tuple[str, str]:
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(413, 'CV tối đa 5 MB.')
    if not content:
        raise HTTPException(422, 'File PDF rỗng. Vui lòng chọn lại file CV.')
    if not name.lower().endswith('.pdf'):
        raise HTTPException(422, 'Vui lòng chọn tệp PDF hợp lệ.')
    # Some exporters prepend a BOM or whitespace. Let the parser validate the
    # structure instead of rejecting an otherwise readable PDF at byte zero.
    if b'%PDF-' not in content[:1024]:
        raise HTTPException(422, 'Vui lòng chọn tệp PDF hợp lệ. Nội dung file không có định dạng PDF.')
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        # PDF permission restrictions may encrypt a file without an opening
        # password. These documents can be opened with the empty user password.
        if reader.is_encrypted and not reader.decrypt(''):
            raise HTTPException(422, 'PDF yêu cầu mật khẩu để mở. Hãy xuất bản PDF không khóa rồi tải lại.')
        page_count = len(reader.pages)
        if page_count == 0:
            raise HTTPException(422, 'PDF không có trang nội dung. Vui lòng xuất lại CV.')
        if page_count > 30:
            raise HTTPException(422, f'CV tối đa 30 trang; file này có {page_count} trang.')
    except HTTPException:
        raise
    except Exception as error:
        logger.warning('Resume PDF validation failed: %s', type(error).__name__)
        raise HTTPException(422, 'Không đọc được cấu trúc PDF. Hãy dùng chức năng Xuất PDF hoặc In thành PDF rồi tải lại.') from error

    texts = []
    extraction_failed = False
    for page in reader.pages:
        try:
            texts.append((page.extract_text() or '')[:10000])
        except Exception as error:
            # A font/encoding extraction failure must not discard a valid CV.
            logger.warning('Resume text extraction failed: %s', type(error).__name__)
            extraction_failed = True
    text = '\n'.join(texts)[:60000]
    warning = ''
    if extraction_failed:
        warning = 'CV đã lưu nhưng chưa đọc được toàn bộ văn bản. Hãy bổ sung kỹ năng trong hồ sơ hoặc xuất lại PDF để ghép việc chính xác hơn.'
    elif not text.strip():
        warning = 'CV đã lưu nhưng PDF không có lớp văn bản (có thể là bản scan). Hãy bổ sung kỹ năng trong hồ sơ để ghép việc.'
    return text, warning
