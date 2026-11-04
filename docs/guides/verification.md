# Kết quả kiểm tra sau tái cấu trúc — 04/11/2026

## Kết quả mới nhất

| Kiểm tra | Kết quả |
| --- | --- |
| Cấu trúc source | apps/web, services/api, services/ai; không còn frontend/backend/ai/tools ở root |
| Cấu hình | Chỉ còn `.env` gốc, không có file env mẫu hoặc env riêng của web/service |
| Đổi cổng bằng file | Chỉ sửa `.env` sang 3100/8100/8101; dev script, web proxy, API, AI và Origin đều hoạt động |
| Dữ liệu local | Database đã chuyển sang var/data; đăng nhập và việc làm seed vẫn đọc được |
| Pytest | 10/10 ca qua |
| ESLint / TypeScript | Qua |
| Docker production build | Qua, npm audit trong image báo 0 lỗ hổng |
| Docker runtime | Project unitalent, các service web/api/ai đều healthy |
| E2E trình duyệt thật trong Docker | 8/8 ca qua trong 17,8 giây; 0 skipped/failed/flaky, không retry |
| Matching model fixture | hybrid-v2, 10 mẫu, accuracy 0,8000, macro-F1 0,7487 |
| Đường dẫn Markdown | Mọi local link trong hướng dẫn/README đã được kiểm tra |

E2E dùng Playwright 1.64.1 trong image Docker, Chromium headless ở desktop 1440×900 và mobile 390×844, gọi server production thật qua `http://web:3000`. Kiểm tra đăng ký/login/logout, role guard, lưu phiên, PDF giả/hợp lệ, lưu CV, đăng tin, matching, nộp/chặn trùng, tải đúng CV đã nộp bằng SHA-256, kỹ năng thiếu đổi 1 → 0, lịch hẹn, lịch sử luyện phỏng vấn và CSV analytics export. Lần chạy xác nhận mới nhất đã sửa Origin nội bộ Compose, migration skill index và race condition upload CV; không còn lỗi 403 khi đăng nhập/đăng ký hoặc lỗi thay CV. Không thay đổi media cá nhân.

Pytest hiện vẫn có một deprecation warning từ Starlette TestClient về httpx (phụ thuộc upstream, không làm test thất bại); 10 test đều qua. CI workflow đã cập nhật đường dẫn mới và có job E2E, chưa có kết quả CI trên GitHub vì chưa push.

## Dữ liệu và cấu hình được giữ

`.env` hiện đặt COMPOSE_PROJECT_NAME=unitalent, tham chiếu DATA_VOLUME=unitalent-e2e_backend_data với external=true. Điều này giữ nguyên dữ liệu Docker cũ dù service backend đổi tên thành api. Local dùng var/data/unitalent.db. Cấu hình cổng thử nghiệm đã được trả lại giá trị ban đầu sau smoke test.

Kết quả E2E hiện ở `artifacts/e2e/results.json`, báo cáo HTML tại `artifacts/e2e/report/index.html`. Chạy `npm run test:e2e:report` để mở server báo cáo. Source test ở `apps/web/e2e`, config ESM ở `apps/web/playwright.config.mjs`.

## Nội dung dọn dẹp

Đã bỏ file env mẫu trùng trong ứng dụng web; root `.env.example` hiện là template duy nhất và không chứa secret. Dọn 15 đích cache/render/dữ liệu thử/ảnh trùng ra khỏi dự án, có backup ở:

```text
C:\Users\admin\.codex\backups\unitalent-layout-cleanup-20261028-115119
```

Bảng đổi tên và lý do ở [project-layout.md](project-layout.md), manifest ở `artifacts/layout-cleanup.json`. Báo cáo DOCX gốc, video và phụ đề cá nhân được giữ; ba ảnh trùng đã đối chiếu SHA-256 với bản chính trước khi dọn.

## Backup Git cũ

Không tạo Git gốc hoặc push thay người dùng. Metadata Git frontend từ lần trước vẫn ở ngoài workspace:

```text
C:\Users\admin\.codex\backups\unitalent-frontend-git-20261028-110936\
├── frontend-git.zip        43 file metadata, archive đã kiểm tra CRC
├── frontend.git.original  Metadata gốc đã chuyển ra
└── GIT_BACKUP_LOCATION.txt
```

`.env`, media/, var/, artifacts/ và cache được bỏ qua; Git guard chặn cả khi cố tình stage những dữ liệu riêng này. Chỉ ảnh tài nguyên apps/web/public và docs/diagrams được cho phép. Đây là kiểm chứng phạm vi local/Docker, không phải chứng nhận vận hành production.
