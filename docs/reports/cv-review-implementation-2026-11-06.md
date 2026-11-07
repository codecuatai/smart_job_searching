# Triển khai tư vấn CV–JD và Outline CV — 06/11/2026

Triển khai theo [kế hoạch](../plans/cv-jd-consultation-2026-11-06.md), từ baseline `b8da64d`.
Hướng dẫn người dùng và API tại [cv-review.md](../guides/cv-review.md).

## Kết quả

- Có menu/trang `/student/cv-review`, link từ hồ sơ và lộ trình kỹ năng.
- Chọn CV theo phiên bản; dùng lại extraction/Gemini/OCR hiện có, sửa và xác nhận kỹ năng.
  Bắt buộc chọn JD trong hệ thống hoặc nhập JD riêng, không tự lấy việc đầu tiên.
- Lưu snapshot CV/analysis/profile/JD; ma trận mỗi kỹ năng có câu trích JD, CV,
  must-have/nice-to-have và trạng thái. Không đồng nhất tự khai báo hoặc thiếu từ khóa với thiếu năng lực.
  Số gap không bị ép thành 3; unknown cần được rà soát thủ công.
- Gemini tạo thứ tự Outline, lý do, hướng dẫn và hành động học. Bullet dữ kiện được lấy nguyên văn
  từ source ID đã kiểm tra; không có trường cho AI tự thêm thành tích. Schema/source IDs/gap IDs
  được kiểm tra lại tại API. Lời khuyên tự do vẫn cần người dùng xem lại.
- Chỉnh Outline, chọn/bỏ bằng chứng, thêm/bỏ/đổi thứ tự mục, lưu lịch sử revision.
  CAS bảo vệ việc ghi từ hai tab; khi lỗi giữ draft và có so sánh bản máy chủ để chọn cách xử lý.
  Retry tạo Outline/kịch bản giữ nguyên nội dung đã tạo thay vì ghi đè bản chỉnh sửa.
- BI chỉ trả aggregate job real, tần suất skill theo tags chuẩn hóa, bộ lọc/category,
  nguồn, ngày đăng và thời điểm chụp; không mở quyền recruiter analytics hoặc lộ candidate/funnel.
- Xuất Markdown từ bản vừa lưu; escape markup, mặc định ẩn email/URL/số điện thoại.
  Báo cáo có gap, Outline, hành động học, BI, lời thoại và checklist đọc được bằng tiếng Việt.
- Tạo kịch bản có thể sửa từ dữ liệu đã lưu khi đủ Outline và 3+ gap được chọn có căn cứ.
  Checklist CV thật/quyền sử dụng, Outline review, thời lượng video và đã nộp do người dùng xác nhận.
  Thời gian đọc chỉ là ước lượng; không tự quay/nộp hoặc xác minh bài tập.
- Migration SQLite v5 additive: `cv_consultations`, `cv_consultation_revisions` và index owner.
  Không chuyển database local cũ vào Docker; không dùng snapshot ứng tuyển thay cho ca tư vấn.
- Có provider fixture dành riêng cho endpoint mới trong môi trường test.
  `E2E_ARTIFACT_DIR` cho phép tách report từng đợt, giữ nguyên mặc định cũ.

## Kiểm chứng

| Kiểm tra | Kết quả/phạm vi |
|---|---|
| Python toàn bộ | **83 passed**, 1 cảnh báo deprecation có sẵn của Starlette/httpx |
| Unit mới | 11 ca API/AI: quyền sở hữu, chọn CV cũ, snapshot bất biến, gap/BI, nguồn giả, lỗi provider, revision, export, script, migration legacy/idempotency, kỹ năng tự khai báo và provenance sửa Outline |
| ESLint/TypeScript | Passed; production build cũng chạy lint/type validation |
| Next production build | Passed, tạo được cả route mới; không phải Docker rebuild |
| E2E mới, offline | **4/4 passed**, 40,1s, 0 skip/flaky; 2 kịch bản × desktop/mobile, web/API/AI thật trên host và provider fixture có nhãn rõ |
| Kịch bản E2E thành công | CV cũ dù có CV mới hơn → JD riêng → 3 gap → Outline → sửa/lưu/reload → kịch bản → checklist → export |
| Kịch bản E2E lỗi | Chủ động chặn analyze bằng HTTP 503; đầu vào đã lưu còn sau reload; retry thành công; chỉ 1 gap thì nút tạo kịch bản bị khóa |
| Gemini thật, kiểm tra riêng | Synthetic context, **passed**, method `gemini:gemini-3.5-flash-lite`; 3 sections + 3 learningActions hợp schema, 3,81s. Có một 503 được retry tự động. Không phải full live browser E2E hoặc cam kết provider luôn khả dụng |
| UI thật 1440/768/390 | Trang tạo và chi tiết: **6/6 snapshots**, không JS pageerror, không tràn ngang; probe/layout/app + judge của design-taste-frontend không còn FAIL/WARN sau sửa |
| Source design lint | 0 FAIL / 0 WARN trên màn hình mới |
| Cách ly dữ liệu | Database test ở `artifacts/cv-review-2026-11-06/test.db`; không chạy migration trên DB nghiệp vụ local hoặc volume Docker |

Artifact local riêng tư:

- `artifacts/cv-review-2026-11-06/e2e-final/results.json` và `report/index.html`.
- `artifacts/cv-review-2026-11-06/live-outline.json` — chỉ metadata, không có key/CV cá nhân.
- `artifacts/cv-review-2026-11-06/ui/audit.json` và ảnh `create/detail-1440/768/390.png`.

Vòng E2E ban đầu có một desktop timeout khi dev server biên dịch route lần đầu khoảng 11s,
vượt assertion URL mặc định 10s. Đã chờ navigation theo ngưỡng 30s của cấu hình;
vòng cuối đạt cả 4 ca, không đổi expected status và không retry thủ công để coi lỗi provider là pass.

## Thiết kế và giới hạn

- Áp dụng skill ui-ux-pro-max cho trạng thái loading/success/error; design-taste-frontend app mode
  chọn **Framed sheet**, seed `562403866`, giữ palette/type sẵn có. Không redraw.
  Câu hỏi chính: “CV này thiếu minh chứng gì so với JD và nên đổi bố cục thế nào?”.
  Đặc trưng của màn hình là ma trận câu trích CV–JD, không dùng KPI hoặc số liệu trang trí.
- Sửa nhãn điểm thành “Điểm tham khảo”, tăng contrast và ẩn nội dung details đóng một cách rõ ràng
  để không tạo text layout giả sát mép ở tablet. Không xin miễn trừ rule inspector.
- Screenshot dùng tài khoản/CV/JD synthetic để kiểm thử. Khi sử dụng thực tế, người học phải tự chọn
  CV và JD phù hợp, xác minh dữ kiện và quyền sử dụng; không có ca CV cá nhân được công bố trong Git.
- Chưa chạy lại toàn bộ suite Docker, OCR scan hoặc Metabase ở lượt này vì Docker daemon không chạy.
  E2E mới đã chạy trên host; các phép thử OCR/BI Docker lịch sử vẫn được tách khỏi bằng chứng mới.
- Chưa khẳng định chất lượng matching thực tế, ATS acceptance, khả năng được tuyển hoặc bài nộp đã đạt.
  Hạn chế taxonomy/gold labels/dataset BI của bản nền vẫn còn. Outline không thay cho đào tạo kỹ năng.
- Kịch bản đã tạo được giữ để người dùng biên tập; nếu thay lựa chọn gap hoặc Outline, cần tự kiểm tra
  và sửa lời thoại tương ứng. Có thể xóa lời thoại, lưu rồi tạo lại từ dữ liệu mới.
- Những tiến trình test riêng được dừng sau kiểm tra; không để ứng dụng fixture chạy như bản thật.
