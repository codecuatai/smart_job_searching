# Báo cáo BI và dữ liệu phân tích

## Metric đang chạy

Dashboard recruiter lấy metric owner-scoped từ SQLite qua `GET /api/analytics` và cung cấp CSV qua `GET /api/analytics/export.csv`; Metabase đọc các view aggregate-only trong PostgreSQL mart.

- **Skill demand**: tỷ lệ tin có nhãn kỹ năng.
- **Skill supply**: tỷ lệ sinh viên khai báo nhãn kỹ năng.
- **Shortage**: `max(0, demandPercentage - supplyPercentage)`.
- **Salary**: median midpoint của khoảng lương có đủ hai cận, tách currency/period; các tin “thỏa thuận”, một phía hoặc mơ hồ không được tính.
- **Hiring funnel**: số hồ sơ đã đạt từng stage và tỷ lệ so với stage trước.

Dashboard hiển thị dữ liệu trong hệ thống, không đại diện thống kê lao động toàn thị trường. Job crawl có `source`, `sourceUrl` và `importedAt`; dữ liệu crawl phải được kiểm tra quyền sử dụng trước khi công khai.

## Kiểm chứng

- Analytics được gọi trong E2E workflow recruiter.
- CSV export được kiểm tra status `200` và `text/csv` trong E2E.
- Funnel lấy lịch sử từ bảng `application_stage_events`.
- CSDL có các bảng chuẩn hóa `skills`, `candidate_skills`, `job_skills`, `resume_extractions` và `model_predictions` để mở rộng ETL/data mart.

## Giới hạn hiện tại

Đã chạy PostgreSQL + Metabase v0.64.1 trong Docker, worker ETL 60 giây, 6 câu hỏi/dashboard bootstrap idempotent. Role bi_reader chỉ SELECT các view tổng hợp; metadata Metabase ở database riêng. `npm run bi:verify` đối soát supply/median/month/currency với SQLite, kiểm tra idempotency và quyền. [Grain/định nghĩa/sao lưu](../guides/bi-and-recovery.md). Lịch sử bắt đầu từ ngày quan sát, không tạo giả dữ liệu quá khứ. Nguồn real/demo/test tách biệt; nguồn cung đếm DISTINCT người theo canonical skills, có cả CV đã xác nhận; median midpoint lương theo tháng/ngành, tách tiền tệ/kỳ. Mẫu hiện tại không đại diện toàn thị trường.
