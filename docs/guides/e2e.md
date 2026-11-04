# Kiểm thử E2E bằng trình duyệt trên Docker

Bộ kiểm thử dùng **Playwright Test**, trình duyệt Chromium/Edge thật, frontend production trong Docker và hai dịch vụ API/AI thật. Không mock API hoặc thay dữ liệu trả về bằng fixture. CV thử nghiệm được tạo trong bộ nhớ, có lớp văn bản PDF; không đọc hoặc upload CV/video cá nhân.

## Chạy lại

Tại thư mục gốc, cách khuyến nghị là chạy toàn bộ E2E trong Docker:

```powershell
npm run docker:test
```

`docker:test` build và khởi động web/API/AI, chờ healthcheck, sau đó chạy Playwright trong service `e2e` trên cùng network Docker với `E2E_BASE_URL=http://web:3000`. Không cần Python virtualenv, npm dependencies hoặc trình duyệt cài trên máy host.

Lệnh test tự sinh báo cáo HTML/JSON vào `artifacts/e2e/`. Nếu máy đã cài dependencies của `apps/web`, có thể mở report tương tác bằng `npm run test:e2e:report`.

Nếu muốn chạy runner trên host để debug nhanh, dùng `npm run setup`, `docker compose up --build -d --wait`, rồi `npm run test:e2e`.

Ứng dụng: [localhost:3000](http://127.0.0.1:3000). Báo cáo HTML sau khi chạy lệnh report: [localhost:9323](http://127.0.0.1:9323). Giữ terminal report mở khi xem; `Ctrl+C` chỉ dừng report server.

Trên Windows, cấu hình mặc định dùng Microsoft Edge đã cài, chạy headless; không mở cửa sổ ảnh hưởng công việc của bạn. Có thể chọn Chrome:

```powershell
$env:PLAYWRIGHT_CHANNEL='chrome'
npm run test:e2e
```

Trên Linux/macOS hoặc Windows không có Edge/Chrome, cài Chromium của Playwright:

```powershell
# Chạy trong apps/web/
npx playwright install chromium
```

Trên Windows sau khi cài Chromium, đặt `$env:PLAYWRIGHT_CHANNEL='chromium'` trước khi chạy. Trên Linux, channel mặc định để trống để dùng Chromium bundled; CI cần `npx playwright install --with-deps chromium` để có thư viện hệ thống.

Nếu kiểm thử server khác, đặt `E2E_BASE_URL` trong `.env` gốc; nếu bỏ trống, runner suy ra từ WEB_PORT. Chỉ trỏ tới môi trường thử nghiệm vì suite tạo tài khoản, tin và đơn ứng tuyển thật. Mỗi lần chạy dùng ID/email duy nhất, không phụ thuộc dữ liệu của lần trước. Chưa có API xóa tài khoản; dữ liệu tên `E2E ...`/email `@example.test` thuộc dữ liệu synthetic. Không chạy bộ test này vào production.

## Phạm vi 8 ca

Chạy cùng 4 kịch bản trên **desktop 1440×900** và **mobile 390×844**:

| Kịch bản | Những điều được kiểm chứng |
| --- | --- |
| Đăng nhập và phân quyền | Trang riêng chuyển về login khi chưa xác thực; mật khẩu sai có lỗi; đăng nhập đúng; phiên giữ sau reload; không vào trang/API recruiter bằng student; logout thu hồi cookie/session |
| CV | Đăng ký từ UI; báo chưa có CV; từ chối PDF giả; nhận PDF có text; CV vẫn hiện đúng sau reload |
| Tuyển dụng toàn trình | Hai tài khoản độc lập đăng ký từ UI; recruiter đăng tin; student sửa hồ sơ, upload CV, tìm việc, xem chi tiết và nộp; nộp trùng có lỗi; lộ trình chỉ đúng kỹ năng thiếu; đổi CV tăng điểm phù hợp; recruiter tải đúng CV phiên bản cũ (so SHA-256); lưu lịch; student đọc được lịch; recruiter khác bị chặn đọc/sửa/tải hồ sơ |
| Phỏng vấn | Trả lời, nhận điểm/feedback, lịch sử có nội dung đúng và giữ sau reload; đổi chủ đề đúng câu hỏi |

Các trang chính còn được kiểm tra không tràn ngang ở viewport tương ứng. Đây là kiểm thử Chromium/Edge, chưa phải chứng nhận tương thích Safari/Firefox hoặc kiểm toán accessibility đầy đủ.

## Mã nguồn và bằng chứng

- `apps/web/playwright.config.mjs`: địa chỉ server, viewport, thời gian chờ, reporter và trace khi lỗi.
- `apps/web/e2e/workflows.spec.ts`: toàn bộ luồng, fixture PDF, assertion và ảnh bằng chứng.
- `artifacts/e2e/report/index.html`: báo cáo HTML.
- `artifacts/e2e/results.json`: kết quả máy đọc được.
- `artifacts/e2e/results/`: screenshot theo từng ca; khi lỗi có trace ZIP để tái hiện thao tác.

`artifacts/` nằm ngoài vùng commit theo `.gitignore`; ảnh/PDF/trace thử nghiệm không được đẩy lên Git. Source tests và config được commit cùng dự án. Báo cáo/trace có thể chứa dữ liệu đăng nhập thử nghiệm; giữ cục bộ.

Xem [VERIFICATION.md](verification.md) để biết kết quả lần chạy thực tế gần nhất và trạng thái container. Các assertion dùng cơ chế chờ điều kiện của [Playwright](https://playwright.dev/docs/test-assertions), không dùng sleep cố định để che lỗi tải dữ liệu.

## Dừng Docker

```powershell
docker compose down
```

Lệnh này giữ volume. Chỉ xóa volume bằng `down --volumes` khi chắc chắn project này chỉ chứa dữ liệu thử nghiệm và không cần giữ. Không dừng hoặc xóa volume của project Docker khác.
