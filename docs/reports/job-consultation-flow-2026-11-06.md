# Luồng Job → Tư vấn CV → Checklist — 06/11/2026

> Tài liệu lịch sử. Giao diện sản phẩm hiện tại đã gỡ checklist 6 yêu cầu, phần quay/nộp video
> và các nội dung bài tập khỏi trang tư vấn và bản xuất Markdown. Xem [hướng dẫn hiện tại](../guides/cv-review.md).

## Quyết định giao diện

Bắt đầu từ job phù hợp mục tiêu nghề nghiệp giúp người dùng hiểu ngay CV được tư vấn cho vị trí nào.
Luồng này giảm việc quay sang công cụ độc lập rồi tìm lại JD:

`Việc làm → Tư vấn CV → CV đúng phiên bản + JD đã chọn → gap/BI → Outline → chuẩn bị video`

Một ca vẫn gắn với một JD. Bấm tư vấn ở job khác mở một đầu vào khác, không gộp các yêu cầu
của nhiều công việc để tạo khoảng trống giả. Bản phân tích đã lưu vẫn giữ snapshot bất biến.

## Đã triển khai

- Nút **Tư vấn CV** trên từng hàng việc làm; **Tư vấn CV theo JD này** tại trang chi tiết.
- Truyền `jobId` qua URL `/student/cv-review?jobId=…`; route server chuyển vào form client.
  Tên vị trí/công ty hiển thị ở đầu form, reload giữ context. Không hiện lại bộ chọn nguồn JD
  hay vị trí mục tiêu khi đã vào từ job; người dùng chỉ chọn CV đã tải lên.
- Với luồng từ job, checklist nằm ở cột bên desktop và dưới form trên mobile để ô chọn CV
  xuất hiện trong màn hình đầu.
- Với luồng bắt đầu từ job, tải đúng `/api/jobs/{id}` thay vì xếp hạng toàn bộ danh sách job.
- Không tải được JD thì báo lỗi và không âm thầm chọn job khác; có link quay về danh sách job.
- Checklist 6 mục tại trang chọn đầu vào và trang ca tư vấn, liên kết đến phần liên quan.
  JD/gap/Outline phản ánh đầu vào hiện tại; thay đổi draft chưa lưu được ghi rõ.
- CV thật/quyền sử dụng, video và việc nộp do người dùng xác nhận. Ghi trạng thái tham khảo,
  không tuyên bố chấm đạt, xác minh video hoặc nộp đúng hạn tự động.
- Tách label của JobSelector khỏi nội dung option để truy vấn nhãn rõ ràng và ổn định.
- Giữ menu Tư vấn CV, cách dán JD riêng khi mở trang trực tiếp và các ca tư vấn cũ.

## Checklist hiển thị

1. Chọn CV thực tế — phân biệt đã chọn file và người dùng xác nhận quyền sử dụng.
2. Chọn JD cụ thể — job đang xem được điền sẵn.
3. BI & AI: ít nhất 3 skill gaps — số gap được chọn, cần kiểm tra bằng chứng và BI.
4. Đề xuất Outline CV mới — phân biệt đã tạo và đã xem lại.
5. Quay video 2–3 phút — thời lượng do người dùng nhập, đối chiếu khoảng 120–180 giây.
6. Nộp video đúng hạn — tự xác nhận và tự kiểm tra hạn trên hệ thống lớp.

## Kiểm chứng

- ESLint, TypeScript và Docker production build đạt.
- Audit trang tư vấn có job context trên Docker chính: 1440/768/390, đúng 6 mục,
  không JS pageerror/tràn ngang; probe/layout/app của design-taste-frontend không có finding.
  Ô chọn CV nằm trong viewport 900px ở cả ba kích thước (y=591/681/743).
- Đã xem ảnh render desktop và mobile. Giữ phong cách Framed sheet, palette/type hiện có;
  checklist dùng bố cục 3 cột desktop, 2 cột tablet/mobile; không thêm hero hoặc số liệu minh họa.
- E2E mới kiểm tra cả link trên card và chi tiết, reload, JD đi vào snapshot chính xác,
  sáu mục checklist trước/sau tạo ca và mobile không tràn ngang.
- Vòng đầu: 36 ca cũ đạt, hai ca mới dừng ở truy vấn exact label do label chứa option text.
  Đã sửa markup nhãn/select; không hạ điều kiện đối chiếu JD hoặc đổi expected status.
- Vòng trước khi sửa theo phản hồi: **38/38 Docker offline E2E passed**, 0 skip/flaky; 70.1 giây. Hai ca mới desktop/mobile đều đạt. Provider fixture chỉ dùng cho tác vụ sinh nội dung; các dịch vụ khác chạy thật.
- Sau phản hồi về ô chọn JD bị lặp, đã khóa JD theo `jobId`, ẩn hai ô chọn JD và đưa phần chọn CV lên đầu. E2E kiểm tra job ID trong snapshot sau khi tạo ca. Vòng cuối sau sửa bố cục: **38/38 Docker offline E2E passed** trên desktop/mobile, không retry.
- Audit Docker chính sau sửa ở 1440/768/390px: ô chọn CV bắt đầu tại y=423/417/399 trong viewport 900px; 6 checklist mục, không tràn ngang, không JS pageerror hay finding từ bộ kiểm tra giao diện. Đã xem ảnh desktop/mobile tại `artifacts/job-consultation-2026-11-06/ui-fixed/`.
- Bản Docker chính đã cập nhật; các container test đã dừng, không đổi dữ liệu CV/đơn ứng tuyển thật.

Artifact tại `artifacts/job-consultation-2026-11-06/`: `initial-e2e`, ảnh/audit UI và kết quả cuối.
Không tạo CV thật hoặc ca tư vấn trên volume nghiệp vụ trong lúc kiểm thử; Docker test dùng project riêng.
