# Kiểm thử và khắc phục lỗi

## Tự động

Sau `npm run setup`, chạy tại root:

```powershell
npm test
npm run lint
npm run typecheck
npm run build
```

Pytest dùng database tạm và seed tắt. Bài test API dùng FastAPI TestClient gọi routes AI thật thông qua adapter trong test, không phụ thuộc server đang chạy. Smoke test với các tiến trình thật kiểm tra đường truyền HTTP riêng.

Phạm vi test hiện có:

- Không nhận nhầm JavaScript thành Java hoặc Django thành Go; alias tiếng Việt/k8s được chuẩn hóa.
- Điểm thay đổi theo kỹ năng, danh sách thiếu/khớp có giải thích.
- Đăng ký, trùng email, mật khẩu sai, cookie HttpOnly và logout thu hồi phiên.
- Phân quyền student/recruiter; recruiter khác không truy cập ứng viên/CV hoặc sửa đơn không thuộc tin của mình.
- CV sai định dạng / quá dung lượng bị từ chối; không cho ứng tuyển khi thiếu CV.
- Upload mới giữ nguyên bản CV cũ đã nộp; nộp trùng trả 409.
- Cập nhật lịch và stage được student đọc lại; danh sách ứng viên chỉ có đơn thật.
- Luyện phỏng vấn lưu đúng kết quả trong history; BI rỗng không lỗi; health báo AI dừng.

## Kiểm thử thủ công

Kiểm thử trình duyệt tự động được bổ sung tại [E2E.md](e2e.md), dùng Playwright với hai viewport và server Docker thật. Bộ này độc lập với `npm test` (pytest).

Dùng luồng trong README gốc. Kiểm tra thêm tài khoản mới chưa có CV, tin không tồn tại, API/AI dừng và nút thử lại. Kiểm tra desktop/điện thoại: form không tràn ngang, sidebar thu gọn, lỗi hiển thị gần thao tác. Checklist học chưa lưu bền, không nhầm với trạng thái ứng tuyển trong DB.

Docker Compose đã được build và chạy kiểm thử trên máy hiện tại; chi tiết ở [VERIFICATION.md](verification.md). CI YAML được cung cấp nhưng chỉ có kết quả CI thực sau khi bạn push lên GitHub; không xem file workflow là bằng chứng CI đã chạy.

## Các lỗi thường gặp

| Triệu chứng | Cách xử lý |
| --- | --- |
| Không nhận `node` hoặc `python` | Cài Node 22+/Python 3.12+ và mở terminal mới |
| Không tìm được `.venv/.../python` | Chạy `npm run setup` tại root |
| `ModuleNotFoundError: services` | Chạy `python -m services.run api` từ root, không từ `services/api/` |
| Cổng bận | Dừng đúng tiến trình cũ hoặc đổi WEB_PORT/API_PORT/AI_PORT |
| Đăng nhập báo không kết nối | Kiểm tra backend; Next proxy tới đúng cổng; `/api/health` |
| Jobs / AI báo 503 | Kiểm tra AI, `AI_SERVICE_URL`, timeout; `/health` AI |
| Mutation báo Origin không được phép | Sửa ALLOWED_ORIGINS cho URL trình duyệt, restart backend |
| Demo login sai sau đổi env | Seed không ghi đè mật khẩu cũ; dùng mật khẩu tài khoản đã tạo |
| CV scan không tăng điểm | PDF không có text; khai báo kỹ năng/dự án hoặc dùng PDF có text |
| Recruiter chưa thấy ứng viên | Sinh viên phải nộp đúng tin thuộc recruiter đó; refresh trang |
| `next build` lỗi Google Fonts | Kiểm tra mạng build hoặc chuyển font local; không tắt TypeScript/lint để che lỗi |
| `.next` lỗi sau chạy dev/build | Dùng script dev root (.next-dev), dừng server trước sửa/xóa cache có kiểm soát |
| Media hiện trong Git status | Kiểm tra path/quy tắc .gitignore, gỡ tracked bằng `--cached`, bật hooks |

## Kết quả xác nhận

Kết quả chạy thực và ghi chú bàn giao được cập nhật ở `docs/guides/verification.md`. Các screenshot cục bộ nằm trong `artifacts/` và không đưa vào Git.
