# Kiểm tra và sửa độ ổn định Gemini — 05/11/2026

## Nguyên nhân đã xác minh

- Model chính đúng tên: `gemini-3.5-flash-lite`. `models.get` với key hiện tại trả 200, name `models/gemini-3.5-flash-lite`, version `3.5-flash-lite-07-2026`, hỗ trợ `generateContent`; khớp [tài liệu Google](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).
- Lỗi thực tế Google trả `503 UNAVAILABLE`, message có `high demand`. Không phải bằng chứng key sai hoặc đã hết quota. Các mã `8190a0de342d`, `bbb62d334557` đối chiếu đúng log lỗi 503. Không công khai key, prompt hoặc URL chứa key.
- Chính sách cũ chỉ có hai lần gọi, chờ 0,4s. Chuyển sang retry tăng dần giúp nhiều tác vụ chạy được, nhưng kiểm thử live chỉ retry model chính vẫn còn 1/30 ca thất bại. Hai lần kiểm tra một-click trên app chính vẫn nhận 503/timeout; không được coi retry là đã xử lý hoàn toàn capacity phía Google.
- Người dùng đã cho phép model Gemini dự phòng. `models.get` xác nhận `gemini-3.1-flash-lite` có sẵn với key, version `3.1-flash-lite-05-2026`. [Tài liệu model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite), [giá Google](https://ai.google.dev/gemini-api/docs/pricing). Dự phòng có thể khác chi phí/đầu ra.

## Sửa ứng dụng

- Giữ nguyên key và model chính, thêm `GEMINI_FALLBACK_MODEL` vào root `.env`, `.env.example`, bộ sinh env và Compose. Để trống để tắt.
- Một ngân sách tổng 60s, tối đa 6 lần gọi; backoff 1/2/4/8/16s cộng jitter, tôn trọng `Retry-After` và `google.rpc.RetryInfo`; 429 không có hint chờ ít nhất 30s. Không retry sai key/model; không chuyển model vì quota hoặc lỗi cấu hình.
- Khi bật dự phòng, mỗi lần tối đa 20s; chuyển sau hai lỗi tạm thời của model chính hoặc một timeout. Dự phòng không tạo một chuỗi retry lồng vô hạn.
- Metadata model gắn theo kết quả thành công; CV/roadmap/interview trả đúng `method` thực tế. Không dùng biến toàn cục có thể nhầm giữa requests hoặc tin trường model do LLM tự khai.
- Tách lỗi tạo câu hỏi/lỗi chấm, giữ draft khi lỗi; validation câu trả lời trắng bằng tiếng Việt. Test 503 chủ động kiểm tra đặt lỗi đúng bước.

## Kết quả kiểm chứng

- Python: 72 passed, gồm recovery nhiều lần 503, retry hữu hạn, deadline/cooldown, key/model sai, không bypass quota, fallback timeout, provenance và JSON không giả mạo được model.
- Docker production build/typecheck và lint passed. App chính tiếp tục chạy trên :3000.
- Sau khi bật model dự phòng: **30/30 E2E live desktop/mobile passed**, 200,3s, không skipped/flaky và không có lần retry thủ công qua UI (`upstream-transient-retry` = 0). Client vẫn có retry/fallback tự động theo policy. Các tác vụ sinh nội dung kiểm tra method `gemini:*`; hai ca fault injection riêng chủ động trả 503 để kiểm chứng UX, không được coi là bằng chứng provider thành công. Báo cáo nguyên bản giữ tại `artifacts/gemini-reliability-2026-11-05/live-e2e-final`.
- Browser thật trên app chính, tài khoản thử nghiệm riêng, job Senior Data Scientist từ dữ liệu thật: **một click tạo = 200 (16,446s)**, **một click chấm = 200 (15,306s)**; cả hai method `gemini:gemini-3.1-flash-lite`; sau reload lịch sử còn 1 kết quả. Không mock API/provider trong phép thử này.
- Artifact riêng tư local: `artifacts/gemini-reliability-2026-11-05/main-interview-live.json` và `main-interview-live.png`. Lượt live chỉ retry model chính 29/30 được giữ riêng tại `live-e2e-initial`; không xóa kết quả thất bại để trình bày thành pass.

Kết quả một thời điểm không bảo đảm Google luôn có capacity hoặc project không bao giờ chạm quota. Nếu cả hai model không khả dụng, API vẫn trả lỗi rõ và giữ dữ liệu; không giả thành công bằng dữ liệu mẫu.
