# API — services/api

FastAPI, Python 3.12+, SQLite. Chứa nghiệp vụ tài khoản, hồ sơ, việc làm, CV, đơn ứng tuyển, lịch và thống kê.

## Chạy từ root

```powershell
npm run setup
.venv/Scripts/python.exe -m services.run api --reload
```

Entrypoint đọc duy nhất `.env` gốc qua `services/config.py`, lấy API_PORT và SERVICE_HOST; mặc định host local `127.0.0.1`. Swagger: `/docs` trên cổng API. [Cấu hình](../../docs/guides/configuration.md) · [Hợp đồng API](../../docs/guides/api.md).

## Thành phần

| File | Trách nhiệm |
| --- | --- |
| `app/main.py` | Routes, upload PDF, orchestration AI, quyền dữ liệu |
| `app/schemas.py` | Payload, enum, giới hạn độ dài, ngày/giờ hẹn |
| `app/db.py` | Connection transaction, foreign keys, schema version 1 |
| `app/security.py` | PBKDF2, session token hash, role guards |
| `app/seed.py` | Khởi tạo demo idempotent, không ghi đè |
| `app/ai_client.py` | HTTP tới AI, timeout và mapping lỗi |
| `seed/demo.json` | Tin/hồ sơ minh họa |
| `tests/` | Nghiệp vụ, quyền truy cập và xử lý lỗi AI |

Cấu hình chung nằm ngoài service tại `services/config.py`. API dùng AI_SERVICE_URL tùy chọn; nếu thiếu, suy ra từ AI_PORT. ALLOWED_ORIGINS mặc định suy ra WEB_PORT, hỗ trợ nhiều origin phân cách bằng dấu phẩy.

## Lưu trữ và quyền

Database local mặc định **`var/data/unitalent.db`**, tính theo root, không nằm trong thư mục source. DATABASE_PATH tương đối cũng tính từ root, kể cả khi chạy Python từ vị trí khác. Docker lưu vào volume `/app/var/data`.

SQLite giữ users, sessions, jobs, resumes, applications và interviews. CV lưu BLOB và văn bản trích xuất; application giữ resume_id bất biến. Upload CV mới không thay bản đã nộp. Unique `(job_id,student_id)` chống đơn trùng tại DB.

Sinh viên chỉ xem CV/đơn của mình. Recruiter chỉ xem/sửa/tải đơn thuộc tin của mình; tài nguyên không tồn tại hoặc không thuộc quyền trả 404. Analytics cho recruiter, chỉ dữ liệu tổng hợp.

Mật khẩu PBKDF2 SHA-256, salt ngẫu nhiên, 310.000 vòng. Session opaque 24 giờ, DB chỉ lưu hash, cookie HttpOnly/SameSite=Lax; logout thu hồi. Khi HTTPS đặt COOKIE_SECURE=true. Mutation trình duyệt kiểm tra Origin.

## PDF và vận hành

Chỉ nhận PDF hợp lệ tối đa 5 MB/30 trang, không mã hóa; trích text bằng pypdf. Không OCR; PDF scan vẫn lưu được, cần khai báo kỹ năng thủ công. File tải về là attachment. Dữ liệu private bị Git bỏ qua.

Schema v1 chưa có migration framework, cần sao lưu trước thay cấu trúc. SQLite phù hợp MVP local; triển khai công khai cần rate limit, quy trình quản lý tài khoản/CV và theo dõi vận hành. Xem [deployment.md](../../docs/guides/deployment.md).
