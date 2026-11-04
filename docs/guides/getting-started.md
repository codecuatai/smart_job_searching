# Chạy dự án từ đầu

Hướng dẫn này dành cho thành viên clone repository mới. UniTalent được thiết kế để chạy bằng Docker Compose; cách khuyến nghị không cần cài Python, virtualenv, package frontend hoặc trình duyệt trên máy host.

## Yêu cầu

- Docker Desktop đang chạy (Compose v2).
- Node.js 22 trở lên để gọi các script `npm` của repository.
- Git để clone source.
- Khoảng trống ổ đĩa cho image ứng dụng và image Playwright nếu chạy E2E lần đầu.

## Khởi động nhanh

```powershell
git clone <URL_REPOSITORY>
cd day8HeThongTimViecLamThongMinh
npm run env:init
npm run docker:up
```

Sau `npm run env:init`, mở `.env` ở thư mục gốc và điền:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Không commit `.env`. Script `docker:up` sẽ build web/API/AI, PostgreSQL warehouse, Metabase và worker BI, tạo volume dữ liệu và chờ healthcheck. Mở ứng dụng tại [http://127.0.0.1:3000](http://127.0.0.1:3000), Metabase tại [http://127.0.0.1:3001](http://127.0.0.1:3001). Nếu chưa điền key, hệ thống vẫn khởi động nhưng các tính năng Gemini (phân tích CV, lộ trình học tập, phỏng vấn) sẽ không hoạt động.

Kiểm tra trạng thái:

```powershell
npm run docker:ps
```

Các service phải hiển thị `healthy`. Xem log khi cần:

```powershell
npm run docker:logs
```

## Tài khoản demo

Khi `SEED_DEMO=true` (mặc định), hệ thống tạo dữ liệu minh họa nếu database còn trống. Có thể đăng nhập bằng:

```text
Sinh viên: nam.nguyen@hcmut.edu.vn
Nhà tuyển dụng: recruitment@vng.com.vn
Nhà tuyển dụng: talent@fptsoftware.com
Mật khẩu chung: demo12345
```

Seed có sẵn 3 ứng viên, avatar nội bộ, CV PDF minh họa, đơn ứng tuyển theo trạng thái và tin tuyển dụng mẫu. Mật khẩu chỉ được áp dụng lúc tài khoản seed được tạo lần đầu; đổi `DEMO_PASSWORD` không ghi đè mật khẩu đã tồn tại.

## Kiểm thử toàn bộ stack Docker

```powershell
npm run docker:test
```

Lệnh này build/khởi động ứng dụng, chờ healthcheck rồi chạy Playwright trong service `e2e` trên network Docker (`E2E_BASE_URL=http://web:3000`). Bộ hiện tại gồm 28 ca trên desktop và mobile. Kết quả được ghi tại:

- `artifacts/e2e/results.json` — kết quả máy đọc được.
- `artifacts/e2e/report/` — báo cáo HTML.
- `artifacts/e2e/results/` — screenshot/trace khi test lỗi.

Nếu đã cài dependencies của `apps/web` trên host, có thể mở report bằng:

```powershell
npm run test:e2e:report
```

## Dừng, khởi động lại và dữ liệu

```powershell
npm run docker:down    # dừng container, giữ volume dữ liệu
npm run docker:up      # build lại và khởi động
```

Database SQLite và CV nằm trong Docker volume `unitalent_data` trên clone mới. Không dùng `docker compose down --volumes` nếu cần giữ tài khoản, CV, tin tuyển dụng và đơn ứng tuyển.

## Cấu hình cổng và môi trường

Không cần tạo `.env` để chạy lần đầu. Khi cần đổi cổng, sửa `.env` ở root:

```dotenv
WEB_PORT=3000
API_PORT=8000
AI_PORT=8001
```

Các biến dữ liệu chính:

| Biến | Mặc định | Mục đích |
| --- | --- | --- |
| `SEED_DEMO` | `true` | Tạo dữ liệu demo khi database chưa có |
| `DEMO_PASSWORD` | `demo12345` | Mật khẩu tài khoản demo mới tạo |
| `DATA_VOLUME` | `unitalent_data` | Tên volume SQLite/CV |
| `DATA_VOLUME_EXTERNAL` | `false` | Dùng volume Docker đã tồn tại |
| `COOKIE_SECURE` | `false` | Đặt `true` khi chạy sau HTTPS |

`.env` là cấu hình máy cá nhân và không commit lên Git. Xem thêm [configuration.md](configuration.md).

## Chạy local không qua Docker (tùy chọn)

Chỉ dùng khi cần debug nhanh từng service:

```powershell
npm run setup
npm run dev
```

Cách này cần Python 3.12 và cài dependencies vào `.venv`. Không chạy local và Docker cùng lúc nếu dùng chung `WEB_PORT`, `API_PORT` hoặc `AI_PORT`.

## Xử lý lỗi thường gặp

| Triệu chứng | Cách xử lý |
| --- | --- |
| Docker daemon không kết nối được | Mở Docker Desktop, chờ trạng thái Running rồi chạy lại `npm run docker:up` |
| Cổng 3000 đã được sử dụng | Đổi `WEB_PORT` trong `.env`, sau đó chạy lại `npm run docker:up` |
| Container chưa healthy | Chạy `npm run docker:logs`; kiểm tra lần lượt `ai`, `api`, `web` |
| Volume external không tồn tại | Xóa `DATA_VOLUME_EXTERNAL=true` hoặc tạo đúng volume; script sẽ tự dùng volume nội bộ cho clone mới |
| E2E tải image lâu ở lần đầu | Bình thường; image Playwright được cache cho các lần sau |
| Đăng nhập demo không được | Tài khoản có thể đã tồn tại với mật khẩu khác; xem [api.md](api.md) hoặc đăng ký tài khoản mới |

## Các tài liệu liên quan

- [Kiến trúc](architecture.md)
- [Cấu hình](configuration.md)
- [Docker và sao lưu](deployment.md)
- [Kiểm thử E2E](e2e.md)
- [Hợp đồng API](api.md)
