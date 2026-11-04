# Triển khai và sao lưu

## Một cấu hình cho local và Docker

Chạy `npm run setup` hoặc `npm run env:init` để tạo `.env` gốc. Mọi thành phần đọc cùng file; không tạo file env trong apps/services. Xem [configuration.md](configuration.md).

Local: `npm run dev`. Chạy riêng từ root: `python -m services.run api --reload`, `python -m services.run ai --reload`, `npm --prefix apps/web run dev` (chọn đúng Python trong .venv).

Build web: `npm run build`; chạy bằng `npm --prefix apps/web start` khi API/AI đang chạy. API_URL/API_PORT được Next đóng vào rewrite lúc build, cần build lại nếu thay đổi. Build font cần truy cập Google Fonts.

## Docker Compose

Cách chạy khuyến nghị cho thành viên trong team được ghi đầy đủ ở [getting-started.md](getting-started.md). Tóm tắt:

```powershell
docker compose config --quiet
npm run docker:up
npm run docker:ps
npm run docker:logs
npm run docker:down
```

Kiểm thử production stack bằng Playwright trong Docker:

```powershell
npm run docker:test
```

Service `web` công bố duy nhất WEB_PORT trên localhost. `api` và `ai` nằm trong mạng Docker. Cả ba có healthcheck. API dùng `http://ai:AI_PORT`; web build proxy tới `http://api:API_PORT`. Các giá trị được tạo từ root .env. Không copy .env vào image; web không nhận mật khẩu seed.

Dữ liệu ở volume `api_data`, tên thực lấy từ `DATA_VOLUME`. `DATA_VOLUME_EXTERNAL=true` dành cho volume đã tồn tại; Compose không tạo/xóa volume external. Bản cấu hình trên máy này giữ volume cũ để bảo toàn dữ liệu. Fresh clone mặc định tạo volume `unitalent_data`. Không dùng `down --volumes` khi cần giữ dữ liệu.

Dockerfile chạy bằng user không phải root. `.dockerignore` bỏ media, env, var, artifacts, node_modules, cache và công cụ agent khỏi build context. Source ứng dụng dùng đường dẫn apps/web, services/api và services/ai.

## Sao lưu local

SQLite mặc định `var/data/unitalent.db`, chứa cả CV. Dừng API trước khi sao chép file; hoặc dùng SQLite backup API để tạo snapshot nhất quán khi chạy:

```python
import sqlite3
from pathlib import Path
root = Path.cwd()  # Chạy tại root repository.
source = sqlite3.connect(root / 'var/data/unitalent.db')
backup = Path.home() / 'UniTalentBackups' / 'unitalent-backup.db'
backup.parent.mkdir(parents=True, exist_ok=True)
target = sqlite3.connect(backup)
source.backup(target)
target.close()
source.close()
```

Để phục hồi: dừng API, giữ bản hiện tại, chép backup vào DATABASE_PATH, khởi động lại và kiểm tra tài khoản/đơn/CV. Với Docker, dùng SQLite backup từ container hoặc thao tác trên volume sau khi dừng API; không copy database đang ghi bằng lệnh file thông thường. DB backup chứa dữ liệu cá nhân, không commit hoặc chia sẻ cùng source.

## Trước khi chạy công khai

MVP đã kiểm thử local/Docker, chưa phải hệ thống production hoàn chỉnh. Cần HTTPS/COOKIE_SECURE, ALLOWED_ORIGINS theo domain, tắt demo, rate limit/login/upload limits, xử lý PDF cách ly, xác minh/khôi phục tài khoản, quản lý/xóa dữ liệu cá nhân, migrations, logging/monitoring và kiểm tra dependency theo thời điểm triển khai. Giữ dịch vụ AI trong mạng nội bộ.
