# Kiểm thử chức năng — 04/11/2026

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
API client đang timeout 15 giây trong khi Gemini timeout mặc định 25 giây, cần đồng bộ để tránh API bỏ cuộc trước khi AI trả response/fallback.

## Trạng thái sau test

Web/API/AI healthy; database integrity_check=ok; 639 jobs, 0 job E2E.
Các kiểm tra dùng CV tổng hợp, không gửi CV cá nhân cho Gemini.
Kết quả E2E chi tiết nằm trong `artifacts/e2e/results.json` và `artifacts/e2e/report/index.html`.
Đợt này chỉ kiểm thử và ghi nhận kết quả, chưa sửa chức năng hay thay đổi timeout.
