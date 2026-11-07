# Đánh giá Docker E2E, luồng CV–JD và bài nộp — 06/11/2026

## Kết luận

Hệ thống đã có các chức năng cần để chuẩn bị bài “Phân tích CV và Skill Gaps bằng mô hình BI & AI”.
Luồng dùng được cho demo; việc hoàn thành ứng dụng không đồng nghĩa đã hoàn thành bài nộp video.
Cần tạo một ca CV thật–JD cụ thể, rà soát 3+ gap và bản Outline trước/sau, đọc thử và quay video 2–3 phút,
rồi nộp đúng hạn theo hướng dẫn lớp.

Kiểm tra từ mã nguồn hiện tại, Docker thật và trình duyệt, không dùng kết quả chạy host thay thế cho Docker.
Đã tham khảo hai báo cáo DOCX tại `docs/research`; các mô tả S-BERT/AST/Voice trong đề xuất không phải
bằng chứng những mô-đun đó đang chạy. Runtime hiện tại là matching hybrid local + Gemini, OCR và BI/ETL.

## Những vấn đề đã xử lý trong đợt kiểm tra

1. **Docker cũ chưa có tính năng mới:** `/student/cv-review` ở cổng 3000 ban đầu trả 404.
   Đã build lại stack chính sau khi có kết quả Docker test và sao lưu; trang mới hoạt động.
2. **Restore chưa theo schema mới:** script còn chặn version >4. Đã dùng `SCHEMA_VERSION`
   chung từ DB cho guard restore; kiểm tra phục hồi bản sao có cả hai bảng tư vấn v5.
3. **Danh sách việc làm lỗi làm mất danh sách CV trên UI:** tiêm HTTP 503 cho `/api/jobs`
   ở trình duyệt demo trên stack chính, API vẫn có 4 CV nhưng UI hiển thị 0 và báo sai chưa có CV.
   Nguyên nhân `Promise.all` làm bỏ cả kết quả tải CV/lịch sử khi một request lỗi.
   Đã đổi sang tải độc lập, thông báo theo nguồn; cho dùng JD riêng, không báo không có CV khi tải CV lỗi.
   Bổ sung E2E desktop/mobile đi tới tạo ca tư vấn bằng JD riêng trong tình huống này.

Sao lưu trước migration: `var/backups/2026-11-06T12-09-18.158Z/` có SQLite, dump PostgreSQL mart và Metabase.
Đối chiếu trước/sau: **221 users, 640 jobs, 179 CV, 5 đơn ứng tuyển**, giữ nguyên;
SQLite `integrity_check=ok`, schema **4 → 5**. Hai bảng tư vấn mới ban đầu chưa có record.
Không chạy E2E tạo user/CV/đơn trên volume nghiệp vụ. Các lần đăng nhập quan sát UI dùng tài khoản demo có sẵn.

## Bằng chứng đã thu thập

- Docker project chính `unitalent`: 6 services healthy; web 3000, Metabase 3001.
  AI chính `APP_ENV=production`, `AI_TEST_FIXTURES=false`.
- E2E baseline offline trong project `unitalent-test-cv-review`: **34/34 passed**, 67,8s,
  0 skip/flaky. Ứng dụng/auth/SQLite/OCR/PostgreSQL/Metabase chạy thật; tác vụ sinh nội dung dùng fixture được ghi nhãn.
- E2E Gemini thật trong project `unitalent-test-cv-review-live`: **34/34 passed**, 105,8s,
  0 skip/flaky, không có `upstream-transient-retry` từ thao tác UI; attachment có
  `gemini:gemini-3.5-flash-lite`. Client vẫn có cơ chế retry/fallback tự động.
  Các ca chủ động trả 503 chỉ kiểm chứng giao diện lỗi, không được tính như gọi provider thành công.
- Các ca bao gồm CV cũ/mới, JD riêng, 3 gap, Outline/lưu/reload/export, giữ draft khi lỗi,
  đăng nhập/phân quyền, biến thể PDF, OCR scan thật, tuyển dụng hai user/CV snapshot,
  coaching/phỏng vấn và sáu câu hỏi Metabase.
- Python: **83 passed**, cảnh báo deprecation Starlette/httpx có sẵn.
- `bi:verify`: parity SQL, idempotency, role aggregate-only và không raw PII columns đạt.
  Mart tại thời điểm đo: job 640, candidate skill 86, stage 8.
- `db:verify-recovery`: SQLite v5 trên bản sao đạt, gồm bảng tư vấn; PostgreSQL mart restore
  vào DB tạm đạt, counts `640|86|8`; DB tạm đã dọn.
- Đã xem UI Docker ở 1440/768/390: profile, tư vấn CV, skill-gap, tổng 9 snapshot;
  không pageerror hoặc tràn ngang. Trang tạo tư vấn mới không có finding;
  profile/skill-gap cũ còn cảnh báo tương phản ở một số nhãn phụ.
- Docker build chạy lint/type validation thành công. Không sửa version dependency dựa trên warning npm.

Regression sau sửa lỗi tải danh sách: **36/36 Docker offline E2E passed**, không skip/flaky,
bao gồm 2 ca mới desktop/mobile chứng minh vẫn chọn CV và tạo ca bằng JD riêng khi `/api/jobs` trả 503.
Trên Docker chính, phép thử read-only sau sửa cũng thấy 4 CV từ API và 4 lựa chọn trên giao diện,
không còn thông báo sai “chưa có CV”. Bản sửa frontend đã build và áp dụng ở cổng 3000.
Kết quả live 34 ca ở trên được thu trước khi bổ sung hai ca lỗi danh sách;
hai ca mới không gọi Gemini, được kiểm tra bằng lượt offline cuối.

## Đối chiếu 6 yêu cầu bài nộp

| Yêu cầu | Hệ thống hỗ trợ | Điều kiện để coi bài nộp đã hoàn thành |
|---|---|---|
| 1. CV thực tế | Upload PDF, OCR, chọn phiên bản, xác nhận extraction | Người học chọn CV thật và có quyền sử dụng; test dùng CV synthetic không chứng minh mục này |
| 2. JD cụ thể | Chọn job hoặc dán JD riêng, snapshot giữ nguyên | Chọn JD đúng mục tiêu nghề nghiệp, nêu vị trí/công ty/nguồn/ngày truy cập nếu có |
| 3. BI & AI, ít nhất 3 gap | Matching + quote CV/JD, Gemini, BI nhu cầu, chọn gap | Rà soát 3+ gap có căn cứ cho chính cặp CV–JD; nêu thiếu minh chứng hay cần học thêm; giải thích BI/AI đã dùng |
| 4. Outline CV mới | AI đề xuất thứ tự, quote và advice; sửa/lưu/xuất | Trình bày bố cục trước/sau và giải thích từng thay đổi liên quan các gap; không thêm kỹ năng chưa có như thành tích |
| 5. Video 2–3 phút | Có lời thoại và checklist | Tự quay, đóng vai tư vấn, giới thiệu → CV/JD → 3 gap → Outline mới; kiểm tra file thực tế dài 120–180 giây |
| 6. Nộp đúng hạn | Cho nhập hạn và tự xác nhận đã nộp | Kiểm tra hạn của lớp và kết quả nộp trên hệ thống; ứng dụng không truy cập/xác minh cổng bài tập |

Tại thời điểm kiểm tra, bảng tư vấn ở volume chính có **0 ca**. Vì vậy không xác nhận được một ca
CV thật–JD đã hoàn chỉnh để nộp. Không dùng số lượng PDF, test pass hoặc checkbox tự khai để thay bằng chứng này.
Các video có sẵn chưa được xác minh đáp ứng đề bài lần này; không suy ra đã nộp từ file trên máy.

## Nhận xét về giải pháp BI & AI

**Đúng hướng:** đối chiếu CV với JD theo từng yêu cầu, phân biệt nguồn bằng chứng/tự khai báo,
không ép đủ 3 gap, giữ snapshot, có Outline và hành động học tách riêng. Điểm `/100` đã ghi là tham khảo.
BI có nguồn/mẫu số/dataset thật; đối soát SQL và quyền được kiểm thử.

**Giới hạn phải nói rõ khi trình bày:** skill matching chủ yếu theo taxonomy và cosine/weights local;
Gemini đọc CV và tổ chức Outline, không xác minh năng lực thực tế. Đã kiểm tra vận hành và nguồn trích,
chưa đo độ chính xác trên gold CV/JD độc lập. Thiếu từ khóa không tự chứng minh thiếu kỹ năng.
Không gọi runtime là S-BERT/GNN/AST/Voice nếu demo đang không sử dụng các mô-đun đó.

Dataset real hiện có **635 tin, 1 ứng viên, 25 tin có lương parsed** (~3,9%).
Đủ minh họa nhu cầu kỹ năng trong dataset; chưa đủ suy ra nguồn cung ứng viên, mặt bằng lương hoặc
xu hướng toàn thị trường. Không cần làm một nghiên cứu model quy mô lớn chỉ để đáp ứng bài video này.

## Đánh giá luồng giao diện và backlog

Luồng hiện tại hợp lý về nghiệp vụ:

`Hồ sơ / tải CV → Tư vấn CV / chọn CV–JD → kiểm tra bằng chứng → gap → Outline trước–sau → BI → lời thoại / xuất`

Điểm tốt: có entry trong menu/profile/skill-gap, không tự chọn JD thay người dùng,
bằng chứng đứng gần kết luận, lưu/reload/export hoạt động, xử lý 503 giữ nội dung,
mobile không tràn ngang. Các trạng thái quan trọng đã có kiểm thử.

Các điểm nên cải thiện, **chưa triển khai trong lượt review này**:

| Ưu tiên | Vấn đề | Cải thiện đề xuất |
|---|---|---|
| P1 | Upload ở profile, chọn/xác nhận ở tư vấn; luồng bị chia đôi | Cho upload tại bước chọn CV, giữ một lần xác nhận theo đúng phiên bản; chỉ báo rõ bước 1–4 |
| P1 | Chi tiết mobile test dài khoảng 5811px; nhiều control chỉnh sửa | Thêm bản trình bày chỉ 3 gap, bảng trước/sau và 1–2 số BI; editor thu gọn riêng |
| P1 | Gap action hiện còn chung; gapIds có trong Outline nhưng chưa hiện nhãn liên kết ở editor | Hiện rõ mỗi gap → việc cần làm → section/bullet nào nên đổi; cho nhập minh chứng/kế hoạch thực tế |
| P1 | Kịch bản mẫu test 291 từ, ứng dụng ước lượng 97s ở 180 từ/phút | Đọc thử và bổ sung phân tích riêng cho 120–180s; có thể thêm phân bổ thời lượng tự điều chỉnh, không hứa thời gian chính xác |
| P1 | Chỉ có guard beforeunload; điều hướng SPA chưa chặn rời draft | Kiểm tra/cảnh báo khi bấm menu/link rời trang còn thay đổi chưa lưu; thêm E2E cho trường hợp này |
| P2 | Profile/skill-gap cũ còn text phụ contrast 2,6–4,1:1 | Tăng tương phản, chuẩn hóa nhãn điểm và kích thước đọc ở mobile |
| P2 | CV/JD thay đổi nhiều nhưng script đã tạo được giữ nguyên | Hiện nhãn lời thoại cần xem lại hoặc cho tạo lại rõ ràng khi gap/Outline đổi |

Chưa cần thiết kế lại toàn bộ app hoặc thêm AST/voice để làm bài này.
Ưu tiên trước nộp là một ca tư vấn cụ thể, giải thích được và một video đủ thời lượng.

## Artifact

- `artifacts/docker-review-2026-11-06/offline/`: bản E2E baseline 34 ca.
- `artifacts/docker-review-2026-11-06/offline-final/`: 36 ca E2E cuối sau sửa, HTML report và JSON.
- `artifacts/docker-review-2026-11-06/live/`: bản Gemini thật 34 ca, HTML report và JSON.
- `artifacts/docker-review-2026-11-06/ui/`: ảnh và `audit.json` trên Docker chính.
- `artifacts/docker-review-2026-11-06/job-list-outage.json`: phép thử tiêm lỗi trước sửa.
- `artifacts/docker-review-2026-11-06/job-list-outage-fixed.json`: phép thử cùng lỗi sau sửa.
- Backup dữ liệu nằm ở `var/backups/`, không commit CV/dữ liệu cá nhân vào Git.

Các project test được dừng sau test; Docker chính được giữ chạy cho người dùng.
