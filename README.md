# UniTalent AI

Hệ thống tìm việc cho sinh viên, gồm web, API và dịch vụ AI cục bộ. Đây là MVP có tài khoản phân quyền, lưu CV/đơn ứng tuyển thật và bộ E2E trên trình duyệt.

## Cấu trúc

```text
.
├── apps/web/                 Next.js 15, React 19, TypeScript; giao diện và E2E
├── services/
│   ├── api/                  FastAPI, xác thực, hồ sơ, việc làm, CV, SQLite
│   ├── ai/                   FastAPI, nhận diện kỹ năng, matching và rubric
│   ├── config.py             Đọc .env gốc và chuẩn hóa đường dẫn dữ liệu
│   └── run.py                Entrypoint chung cho hai dịch vụ Python
├── scripts/
│   ├── lib/env.mjs           Đọc .env gốc, giá trị mặc định và kiểm tra cổng
│   ├── research/             Công cụ tạo báo cáo, sơ đồ và phụ đề
│   └── *.mjs                 Setup, chạy ứng dụng, kiểm thử và kiểm tra Git
├── docs/
│   ├── guides/               Hướng dẫn kỹ thuật Markdown
│   ├── research/             Báo cáo nghiên cứu DOCX gốc
│   └── diagrams/             Sơ đồ dùng chung, không giữ ảnh trùng
├── media/                    Video/phụ đề cá nhân, giữ trên máy, bỏ qua Git
├── var/data/                 SQLite và CV local, bỏ qua Git
├── artifacts/                Báo cáo E2E, screenshot và kết quả chạy, bỏ qua Git
├── .env                      File cấu hình duy nhất, không đưa lên Git
├── compose.yaml              Ba service Docker: web, api, ai
├── requirements*.txt         Dependency Python và lock đã kiểm thử
└── package.json              Các lệnh điều hành từ thư mục gốc
```

Lý do tổ chức: `apps` chứa giao diện người dùng, `services` chứa dịch vụ độc lập; `scripts` chứa công cụ chạy; `docs` chứa tài liệu; `var` chứa dữ liệu nghiệp vụ; `artifacts` chứa kết quả có thể tạo lại. Không đặt database trong source và không trộn bản render thử với báo cáo chính thức. Xem [quyết định cấu trúc](docs/guides/project-layout.md).

## Cài đặt

Yêu cầu Node.js 22+, Python 3.12+, npm; Docker Desktop nếu chạy container.

```powershell
npm run setup
```

Setup tạo `.venv`, cài Python theo `requirements.lock.txt`, cài npm trong `apps/web` và tạo `.env` gốc nếu thiếu. Không ghi đè `.env` đang có. Repository không giữ `.env.example` hoặc `.env.local`; giá trị mặc định được quản lý trong `scripts/lib/env.mjs` và giải thích tại [configuration.md](docs/guides/configuration.md).

Nếu chỉ muốn tạo cấu hình:

```powershell
npm run env:init
```

## Chạy Docker

```powershell
docker compose up --build -d --wait
docker compose ps
```

Mở [localhost:3000](http://127.0.0.1:3000) với `WEB_PORT=3000`. Compose đọc cùng `.env` gốc; địa chỉ kết nối nội bộ `web → api → ai` được tạo từ tên service và cổng, không cần file env riêng trong container.

```powershell
docker compose down
```

Lệnh dừng giữ dữ liệu. Không xóa volume khi cần giữ tài khoản/CV. Bản `.env` trên máy hiện tại đang tham chiếu volume cũ ở chế độ external để bảo toàn dữ liệu sau đổi tên thư mục/service; clone mới dùng volume `unitalent_data`.

## Chạy local

```powershell
npm run dev
```

Script đọc `WEB_PORT`, `API_PORT`, `AI_PORT` từ `.env` và chạy đủ ba dịch vụ. `Ctrl+C` dừng các tiến trình do script tạo. Nếu cổng bận, đổi cổng trong chính `.env`, không tạo file cấu hình khác. Không chạy Docker và local cùng một WEB_PORT.

Chạy riêng từng thành phần từ root:

```powershell
.venv/Scripts/python.exe -m services.run ai --reload
.venv/Scripts/python.exe -m services.run api --reload
npm --prefix apps/web run dev
```

Linux/macOS dùng `.venv/bin/python`. Swagger nằm tại cổng API/AI đã đặt trong `.env`, đường dẫn `/docs`.

## Tài khoản demo

Khi `SEED_DEMO=true`, lần chạy đầu tạo tài khoản bên dưới với `DEMO_PASSWORD` (mặc định `demo12345`). Seed không ghi đè tài khoản đã tồn tại.

| Vai trò | Email |
| --- | --- |
| Sinh viên | `nam.nguyen@hcmut.edu.vn` |
| Nhà tuyển dụng | `recruitment@vng.com.vn` |

Tin/hồ sơ seed là minh họa. Nút đăng nhập nhanh dùng mật khẩu demo mặc định; nếu đổi mật khẩu seed, nhập bằng form. Không dùng tài khoản demo khi mở dịch vụ công khai.

## Chức năng và phạm vi

- Đăng ký/đăng nhập/logout, cookie HttpOnly, session và quyền dữ liệu theo vai trò.
- Nhà tuyển dụng đăng tin; sinh viên sửa học vấn/kỹ năng/dự án, tải CV PDF tối đa 5 MB/30 trang, tìm việc và ứng tuyển.
- Chặn đơn trùng, giữ đúng bản CV đã nộp; nhà tuyển dụng chỉ xem hồ sơ thuộc tin của mình, cập nhật trạng thái/lịch.
- AI đối chiếu kỹ năng + cosine văn bản, giải thích kỹ năng thiếu, sinh lộ trình; luyện phỏng vấn văn bản và lưu lịch sử.
- BI tổng hợp dữ liệu trong SQLite hiện tại, không khẳng định số liệu thị trường thực.

AI là baseline NLP/rule-based, chưa có AST/đạo văn, xác minh commit GitHub, OCR, voice STT/TTS, LLM hoặc email tự động. Xem [trạng thái triển khai](docs/guides/implementation-status.md).

## Kiểm thử và build

```powershell
npm test
npm run lint
npm run typecheck
npm run build
# Cần web/API/AI đang chạy tại WEB_PORT trong .env:
npm run test:e2e
npm run test:e2e:report
```

E2E dùng Edge headless trên Windows (Chromium trên Linux), hai viewport desktop/mobile và server thật. Kết quả tại `artifacts/e2e/`; báo cáo HTML mặc định ở [localhost:9323](http://127.0.0.1:9323). Xem [hướng dẫn E2E](docs/guides/e2e.md) và [kết quả kiểm tra](docs/guides/verification.md).

Build dùng `.next`, dev dùng `.next-dev`. Next rewrite được chốt lúc build; đổi cổng API/địa chỉ proxy cần build lại. Font hiện có được tải từ Google Fonts khi build, cần Internet.

## Git và media

`.gitignore` và hooks chặn media cá nhân, `.env`, database và file lớn. Ảnh ứng dụng trong `apps/web/public/` và sơ đồ trong `docs/diagrams/` là asset chủ định được commit. Toàn bộ `media/`, `var/`, `artifacts/` được bỏ qua. Media gốc được giữ nguyên.

```powershell
# Khi bạn muốn tạo repository chung:
git init
npm run git:hooks
git add .
npm run git:check
```

Không còn Git riêng trong ứng dụng web. Lịch sử Git cũ được sao lưu ngoài dự án; không có commit/push tự động. Xem [Git và media](docs/guides/git-and-media.md).

## Tài liệu

- [Mục lục](docs/README.md)
- [Cấu hình duy nhất](docs/guides/configuration.md)
- [Kiến trúc](docs/guides/architecture.md) · [API](docs/guides/api.md)
- [Web](apps/web/README.md) · [API service](services/api/README.md) · [AI service](services/ai/README.md)
- [Triển khai và sao lưu](docs/guides/deployment.md) · [Công cụ nghiên cứu](scripts/research/README.md)
