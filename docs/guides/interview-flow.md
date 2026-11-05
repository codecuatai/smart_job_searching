# Luồng luyện phỏng vấn

1. Khi mở trang, `GET /api/interview/questions` lấy ba câu hỏi đã lưu theo tài khoản. Chưa có thì hiển thị ngân hàng tham khảo; thao tác mở trang không tự gọi Gemini để tạo bộ mới.
2. Chọn job trong danh sách. Nếu bỏ trống, API chọn job gợi ý đầu tiên. Chọn job chưa tự thay bộ câu hỏi đang hiển thị.
3. Bấm **Tạo bộ câu hỏi AI**: `POST /api/interview/questions {jobId}`. Backend gửi kỹ năng nhận diện từ CV/hồ sơ, định hướng, tên/mô tả dự án trong profile và JD sang AI service. Gemini tạo đủ ba chủ đề API, cơ sở dữ liệu, dự án; validate schema trước khi thay bộ câu hỏi trong DB. Lỗi provider không xóa bộ cũ.
4. Chọn chủ đề, nhập câu trả lời, bấm **Phân tích câu trả lời**: `POST /api/interview/evaluate {questionId,answer}`. Backend đối chiếu câu hỏi với tài khoản, gửi nguyên câu hỏi đã lưu cùng rubric keywords và câu trả lời sang AI service.
5. Chỉ khi chấm thành công mới hiển thị score/feedback và thêm lịch sử. Điểm phục vụ luyện tập; không phải điểm tuyển dụng hoặc xác minh năng lực.

## Xử lý lỗi

- Câu trả lời rỗng/chỉ khoảng trắng: thông báo tiếng Việt ngay tại ô, chuyển focus về ô, không gọi API.
- Tạo bộ câu hỏi thất bại: lỗi ở bước chuẩn bị bộ câu hỏi, giữ câu hỏi/câu trả lời hiện tại. Có thể bấm tạo để thử lại.
- Chấm thất bại: lỗi ở phần trả lời, giữ nội dung đã nhập, không thêm lịch sử thành công.
- Chỉ thay câu hỏi/xóa bản nháp khi tạo bộ mới thành công hoặc người dùng chủ động đổi chủ đề.
- Mã lỗi `bbb62d334557` trong ảnh người dùng ngày 05/11 được đối chiếu log: Gemini HTTP 503 qua hai lần gọi, `provider-unavailable`. Lỗi tạo bộ câu hỏi từng dùng chung state với lỗi chấm nên hiện sai dưới ô trả lời; nay đã tách state và khu vực thông báo.
- Sau khi xác nhận model chính bị `503 UNAVAILABLE / high demand`, người dùng đã đồng ý dự phòng bằng model Gemini khác. Cấu hình hiện tại giữ `gemini-3.5-flash-lite` chính và `gemini-3.1-flash-lite` dự phòng; UI hiển thị đúng model đã dùng qua `method`. Không thay kết quả bằng mẫu tĩnh. Xem [báo cáo sửa độ ổn định](../reports/gemini-reliability-2026-11-05.md).

## Ý nghĩa kết quả kiểm thử

CI mặc định dùng provider fixture cho sinh nội dung, vì vậy offline pass không chứng minh Gemini thật đang khả dụng. Lượt live trước sửa UI có 22/28 pass, 6 lỗi 503; không được báo là toàn bộ AI live đã pass. Bộ test mới bổ sung lỗi tạo/chấm bằng fault injection để kiểm chứng giao diện giữ draft và đặt lỗi đúng bước. Ca thành công vẫn kiểm tra HTTP 200, đúng provider/mode, nội dung phản hồi và lịch sử sau reload. Xem [E2E](e2e.md).
