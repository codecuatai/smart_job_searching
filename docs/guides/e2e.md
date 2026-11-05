# Kiểm thử E2E bằng trình duyệt trên Docker

Bộ kiểm thử dùng **Playwright Test**, trình duyệt Chromium/Edge thật, frontend production trong Docker và các dịch vụ API/AI, database, OCR và BI thật. Mặc định `docker:test` dùng provider sinh nội dung xác định trong AI service, ghi method `test-fixture:offline-v1`, không gọi Gemini. Chế độ live dùng Gemini thật. CV thử nghiệm được tạo trong bộ nhớ; không đọc hoặc upload CV/video cá nhân.

## Chạy lại

Tại thư mục gốc, cách khuyến nghị là chạy toàn bộ E2E trong Docker:

```powershell
npm run docker:test
```

`docker:test` build và khởi động web/API/AI/warehouse/Metabase/ETL trong project `unitalent-test` và volume riêng, chờ healthcheck rồi chạy Playwright với `E2E_BASE_URL=http://web:3100`. Web test :3100, BI test :3101, dữ liệu app chính :3000 giữ nguyên. Không cần Python/dependencies/browser trên host. Test reset đúng volume test trước mỗi lần chạy và tự dừng container/network trong `finally`, kể cả khi thất bại.

Live AI trên PowerShell: `$env:E2E_AI_MODE='live'; npm run docker:test`. Sau đó `Remove-Item Env:E2E_AI_MODE` để về mặc định. Linux/macOS: `E2E_AI_MODE=live npm run docker:test`. Live yêu cầu `GEMINI_API_KEY`; không đổi expected 200 thành 503 để làm test pass. Offline pass không chứng minh provider live khả dụng.

Fixture chỉ bật với `APP_ENV=test` và `AI_TEST_FIXTURES=true`; service từ chối khởi động nếu bật fixture ngoài môi trường test. Không thêm hai biến này vào `.env` dùng ứng dụng bình thường. CI luôn chạy offline; live chạy thêm khi có secret và giữ báo cáo offline riêng.

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

## Phạm vi 28 ca

Chạy 14 kịch bản trên **desktop 1440×900** và **mobile 390×844**. Ngoài các ca bên dưới, có Gemini CV extraction + chỉnh/xác nhận + giải thích matching; PDF raster qua OCR thật; 6 Metabase SQL questions thực thi thành công.

| Kịch bản | Những điều được kiểm chứng |
| --- | --- |
| Đăng nhập và phân quyền | Trang riêng chuyển về login khi chưa xác thực; mật khẩu sai có lỗi; đăng nhập đúng; phiên giữ sau reload; không vào trang/API recruiter bằng student; logout thu hồi cookie/session |
| CV cơ bản | Đăng ký từ UI; PDF giả/hỏng có lỗi cố định; PDF có text và PDF có BOM được lưu; lỗi upload không thay CV cũ; CV vẫn hiện đúng sau reload |
| Sáu biến thể PDF | File rỗng, khóa mật khẩu, hạn chế quyền không cần mật khẩu mở, 31 trang, quá 5 MB, không có lớp chữ; kiểm tra status, thông báo, reload và SHA-256 bản tải về |
| Validation và bộ lọc | Trùng email, mật khẩu sai, GPA sai, student không đọc analytics; lọc ngành, tìm kiếm không có kết quả và xóa bộ lọc |
| Tuyển dụng toàn trình | Hai tài khoản độc lập; đăng tin; chặn thiếu CV/trùng; skill gap đổi khi thay CV; Gemini tạo lộ trình theo 6 giờ học/tuần, checklist lưu sau reload và không có projectedScore giả; bộ lọc ứng viên; CV snapshot SHA-256; lịch hẹn; phân quyền; BI và CSV |
| Phỏng vấn | Gemini tạo ba câu hỏi theo hồ sơ/job; kiểm tra provider, chấm đúng câu đã lưu, điểm/feedback và lịch sử sau reload; đổi đúng câu hỏi theo chủ đề |

Các trang chính còn được kiểm tra không tràn ngang ở viewport tương ứng. Đây là kiểm thử Chromium/Edge, chưa phải chứng nhận tương thích Safari/Firefox hoặc kiểm toán accessibility đầy đủ.

Ca phỏng vấn chờ response API tối đa 35 giây, kiểm tra HTTP 200, điểm 0–100 và `method=gemini:...` trước khi kiểm tra kết quả UI. Lộ trình/câu hỏi được tạo qua Gemini thật, không mock. File JSON lộ trình và câu hỏi/đánh giá được đính kèm vào report. Lỗi HTTP 503 hoặc provider không phải Gemini làm test thất bại. Job tạo trong workflow được xóa trong `finally` cùng lộ trình liên quan; tài khoản/CV synthetic vẫn ở database test.

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
