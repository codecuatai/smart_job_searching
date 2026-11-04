# Một file cấu hình: .env tại gốc

Dự án chỉ có **một file `.env` thực ở gốc repository**. Không có `.env.example`, `.env.local` hoặc file env riêng cho web/API/AI.

```powershell
npm run env:init
# hoặc npm run setup
```

Lệnh tạo `.env` nếu thiếu và không ghi đè cấu hình đang có. Giá trị mặc định được quản lý bằng mã nguồn trong `scripts/lib/env.mjs`; clone mới không cần lấy file bí mật từ Git.

## Các biến

| Biến | Mặc định khi tạo mới | Ý nghĩa |
| --- | --- | --- |
| COMPOSE_PROJECT_NAME | unitalent | Tên project Compose |
| WEB_PORT | 3000 | Cổng web local và cổng Docker được công bố trên localhost |
| API_PORT | 8000 | Cổng API local / nội bộ container |
| AI_PORT | 8001 | Cổng AI local / nội bộ container |
| SEED_DEMO | true | Tạo tài khoản và tin minh họa nếu chưa có |
| DEMO_PASSWORD | demo12345 | Mật khẩu chỉ áp dụng khi tạo tài khoản seed mới |
| COOKIE_SECURE | false | true khi dùng HTTPS |
| DATA_VOLUME | unitalent_data | Tên volume SQLite/CV Docker |
| DATA_VOLUME_EXTERNAL | false | true khi giữ lại một volume đã tồn tại, Compose không sở hữu/xóa volume này |

Biến tùy chọn, chỉ thêm vào cùng `.env` khi cần:

| Biến | Khi không đặt |
| --- | --- |
| API_URL | Web local suy ra `http://127.0.0.1:API_PORT`; Docker build dùng `http://api:API_PORT` |
| AI_SERVICE_URL | API local suy ra `http://127.0.0.1:AI_PORT`; Docker dùng `http://ai:AI_PORT` |
| ALLOWED_ORIGINS | Suy ra hai origin localhost/127.0.0.1 tại WEB_PORT |
| DATABASE_PATH | `var/data/unitalent.db` tính từ root; Docker cố định `/app/var/data/unitalent.db` trên volume |
| E2E_BASE_URL | `http://127.0.0.1:WEB_PORT` |
| PLAYWRIGHT_CHANNEL | Windows: msedge; Linux/macOS: Chromium bundled |
| SERVICE_HOST | Local Python: 127.0.0.1; Docker: 0.0.0.0 |
| WEB_HOST | Local web: 127.0.0.1; Docker: 0.0.0.0 |

Ví dụ đổi cổng bằng cách sửa chính `.env`:

```dotenv
WEB_PORT=3100
API_PORT=8100
AI_PORT=8101
```

Không phải gõ lại các URL tương ứng: dev script, Next config, Python entrypoints, Origin mặc định và E2E đều suy ra từ ba cổng này. Docker cũng nội suy các cổng và địa chỉ service từ cùng file.

## Cách cấu hình được nạp

- Node: `scripts/lib/env.mjs` tìm root theo vị trí file, dùng `process.loadEnvFile`; không phụ thuộc terminal đang đứng ở đâu.
- Web: lệnh dev/build/start gọi `scripts/web.mjs`; `next.config.mjs` cũng đọc cấu hình chung khi Next CLI được gọi trực tiếp.
- Python: `services/config.py` đọc root `.env` bằng python-dotenv; `python -m services.run api|ai` lấy cổng từ đó.
- Docker Compose tự đọc root `.env`, truyền danh sách biến cần thiết cho từng container. File `.env` không được copy vào image.
- Playwright đọc cùng module Node để lấy E2E_BASE_URL hoặc WEB_PORT.

Biến đã đặt trong môi trường tiến trình ưu tiên hơn `.env`, phù hợp CI/container. Các địa chỉ service nội bộ Docker do Compose sinh để tránh dùng localhost của container khác. Đây là giá trị runtime/build, không phải file cấu hình thứ hai.

## Sau khi đổi cấu hình

Local: dừng và chạy lại `npm run dev`. Docker: `docker compose up --build -d --wait`. Cần build lại web khi đổi API_PORT/API_URL vì Next rewrite được chốt lúc build. Đổi DATA_VOLUME sẽ chọn dữ liệu khác; không tự di chuyển dữ liệu giữa volume.

Trên máy đang tái cấu trúc, DATA_VOLUME được giữ là `unitalent-e2e_backend_data` và DATA_VOLUME_EXTERNAL=true để tiếp tục dùng database cũ. Không đổi chỉ để làm đẹp tên nếu chưa sao lưu/migrate. `.env` của clone mới mặc định dùng tên `unitalent_data`.

Mật khẩu seed không được cập nhật ngược vào tài khoản đã có. Nút demo trên giao diện dùng mật khẩu mặc định; nếu đổi DEMO_PASSWORD, đăng nhập bằng form với mật khẩu thực của tài khoản.

## Git

`.env`, `var/` và `artifacts/` bị bỏ qua. `.env` thật không được commit; scripts tạo lại mặc định cho máy mới. Không có biến NEXT_PUBLIC chứa thông tin bí mật.
