# Lộ trình học và phỏng vấn Gemini

## Sử dụng

1. Cập nhật hồ sơ/CV, mở **Lộ trình kỹ năng**, chọn job và số giờ học mỗi tuần, bấm **Tạo lộ trình AI**.
2. Gemini tạo kế hoạch có thứ tự kiến thức, bài tập, tiêu chí hoàn thành và tên tài liệu. Đánh dấu cột mốc để lưu tiến độ theo tài khoản. Khi kỹ năng/JD/giờ học thay đổi, hệ thống dùng kế hoạch riêng; không trộn tiến độ.
3. Mở **Luyện phỏng vấn**, chọn vị trí và bấm **Tạo bộ câu hỏi AI**. Ba câu hỏi theo chủ đề được tạo từ kỹ năng/dự án và JD, lưu lại để dùng tiếp.
4. Trả lời câu hỏi. Backend lấy nguyên câu hỏi và tiêu chí đã lưu để Gemini chấm, rồi lưu câu hỏi/đánh giá trong lịch sử.

Model cấu hình: `GEMINI_MODEL=gemini-3.5-flash-lite`.

## Dữ liệu và cách kiểm chứng

Input coaching gồm kỹ năng nhận diện từ hồ sơ/CV, mô tả dự án khai báo, JD và số giờ học. Không cần gửi file CV gốc, email hoặc tên tài khoản trong context. Kỹ năng đầu vào vẫn được nhận diện bằng taxonomy local, nên không coi danh sách này là bằng chứng đã xác minh năng lực.

Response lộ trình/câu hỏi được kiểm tra bằng Pydantic. Output sinh bằng Gemini có `method=gemini:<model>`; khi gọi dịch vụ thất bại, API trả lỗi để thử lại. Bộ câu hỏi tham khảo cũ có `method=question-bank`, được ghi rõ trong UI.

Không còn `projectedScore=100` hoặc nhãn “Match sau 2 tuần”. Thời lượng học do AI ước lượng; matching được tính lại từ minh chứng cập nhật, không từ thao tác đánh dấu hoàn thành.

SQLite schema version 3 thêm `learning_plans` và `coaching_questions`, giới hạn dữ liệu theo tài khoản. Lộ trình cache bằng fingerprint của context và giờ học; progress key chỉ được nhận nếu thuộc milestones của chính kế hoạch đó. Câu hỏi AI mới thay bộ câu hỏi đang luyện của tài khoản, còn lịch sử giữ nguyên bản chụp nội dung cũ.

## Kiểm thử

Kết quả xác nhận ngày 04/11/2026: **24/24 backend/AI**, lint/typecheck/build qua; **22/22 Docker E2E** trong 141,9 giây, 0 failed/skipped/flaky và không retry. Vòng đầu phát hiện checkbox chưa cập nhật ngay vì chờ API; đã sửa cập nhật tức thời và rollback khi lưu thất bại, rồi chạy lại toàn bộ suite.

Hai viewport đều tạo kế hoạch/câu hỏi và chấm câu trả lời bằng `gemini:gemini-3.5-flash-lite`; kiểm tra checklist giữ qua reload. Schema versions [1,2,3], integrity_check=ok, 639 job và 0 job E2E sau cleanup. Web/API/AI healthy.

- Unit/API kiểm tra cache, thay đổi context/giờ học, lưu tiến độ, ID task hợp lệ, phân quyền, câu hỏi và lịch sử, lỗi Gemini không được báo thành công.
- Unit/AI kiểm tra schema, tuần trùng và đủ ba chủ đề.
- Docker E2E yêu cầu provider Gemini thật, lưu checklist qua reload, không có điểm tương lai gán cứng, tạo/chấm đúng câu hỏi AI. Report có JSON `gemini-learning-plan`, `gemini-interview` và screenshot `gemini-roadmap`.

Chưa có phỏng vấn giọng nói STT/TTS. Lộ trình và phản hồi AI cần được người học xem xét; không dùng điểm luyện tập để tự động quyết định tuyển dụng.
