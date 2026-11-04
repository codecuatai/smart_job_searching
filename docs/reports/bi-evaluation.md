# Báo cáo BI và dữ liệu phân tích

## Metric đang chạy

Dashboard recruiter lấy dữ liệu từ SQLite qua `GET /api/analytics` và cung cấp CSV qua `GET /api/analytics/export.csv`.

- **Skill demand**: tỷ lệ tin có nhãn kỹ năng.
- **Skill supply**: tỷ lệ sinh viên khai báo nhãn kỹ năng.
- **Shortage**: `max(0, demandPercentage - supplyPercentage)`.
- **Salary**: khoảng lương trung bình phân tích được từ nội dung tin; các tin “thỏa thuận” không được tính.
- **Hiring funnel**: số hồ sơ đã đạt từng stage và tỷ lệ so với stage trước.

Dashboard hiển thị dữ liệu trong hệ thống, không đại diện thống kê lao động toàn thị trường. Job crawl có `source`, `sourceUrl` và `importedAt`; dữ liệu crawl phải được kiểm tra quyền sử dụng trước khi công khai.

## Kiểm chứng

- Analytics được gọi trong E2E workflow recruiter.
- CSV export được kiểm tra status `200` và `text/csv` trong E2E.
- Funnel lấy lịch sử từ bảng `application_stage_events`.
- CSDL có các bảng chuẩn hóa `skills`, `candidate_skills`, `job_skills`, `resume_extractions` và `model_predictions` để mở rộng ETL/data mart.

## Giới hạn hiện tại

Đây là BI tích hợp trong ứng dụng, chưa phải kết nối tới Power BI/Tableau/Metabase. Khi cần dashboard self-service, có thể kết nối công cụ BI read-only vào data mart sau khi chuyển phần phân tích sang PostgreSQL.
