# So sánh từng CV với việc làm

Tính năng tại `/student/cv-review`, trong menu ứng viên **So sánh CV & việc làm**.
Áp dụng cho CV của chính bạn hoặc CV bạn có quyền sử dụng.

## Cách sử dụng

Luồng gồm hai trang:

1. **So sánh từng CV với việc làm**: chọn một CV đã tải lên, xem job được xếp hạng theo đúng
   nội dung CV đó. Đổi CV sẽ tính lại điểm, kỹ năng nhận diện được và yêu cầu cần kiểm tra.
   Nếu vào từ một job, job đó được ghim trong danh sách để bạn so với CV mình chọn.
2. **Skill gaps của CV so với một job**: bấm **Xem skill gaps** trên job. Trang này giữ snapshot
   của đúng cặp CV–JD, hiển thị câu yêu cầu, bằng chứng trong CV, các kỹ năng cần làm rõ,
   BI tham khảo và đề xuất Outline CV. Ba nội dung này nằm ở ba tab độc lập; chỉ tab đang chọn
   mới được hiển thị để tránh một trang quá dài.

Tải PDF tại **Hồ sơ năng lực** nếu chưa có CV. Bản CV chưa xác nhận vẫn được so sánh sơ bộ từ
văn bản PDF; bạn có thể kiểm tra và xác nhận kỹ năng tại Hồ sơ năng lực. Nếu PDF không có lớp chữ,
hãy dùng phân tích OCR trước. Kỹ năng tự khai không được coi là bằng chứng trong CV.

Ở trang skill gaps, kiểm tra từng yêu cầu, chọn kỹ năng cần ưu tiên và điều chỉnh đánh giá khi cần.
Bấm **Tạo Outline bằng AI**, kiểm tra thứ tự mục, lý do, câu trích và gợi ý.
   Sửa tiêu đề/lời khuyên, chọn bằng chứng, bỏ/thêm/di chuyển mục; lưu thay đổi.
   Hành động học nằm riêng, không được trình bày như thành tích đã đạt.
Xem BI tham khảo và xuất báo cáo Markdown; mặc định ẩn email, URL và số điện thoại.

Ứng dụng giữ đúng số gap tìm thấy và không coi thiếu từ khóa trong CV là thiếu năng lực.
Yêu cầu “chưa đánh giá” cần được người dùng rà soát trước khi kết luận.

## Dữ liệu và nguồn kết quả

- Ca tư vấn giữ nguyên CV text/hash, trạng thái phân tích lúc so sánh,
  JD và thời điểm tạo. Cập nhật hồ sơ/CV/job sau đó không đổi ca cũ; tạo ca mới nếu muốn đổi đầu vào.
- Xếp hạng job theo từng CV, không lấy CV mới nhất hoặc kỹ năng hồ sơ thay cho CV đã chọn.
  Matching dùng engine local hiện có, dùng các kỹ năng có trích dẫn kiểm chứng làm tín hiệu CV;
  điểm `/100` không phải xác suất tuyển dụng. Người dùng tự khai báo không có quote không được coi là bằng chứng CV.
- AI đề xuất cấu trúc và lời khuyên; bullet dữ kiện được ứng dụng lấy nguyên văn từ nguồn có thật.
  Server từ chối source/gap ID không tồn tại. Điều này kiểm tra nguồn trích, không xác minh năng lực thực tế.
- Nguồn model được lấy từ provider, có cả trường hợp fallback; fixture được ghi `test-fixture:*`
  và chỉ hoạt động khi `APP_ENV=test`. Gợi ý vẫn cần người dùng xem lại, nhất là các lời khuyên tự do.
- BI đếm kỹ năng chuẩn hóa từ tags trong các job real, khử trùng theo URL nguồn/id.
  Bộ lọc category của JD (hoặc tất cả với JD riêng), tử số/mẫu số, nguồn/ngày đăng và thời điểm chụp được lưu.
  Không trả candidate supply, tài khoản khác hoặc funnel doanh nghiệp cho sinh viên.
  Dataset nhỏ/rỗng được ghi rõ; không suy ra xu hướng của toàn thị trường.
- Lịch sử chỉnh sửa được lưu ở `cv_consultation_revisions`. Mỗi lần ghi yêu cầu revision đúng;
  khi 409, giữ draft, cho so sánh bản mới và chọn rõ bản muốn giữ.
- Retry tạo Outline không tự ghi đè bản đã tạo và chỉnh sửa.
  Lỗi Gemini không được thay bằng nội dung mẫu ngoài môi trường test.

## API

Tất cả endpoint bên dưới yêu cầu session student, kiểm tra owner; tài nguyên người khác trả 404.

| Endpoint | Nội dung |
|---|---|
| `GET /api/resumes` | Metadata và analysis các phiên bản CV của tài khoản |
| `GET /api/resumes/{id}/matches?targetJobId=&limit=12` | Job xếp hạng riêng cho CV đã chọn; job được ghim nếu có |
| `POST /api/cv-consultations` | `{resumeId, jobId}`; CV cần có văn bản PDF hoặc OCR. CV chưa xác nhận kỹ năng vẫn tạo được ca và được đánh dấu phân tích sơ bộ. API vẫn nhận custom JD cho ca cũ/tích hợp. |
| `GET /api/cv-consultations` | Danh sách ca đã lưu |
| `GET /api/cv-consultations/{id}` | Snapshot, phân tích, draft và readiness của bản đã lưu |
| `POST …/{id}/analyze` | `{revision}`; tạo Outline có validation, trả bản có sẵn nếu đã tạo |
| `PATCH …/{id}` | `{revision, selectedGapIds?, gapAssessments?, currentOutline?, outline?}` |
| `GET …/{id}/export?hideContacts=true` | Markdown được escape, mặc định ẩn liên hệ |

AI nội bộ: `POST /resume/outline` nhận `{context}` và trả Outline, method, promptVersion.
`sections[].sourceIds` chọn câu trích, `gapIds` liên kết khoảng trống;
`learningActions[]` giữ việc cần học trước khi ghi vào CV. Endpoint không sinh bullet thành tích mới.

Schema SQLite **v5** thêm hai bảng bằng migration additive trong `init_db()`.
Đã kiểm tra khởi tạo lặp và dữ liệu legacy trên database tạm. Các kết quả kiểm thử lần này
dùng database riêng; không chuyển database local cũ sang volume Docker.

## Kiểm tra

```powershell
npm test
npm run lint
npm run typecheck
npm run build
# Cần web/API/AI đang chạy; Docker test tự chạy toàn bộ suite gồm các ca mới:
npm run docker:test
```

Chỉ chạy ca mới trên stack test riêng:

```powershell
$env:E2E_AI_MODE='offline'
$env:E2E_BASE_URL='http://127.0.0.1:3200'
$env:E2E_ARTIFACT_DIR='../../artifacts/cv-review-check/e2e'
npm --prefix apps/web run test:e2e -- cv-review.spec.ts
```

`E2E_ARTIFACT_DIR` tính từ `apps/web`, mặc định `../../artifacts/e2e`.
Stack offline phải đặt `APP_ENV=test`, `AI_TEST_FIXTURES=true`, database/cổng riêng;
không bật fixture trên ứng dụng thật. Kết thúc shell test hoặc xóa các biến override khi đổi môi trường.
Xem [báo cáo triển khai](../reports/cv-review-implementation-2026-11-06.md).
