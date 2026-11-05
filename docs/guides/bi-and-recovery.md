# Chạy ứng dụng, BI và sao lưu

## Máy clone mới

Cần Git, Node.js 22+ và Docker Desktop đang chạy (Linux containers), còn khoảng 4 GB RAM cho Docker. Không cần Python/PostgreSQL cài trên host nếu chỉ chạy Docker.

```powershell
npm run env:init
# Mở .env, điền GEMINI_API_KEY; giữ GEMINI_MODEL=gemini-3.5-flash-lite
npm run docker:up
```

Web: http://127.0.0.1:3000. Metabase: http://127.0.0.1:3001, dashboard **TH3 · AI & BI**. Lần đầu cần tải image và khởi tạo metadata, có thể mất vài phút. Script chờ tất cả healthcheck, gồm bootstrap dashboard.

Tài khoản Metabase local mặc định: `bi-admin@unitalent.local` / `Local-BI-Admin-4829!`. Đổi `BI_ADMIN_EMAIL`, `BI_ADMIN_PASSWORD` trước lần tạo volume đầu tiên để dùng tài khoản riêng. Khi đã tạo, việc đổi env không tự đổi mật khẩu tài khoản Metabase. Đổi mật khẩu trong Metabase. Các mật khẩu mẫu chỉ dành cho máy local, các cổng được bind loopback. Chỉ người vận hành BI dùng tài khoản này; tài khoản recruiter trong web không tự trở thành admin Metabase.

`SEED_DEMO=true` thêm 4 job mẫu có nhãn demo. Dữ liệu crawl trên máy dev **không nằm trong image/Git**. Sau khi clone, nhập file crawl hợp lệ bằng `npm run jobs:import -- --input <file> --target docker` theo [hướng dẫn dữ liệu](job-crawler.md); không hứa máy clone có sẵn 635 tin ITviec. TopCV bị 403 ở lần crawl đã ghi nhận, chưa có dữ liệu TopCV và không gán nhãn giả.

## Mart và định nghĩa số liệu

SQLite vẫn giữ tài khoản, CV BLOB, đơn và coaching. Worker `bi` lấy consistent backup snapshot, thay facts trong một transaction PostgreSQL mỗi 60 giây. Advisory lock ngăn hai lần refresh chồng nhau; dữ liệu ngày quan sát upsert theo `(job_id,day)`. Không suy diễn biến động trước ngày bắt đầu snapshot.

- `fact_job`: một job hiện có, salary hai cận/tiền tệ/kỳ; `bridge_job_skill`: một job–skill.
- `fact_candidate_skill`: một người đã ẩn danh–skill, cộng hợp hồ sơ khai báo và CV hiện hành đã xác nhận. Không cộng trùng nhiều CV/đơn.
- `fact_application_stage`: một đơn ẩn danh–giai đoạn từng đạt. Qua giai đoạn sau được xem đã đạt các bước trước; các bước suy ra dùng thời điểm sự kiện tiếp theo. Không phải thời điểm ứng viên thực sự được xem nếu chưa có sự kiện đó.
- `job_observations`: một job–ngày quan sát; `dim_time`: một ngày; `refresh_status`: trạng thái transaction ETL mới nhất.
- `bi_skill_supply/demand`, `bi_salary_trend/monthly`, `bi_hiring_funnel`, `bi_quality`: view tổng hợp cho Metabase. Role `bi_reader` chỉ SELECT các view và refresh status, không đọc fact/raw CV hoặc ghi dữ liệu.

Metabase app metadata nằm trong database `metabase`, do role `metabase_app` sở hữu. Mart ở `unitalent_analytics`. CV/email/tên/số điện thoại không được ETL sang mart. Mỗi câu hỏi có tham số dataset `real` mặc định; `demo`/`test` chỉ để minh họa/kiểm thử. Funnel Metabase là **tổng hợp toàn bộ mẫu**; funnel riêng trong web chỉ gồm các job do recruiter đang đăng nhập sở hữu. Không public embedding.

Web hỗ trợ lọc thị trường theo dataset, ngày đăng, ngành, địa điểm, nguồn; CSV cùng filter. Nguồn cung kỹ năng là toàn bộ ứng viên trong dataset, không suy ra ứng viên cư trú ở địa điểm của job. Funnel web hiện all-time theo owner, được ghi rõ và không áp dụng filter thị trường. Lương là trung vị midpoint của các khoảng có đủ hai cận, tách USD/VND và tháng/năm/giờ; chưa quy đổi FX. Thiếu ngày đăng không đưa vào biểu đồ thời gian. Chưa đủ hai kỳ thì không kết luận xu hướng. Tin thiếu expiry được ghi unknown, không coi là xác nhận còn tuyển.

```powershell
npm run bi:refresh
npm run docker:ps
npm run docker:logs
```

## Test tách dữ liệu nghiệp vụ

```powershell
npm run docker:test
```

Tạo project `unitalent-test`, volume `unitalent-test_api_data`, warehouse riêng; web :3100, BI :3101. Mỗi lần `docker:test` sẽ xóa đúng các volume của project test rồi tạo mới; không đụng `DATA_VOLUME` nghiệp vụ và không xóa CV thật. Mặc định offline dùng provider fixture cho sinh nội dung, không cần key. Đặt `E2E_AI_MODE=live` để gọi Gemini thật; lỗi upstream làm ca live thất bại. Container/network test tự dọn trong `finally`. Báo cáo tại `artifacts/e2e`. `E2E_PROJECT_NAME` phải là `unitalent-test` hoặc `unitalent-test-<suffix>`; có thể đổi `E2E_WEB_PORT`, `E2E_BI_PORT`.

## Backup và restore

```powershell
npm run db:backup
npm run db:verify-recovery
# Chọn đúng backup, lệnh tiếp theo thay dữ liệu nghiệp vụ bằng bản đó:
npm run db:restore -- var/backups/<timestamp>/unitalent.db
```

Backup lưu trong `var/backups/<timestamp>`: SQLite consistent backup và `pg_dump -Fc` của cả hai PostgreSQL databases. Đây là dữ liệu riêng tư, không commit. Restore SQLite dừng web/API/ETL, kiểm tra integrity/schema, lưu bản hiện tại vào volume với hậu tố `.pre-restore`, khôi phục rồi khởi động lại. Worker xây lại mart từ SQLite. Không chạy restore trên dữ liệu đang có thay đổi cần giữ.

`db:verify-recovery` kiểm thử SQLite backup/restore vào hai file tạm (integrity và số bản ghi), dump/restore mart PostgreSQL vào database tạm và đối chiếu counts. Script tự dọn bản sao; không dừng hoặc ghi đè database nghiệp vụ. Chưa thay thế diễn tập khôi phục toàn bộ máy, Metabase metadata và volumes trên host mới.

Khi mất cả volume PostgreSQL: tạo lại warehouse bằng Compose, dừng `bi metabase`, dùng `pg_restore --clean --if-exists -U postgres -d <database>` với file dump tương ứng bên trong container warehouse, sau đó bật lại `metabase bi`. Hai database/roles phải được bootstrap trước; giữ cùng bộ mật khẩu của backup. Khi chỉ mất mart, có thể bỏ qua restore mart và để ETL tái tạo; lịch sử `job_observations` cũ cần dump để phục hồi.

`docker:down` không xóa volumes. Không dùng `down --volumes` cho môi trường nghiệp vụ khi chưa có backup đã kiểm tra.
