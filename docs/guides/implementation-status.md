# Trạng thái triển khai

Mốc cập nhật: **04/11/2026**. Phạm vi bàn giao: MVP full-stack chạy local, ba dịch vụ và tài liệu để phát triển tiếp.

| Chức năng | Hiện trạng |
| --- | --- |
| Frontend Next.js nhiều vai trò | Đã nối API, có trạng thái tải/lỗi, bảo vệ trang theo vai trò |
| Đăng ký / đăng nhập / đăng xuất | Chạy thật, password hash, session SQLite, cookie HttpOnly |
| Chỉnh hồ sơ / CV PDF | Chạy thật, giới hạn 5 MB / 30 trang, text extraction |
| Đăng tin tuyển dụng | Lưu SQLite, công ty/owner lấy từ tài khoản đăng nhập |
| Tìm kiếm / lọc jobs và candidates | Lọc tại frontend trên dữ liệu API; chưa phân trang server |
| Ghép việc | Hybrid-v2 logistic scorer có model artifact, skill coverage + cosine, fixture gán nhãn và script đánh giá; vẫn là baseline nhỏ, chưa đủ dữ liệu production |
| Ứng tuyển / tải CV | Chạy thật, unique một đơn/job/student, CV snapshot |
| Pipeline / lịch phỏng vấn | Chạy thật trong ứng dụng; refresh để nhận dữ liệu mới |
| Lộ trình kỹ năng | Sinh từ skills thiếu, checklist chỉ tồn tại khi mở trang |
| Phỏng vấn | Văn bản, bộ câu hỏi cố định, rubric từ khóa/độ dài, lưu lịch sử |
| BI | Dashboard kỹ năng, lương, funnel và CSV export; có bảng skill/prediction chuẩn hóa; chưa kết nối Power BI/Tableau/Metabase |
| Đọc PDF scan | Lưu được file nhưng không OCR; nhập kỹ năng thủ công |
| GitHub AST / SOLID / vulnerability scan | Chưa triển khai; không dùng chỉ số mock để xác minh ứng viên |
| Phát hiện đạo văn / xác minh commit | Chưa triển khai |
| Quy đổi đồ án thành số năm kinh nghiệm | Ghi chú JD, chưa có mô hình kiểm định |
| Gemini LLM | Đã tích hợp `gemini-3.5-flash-lite` cho interview evaluation và optional skill extraction; có fallback offline khi thiếu key/lỗi mạng |
| Voice STT/TTS thời gian thực | Chưa triển khai; bỏ thao tác thu âm giả của prototype |
| Email / Calendar tự động | Chưa tích hợp; lịch chỉ lưu trong DB |
| ClickHouse / ETL / Star Schema | Sơ đồ/đề xuất nghiên cứu; chưa phải hạ tầng chạy thực |
| Docker Compose | Đã build/chạy web/api/ai/e2e; có lệnh train/evaluate AI và kiểm tra luồng nghiệp vụ |
| Production quy mô lớn | Cần hardening, migrations, rate limit, quan sát và vận hành |

Các báo cáo DOCX và hình sơ đồ cũ được giữ nguyên như tài liệu học thuật. Nếu trình bày báo cáo, nói rõ phần đã triển khai theo bảng này, không trình bày điểm AST/voice hoặc số liệu thị trường mẫu như kết quả đo thực tế.
