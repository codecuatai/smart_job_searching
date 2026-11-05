# Audit nghiệm thu và UX ngày 05/11/2026

Baseline `99323c3`. Đợt này chạy dự án, kiểm thử và lập kế hoạch; chưa thay đổi chức năng hoặc giao diện.

## Kết quả

| Hạng mục | Kết quả |
|---|---|
| Docker build/start | 6 services healthy; web 3000, Metabase 3001 |
| Unit/API/AI | 48 passed |
| TypeScript/ESLint | Passed |
| Browser E2E core, desktop và mobile | 18 passed |
| Browser E2E AI/BI, desktop | 3 passed, 2 failed |
| BI SQL parity/idempotency/role | Passed |
| UI route snapshots | 10 route × 2 widths; không page overflow hoặc pageerror trong snapshot |

E2E chạy Edge trên host gọi production server Docker. Không dùng `npm ci` trong container Playwright ở lượt này. Live AI có pass/fail xen kẽ: roadmap và CV thường trả 503, scan OCR/Gemini và phỏng vấn thành công. Log provider có HTTP 503 và retry. Chưa kết luận toàn bộ AI ổn định.

## Phát hiện quan trọng

Ca chẩn đoán trực tiếp gọi engine trên JD có Python, SQL, Docker, FastAPI, Git và minimumExperienceYears=5:

| Input | Điểm |
|---|---|
| Profile có đủ skill, không CV | 92 |
| Cùng profile và CV có đủ skill | 84 |
| CV có đủ skill, kinh nghiệm 1 năm | 84 |
| CV có đủ skill, kinh nghiệm 8 năm | 84 |

Đây là lỗi/thiếu sót của policy scoring, không được che bằng giảm điểm hàng loạt. Unit tests hiện tại chưa bao phủ tính nhất quán theo nguồn và tác động của kinh nghiệm. `scoreFactors` còn thiếu các cap/calibration sau model.

Dashboard real có 635 jobs, 1 candidate và salary coverage 4% tại lúc chụp. SQL đúng trên dữ liệu hiện có, nhưng mẫu chưa đủ để kết luận xu hướng thị trường rộng.

## Nhận xét giao diện từ render

### Landing — ROUND 1

Seen in one second: tiêu đề tìm việc và bảng minh họa job.
Idea (one sentence): CV của ứng viên kết nối với cơ hội và khoảng trống kỹ năng có bằng chứng.
Live thing: chuyển minh họa ứng viên/nhà tuyển dụng và CTA đăng ký.
Layout words by section: hero=split / workflow=split / recruiter=split / roles=columns / FAQ=split / CTA=split.
Scores (nhận xét chủ quan cho giao diện hiện tại): design 6.5 · usability 7 · creativity 6 · content 7 → overall 6.6, cap 6.0 theo inspector motion. Cap motion là tiêu chí riêng của skill, không phải điều kiện TH3 và không dùng làm lý do thêm animation không cần thiết.
Caps applied: inspector still-page; cảnh báo contrast có giá trị thực tế cao hơn số lượng chuyển động.
Top three problems:

1. Chữ nhãn minh họa tương phản 3.7–3.8:1 trên cả ba viewport. Tăng contrast tới ≥4.5:1.
2. Tablet có margin lệch 30/47px, nhiều nội dung minh họa bị cắt ngắn. Chuẩn hóa container, giãn preview theo breakpoint.
3. Nhiều khối split và điểm demo 94% lặp lại. Giữ hero và avatar công ty; giảm preview lặp và nhãn số minh họa.

### App screens

- Jobs: banner chiếm vùng lớn, row đầu ở y≈639 desktop/y≈906 mobile (viewport cao 900); text metadata/CTA nhỏ. Hạ banner thành status strip, search đứng đầu, row đầu mobile mục tiêu y≤500.
- Profile: CV dưới form dài; 19 skill chiếm 19 hàng full-width; xác nhận xa chỗ bắt đầu. Đưa CV lên ưu tiên, tabs, chip skill và evidence bên cạnh PDF.
- Analytics: khối skills 20 hàng kéo dài cột category, khoảng trắng lớn; lương/funnel xuống nhiều màn hình. Top 8–10 skills và grid cân nội dung; bảng chi tiết tách tab.
- Post-job: AST threshold 85 vẫn có control nổi bật dù dịch vụ AST chưa triển khai. Ẩn khỏi luồng chính hoặc chỉ giữ metadata có nhãn rõ.
- Coaching/interview: select job chứa danh sách lớn, chưa search; form và notice tách rời, feedback cần trạng thái xử lý/retry dễ thấy.

Ảnh và JSON đo ở `artifacts/audit-2026-11-05/`; artifact có thể chứa hồ sơ cá nhân, giữ local. Không thêm ảnh/asset mới cho đợt review. Source linter báo 2 FAIL/28 WARN nhưng một FAIL là placeholder email example.com hợp lệ trong form, không phải bug. Nhận xét dựa trên render và tác vụ thực tế, không đồng nhất lint style với lỗi ứng dụng.

## Hành động

Xem [kế hoạch nghiệm thu và UI refactor](../plans/th3-release-and-ui-refactor.md) để triển khai theo P0/P1, thứ tự và acceptance criteria. Đánh giá “5/5 có chức năng” trước đó cần phân biệt với “đã nghiệm thu đầy đủ”: lỗi scoring và live AI trong đợt này cho thấy chưa đủ bằng chứng để gọi hoàn tất 100%.
