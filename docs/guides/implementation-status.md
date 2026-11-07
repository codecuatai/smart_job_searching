# Trạng thái triển khai

Mốc cập nhật: **06/11/2026**. Bản TH3 có cấu hình Docker với ứng dụng, PostgreSQL mart, Metabase và worker ETL. [Yêu cầu/ERD](requirements-and-data.md), [vận hành](bi-and-recovery.md), [benchmark](../../data/evaluation/README.md), [nghiệm thu TH3](../reports/release-implementation-2026-11-05.md), [tư vấn CV–JD mới](../reports/cv-review-implementation-2026-11-06.md).

| Chức năng | Hiện trạng |
| --- | --- |
| Frontend Next.js nhiều vai trò | Đã nối API, có trạng thái tải/lỗi, bảo vệ trang theo vai trò |
| Đăng ký / đăng nhập / đăng xuất | Chạy thật, password hash, session SQLite, cookie HttpOnly |
| Chỉnh hồ sơ / CV PDF | Chạy thật, giới hạn 5 MB / 30 trang, text extraction |
| Đăng tin tuyển dụng | Lưu SQLite, công ty/owner lấy từ tài khoản đăng nhập |
| Tìm kiếm / lọc jobs và candidates | API search/filter/page, pageSize tối đa 100; UI 20 bản ghi/trang; cache matching 60s |
| Ghép việc | Hybrid-v2 + cv-evidence-v4; CV-first coverage, kinh nghiệm khi JD có yêu cầu rõ, raw/final score và adjustments; giữ context CV sau xác nhận; chưa có gold validation |
| Ứng tuyển / tải CV | Chạy thật, unique một đơn/job/student, CV snapshot |
| Pipeline / lịch phỏng vấn | Chạy thật trong ứng dụng; refresh để nhận dữ liệu mới |
| Lộ trình kỹ năng | Gemini tạo kế hoạch theo kỹ năng hồ sơ/CV, JD và giờ học/tuần; lưu kế hoạch và checklist theo tài khoản/job; không dự đoán cứng điểm tương lai |
| Phỏng vấn | Gemini sinh bộ câu hỏi theo hồ sơ/job và chấm nguyên câu hỏi đã lưu; lưu lịch sử. Bộ câu hỏi tham khảo vẫn có sẵn, được ghi nhãn rõ |
| BI | Web filters/CSV, ứng viên duy nhất, lương median theo tháng/currency/period, funnel owner; PostgreSQL ETL + Metabase 6 câu hỏi/dashboard |
| Phân tích CV / scan | Gemini schema có evidence, sửa/xác nhận, OCR Poppler/Tesseract eng+vie tối đa 3 trang; giữ file khi AI/OCR lỗi |
| Tư vấn CV theo JD — 06/11 | Chọn CV/JD cụ thể, snapshot bất biến, gap có bằng chứng/phân biệt tự khai báo, Outline Gemini sửa/lưu/revision, BI aggregate real, xuất Markdown, kịch bản và checklist tự xác nhận. [Hướng dẫn](cv-review.md). Video/nộp bài do người học thực hiện |
| GitHub AST / SOLID / vulnerability scan | Chưa triển khai; không dùng chỉ số mock để xác minh ứng viên |
| Phát hiện đạo văn / xác minh commit | Chưa triển khai |
| Quy đổi đồ án thành số năm kinh nghiệm | Ghi chú JD, chưa có mô hình kiểm định |
| Gemini LLM | `gemini-3.5-flash-lite`: tạo lộ trình, tạo/chấm câu hỏi phỏng vấn, endpoint trích xuất kỹ năng. Lộ trình và câu hỏi AI trả lỗi rõ khi Gemini không khả dụng, không thay bằng mẫu tĩnh |
| Voice STT/TTS thời gian thực | Chưa triển khai; bỏ thao tác thu âm giả của prototype |
| Email / Calendar tự động | Chưa tích hợp; lịch chỉ lưu trong DB |
| ETL / Mart | PostgreSQL, facts job/skill/candidate/stage và daily observations, view tổng hợp read-only; không dùng ClickHouse |
| Docker Compose | web/api/ai/warehouse/metabase/bi; bootstrap 2 lệnh, test project/volume riêng; backup SQLite + 2 PostgreSQL DB |
| Benchmark độc lập split | 576 synthetic pairs, 512/32/32, ID-disjoint; validation chọn model, held-out + ablation/errors/latency. Gold human labels = 0, chưa xác nhận chất lượng thực tế |
| Production quy mô lớn | Cần hardening, migrations, rate limit, quan sát và vận hành |
| UI workspace 05/11 | CV/analysis lên đầu, PDF preview, evidence chips, jobs gọn/lọc URL, recruiter mobile filter, BI top skills/sample warning; chưa tách toàn bộ globals thành module |
| CI/E2E 05/11 | Offline Docker E2E bắt buộc, fixture chỉ trong APP_ENV=test; live Gemini riêng khi có key; cleanup trong finally; recovery verification trên bản sao |

Các báo cáo DOCX và hình sơ đồ cũ được giữ nguyên như tài liệu học thuật. Nếu trình bày báo cáo, nói rõ phần đã triển khai theo bảng này, không trình bày điểm AST/voice hoặc số liệu thị trường mẫu như kết quả đo thực tế.
