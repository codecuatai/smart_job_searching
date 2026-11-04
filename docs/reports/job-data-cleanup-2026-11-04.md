# Dọn job E2E và hiển thị dữ liệu ITviec

Ngày: 04/11/2026. Ứng dụng: UniTalent trong repository `day8HeThongTimViecLamThongMinh`.

## Nguyên nhân

- Workflow E2E tạo job `E2E Python SQL <token>` nhưng không xóa trong `finally`.
- Crawler đã có 634 tin ITviec trong `var/data/crawled-jobs.json` và SQLite local.
  API Docker dùng SQLite riêng trong volume `unitalent-e2e_backend_data`, nên
  dữ liệu local không xuất hiện ở giao diện đang chạy bằng Docker.
- Khi nhập đủ dữ liệu vào Docker, API gửi hơn 500 tin trong một request chấm
  điểm; service AI giới hạn 500 và trả 422. Cần chia batch, không bỏ bớt tin.
- TopCV trả HTTP 403 tại `https://www.topcv.vn/sitemap.xml` khi kiểm tra trực
  tiếp từ máy này. Chưa có tin TopCV trong dữ liệu nhập.

## Đã xử lý

| Database | Trước | Sau |
| --- | --- | --- |
| Docker API | 4 job mẫu + 18 job E2E | 4 job mẫu + 634 tin ITviec |
| Local | 4 job mẫu + 13 job E2E + 634 tin ITviec | 4 job mẫu + 634 tin ITviec |

Mỗi lần xóa/import đều tạo SQLite backup trước khi ghi, trong `var/data/backups`
của target tương ứng. Chỉ xóa khi title, company cùng token và email recruiter
đều khớp fixture. Xóa 18 ứng tuyển test liên quan trong Docker và 13 trong
local; giữ tài khoản, profile và CV.

Thay đổi code:

- `services/api/app/job_maintenance.py`: thao tác có backup, cleanup fixture
  và import theo URL ổn định bằng upsert; tái import không xóa ứng tuyển hoặc
  đổi chủ sở hữu tin đã tồn tại, chỉ mục kỹ năng được cập nhật.
- `scripts/manage-jobs.mjs`: chọn `auto/local/docker`, in target trước khi ghi;
  chọn Docker tường minh mà container không chạy sẽ báo lỗi.
- `scripts/crawl-jobs.mjs`: `--import-db` chuyển file JSON sang đúng target.
- `DELETE /api/jobs/{id}`: chỉ recruiter sở hữu job được xóa; cleanup E2E gọi
  endpoint này trong `finally`.
- API danh sách chấm điểm từng nhóm tối đa 500 rồi xếp hạng tất cả tin.

## Kiểm tra

- 11 API tests passed, gồm quyền xóa, giữ CV khi xóa job, chọn đúng fixture,
  backup, upsert giữ ứng tuyển/chủ sở hữu, đồng bộ skill và xếp hạng 501 tin.
- TypeScript typecheck và syntax check các wrapper Node passed.
- API Docker thật trả 638 tin cho tài khoản ứng viên: 634 `source=itviec`,
  4 tin mẫu; không còn job E2E. `PRAGMA foreign_key_check` không có lỗi.
- Workflow tuyển dụng E2E desktop chạy thành công và xóa job vừa tạo sau khi
  kết thúc. Sau test, API và DOM vẫn có đúng 638 tin, không còn job E2E.
- Chrome headless xác nhận 638 `.job-row`, tiêu đề tin ITviec có trên trang,
  không có page error. Ảnh và số liệu nằm trong thư mục đã ignore
  `artifacts/jobs-data-2026-11-04/`.
- Nguồn ITviec mẫu trả HTTP 200 và có JobPosting; TopCV trả HTTP 403. Không tạo
  dữ liệu thay thế để báo nguồn TopCV đã có tin.

Lệnh sử dụng được ghi tại [hướng dẫn crawler](../guides/job-crawler.md).
