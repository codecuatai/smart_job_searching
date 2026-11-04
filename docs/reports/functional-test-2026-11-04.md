# Kiểm thử chức năng — 04/11/2026

## Cập nhật mới nhất: coaching Gemini

Đã triển khai lộ trình Gemini cá nhân hóa, lưu kế hoạch/checklist vào DB và tạo/chấm câu hỏi phỏng vấn theo hồ sơ/job. Không còn điểm tương lai 100% gán cứng. API timeout đã đồng bộ lên ít nhất 35 giây. **24/24 backend/AI và 22/22 Docker E2E** qua trong 141,9 giây; hai viewport yêu cầu Gemini thật và kiểm tra progress qua reload. Chi tiết: [gemini-coaching.md](gemini-coaching.md).

Các phần phía dưới giữ kết quả những vòng kiểm tra trước; các ghi chú “lộ trình mẫu” và timeout 15 giây thuộc trạng thái cũ.

## Cập nhật sau sửa upload PDF và mở rộng E2E

Vòng mới nhất: 19/19 backend, lint/typecheck qua; Docker E2E **22/22 passed** trong 79,7 giây, không retry/skipped/flaky. Kết quả bên dưới phần này ghi nhận vòng kiểm tra trước khi sửa, để giữ lịch sử lỗi.

Đã mở rộng thành 11 kịch bản × desktop/mobile. Ngoài luồng đăng nhập/ứng tuyển/lịch/BI, kiểm tra thêm PDF rỗng, mật khẩu mở, hạn chế quyền không cần mật khẩu, quá 30 trang, quá 5 MB, PDF không có lớp chữ và PDF có BOM. Kiểm tra thông báo lỗi cố định, giữ nguyên CV cũ khi lỗi, đọc lại sau reload và đối chiếu SHA-256 file tải về. Bổ sung validation tài khoản/hồ sơ và tìm kiếm/xóa bộ lọc job/ứng viên.

Ca phỏng vấn chờ response API thay vì đòi UI có kết quả trong 10 giây. Cả hai lần desktop/mobile trả HTTP 200, lưu đúng lịch sử và dùng `gemini:gemini-3.5-flash-lite`. Gemini có timeout cấu hình 60 giây và API client chờ thêm 10 giây để tránh bỏ cuộc trước provider.

Web/API/AI healthy, integrity_check=ok, 639 job (635 ITviec + 4 demo), 0 job E2E sau cleanup. Tài khoản/CV synthetic vẫn được giữ trong DB test. Các giới hạn chưa OCR, upload chưa gọi Gemini skills và nhận diện phủ định chưa sửa vẫn còn nguyên; không coi E2E xanh là bằng chứng chất lượng mô hình.

## Phạm vi và kết quả

Chạy `npm test`: 15 passed, 1 cảnh báo deprecation Starlette/httpx.
Chạy `npm run docker:test` trên web/API/AI thật trong Docker, Chromium desktop/mobile:
7 passed, 1 failed, 0 skipped, thời gian 56,2 giây. Không coi lần chạy này là xanh toàn bộ.

- Đăng ký, đăng nhập, session persistence, logout và role guard: qua cả hai viewport.
- PDF không hợp lệ, upload PDF có chữ và giữ CV sau reload: qua cả hai viewport.
- Đăng job, tìm job, ứng tuyển, chặn nộp trùng, recruiter nhận/tải CV, CV snapshot bất biến: qua cả hai viewport.
- CV mới cải thiện matching và cập nhật skill gap: qua cả hai viewport.
- Lịch phỏng vấn, phân quyền tài nguyên, analytics và CSV export: qua trong workflow cả hai viewport.
- Phản hồi phỏng vấn và lịch sử: mobile qua; desktop không thấy heading kết quả trong giới hạn assertion 10 giây, UI còn hiện “Đang phân tích…”.

## Kiểm tra riêng phân tích CV

Test API/AI trong database tạm, tắt Gemini để kiểm tra đường local một cách xác định:

- Chưa có CV ứng tuyển: 422.
- PDF giả, PDF khóa, PDF 31 trang: 422; file quá 5 MB: 413.
- PDF có chữ “Python SQL portfolio”: `textExtracted=true`, skills khớp Python/SQL, thiếu Docker; score 76.
- Thay bằng PDF “Python SQL Docker”: score 97; recruiter vẫn tải được đúng byte CV cũ đã nộp.
- Nộp trùng: 409; tài khoản khác tải CV/đơn: 404.
- PDF trắng được lưu với `textExtracted=false`; không có OCR. UI hiện cảnh báo bổ sung kỹ năng.
- Extraction được lưu với `extractor_version=pypdf-text-v1`.
- Trong luồng upload/ứng tuyển, các lời gọi AI ghi nhận chỉ có `/match`; upload chưa gọi Gemini `/skills`.
- Câu “I do not know Python, SQL or Docker.” vẫn được nhận diện cả ba kỹ năng: hạn chế nhận diện phủ định còn tồn tại.

## Gemini và các vấn đề còn lại

Gọi trực tiếp `/skills` bằng văn bản CV tổng hợp trong Docker: 200, `method=gemini`, nhận Python/SQL/Docker/FastAPI.
Gọi API phỏng vấn qua web proxy: 200 trong 3,91 giây, `method=gemini:gemini-3.5-flash-lite`, score 95 và lịch sử lưu đúng response.
Điều này xác nhận Gemini hoạt động, nhưng không chứng minh upload CV đã tích hợp Gemini.

Ca desktop thất bại là bằng chứng độ trễ biến động vượt ngưỡng E2E 10 giây; chưa đủ bằng chứng kết luận mọi request phỏng vấn bị lỗi.
API client phải chờ dài hơn timeout Gemini; cấu hình hiện tại là tối đa 70 giây cho client và 60 giây cho provider, phù hợp với prompt CV/OCR dài.

## Trạng thái sau test

Web/API/AI healthy; database integrity_check=ok; 639 jobs, 0 job E2E.
Các kiểm tra dùng CV tổng hợp, không gửi CV cá nhân cho Gemini.
Kết quả E2E chi tiết nằm trong `artifacts/e2e/results.json` và `artifacts/e2e/report/index.html`.
Đợt này chỉ kiểm thử và ghi nhận kết quả, chưa sửa chức năng hay thay đổi timeout.
