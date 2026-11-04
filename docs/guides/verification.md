# Kết quả kiểm tra sau tái cấu trúc — 04/11/2026

## Kết quả mới nhất

| Kiểm tra | Kết quả |
| --- | --- |
| Cấu trúc source | apps/web, services/api, services/ai; không còn frontend/backend/ai/tools ở root |
| Cấu hình | `.env` gốc cho runtime; `.env.example` không chứa secret để clone mới cấu hình Gemini |
| Đổi cổng bằng file | Chỉ sửa `.env` sang 3100/8100/8101; dev script, web proxy, API, AI và Origin đều hoạt động |
| Dữ liệu local | Database đã chuyển sang var/data; đăng nhập và việc làm seed vẫn đọc được |
| Pytest | 43/43 ca qua |
| ESLint / TypeScript | Qua |
| Docker production build | Qua, npm audit trong image báo 0 lỗ hổng |
| Docker runtime | Project unitalent, web/api/ai/warehouse/metabase/bi đều healthy; health API và Metabase trả ok |
| E2E trình duyệt thật trong Docker | 28 ca (14 desktop + 14 mobile); vòng xác nhận sạch đạt 27/28 do một lần Gemini evaluate trả 503 tạm thời; chạy riêng lại ca đó đạt 1/1. Các ca CV analysis/OCR/matching explanation/Metabase đều qua. |
| Gemini coaching | Desktop/mobile tạo lộ trình và câu hỏi cá nhân hóa, lưu tiến độ sau reload, chấm câu hỏi bằng `gemini:gemini-3.5-flash-lite`; JSON và screenshot được đính kèm report |
| Dữ liệu sau test | SQLite integrity_check=ok; 639 job (635 ITviec + 4 demo), 0 job E2E |
| Matching model | Runtime giữ hybrid-v2; benchmark mới 576 synthetic pairs, candidate-v3 bị loại ở validation; gold human labels = 0 |
| Đường dẫn Markdown | Mọi local link trong hướng dẫn/README đã được kiểm tra |

E2E dùng Playwright 1.64.1 trong image Docker, Chromium headless ở desktop 1440×900 và mobile 390×844, gọi server production thật qua `http://web:3000` trong project test riêng. Kiểm tra đăng ký/login/logout, role guard, lưu phiên, PDF giả/hợp lệ, lưu CV, đăng tin, matching, nộp/chặn trùng, tải đúng CV đã nộp bằng SHA-256, kỹ năng thiếu đổi 1 → 0, lịch hẹn, lịch sử luyện phỏng vấn và CSV analytics export. Lần chạy xác nhận mới nhất đã sửa Origin nội bộ Compose, migration skill index và race condition upload CV; không còn lỗi 403 khi đăng nhập/đăng ký hoặc lỗi thay CV. Không thay đổi media cá nhân.

Phạm vi E2E gồm PDF rỗng/khóa mật khẩu/hạn chế quyền/31 trang/quá 5 MB/không có lớp chữ, BOM, giữ CV cũ khi upload thất bại, kiểm tra hash sau reload, validation và bộ lọc. Lộ trình Gemini có bài tập/tiêu chí hoàn thành và checklist lưu bền; không còn điểm tương lai gán cứng. Câu hỏi được Gemini tạo theo hồ sơ/job, chấm đúng câu đã lưu; UI retry khi provider transient 503. CV extraction có evidence/chỉnh sửa, scan OCR thật, matching explanation và 6 câu hỏi Metabase được kiểm tra. E2E dùng project/volume test mới mỗi lần, không làm bẩn dữ liệu nghiệp vụ.

Pytest hiện vẫn có deprecation warning từ Starlette TestClient về httpx và pytest-asyncio (phụ thuộc upstream, không làm test thất bại); 43 test backend/AI đều qua. `npm run typecheck`, `npm run lint`, Next production build, `npm run bi:verify` đều qua. CI có job benchmark và E2E yêu cầu `GEMINI_API_KEY`; chưa có kết quả CI trên GitHub vì chưa push.

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
