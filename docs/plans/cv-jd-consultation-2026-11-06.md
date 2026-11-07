# Kế hoạch bổ sung tư vấn CV theo JD và Outline CV

Ngày kiểm tra: **06/11/2026**. Baseline: `b8da64d`.
Trạng thái: **P0/P1 đã được triển khai ngày 06/11/2026**; xem [hướng dẫn sử dụng](../guides/cv-review.md) và [báo cáo kiểm chứng](../reports/cv-review-implementation-2026-11-06.md).
Phần kết luận kiểm tra bên dưới giữ nguyên hiện trạng trước triển khai để đối chiếu.

## 1. Kết luận kiểm tra

UniTalent AI đã có nền tảng phân tích CV, matching, coaching và BI. Tuy nhiên,
chưa có luồng hoàn chỉnh lưu một ca CV–JD, đối chiếu bằng chứng từng yêu cầu,
đề xuất Outline CV mới và chuẩn bị nội dung video tư vấn 2–3 phút.

| Hạng mục | Bằng chứng trong mã nguồn | Kết luận |
|---|---|---|
| Upload PDF, đọc chữ/OCR, phân tích và xác nhận | `services/api/app/main.py`: `/api/resumes`, `…/analyze`, `…/analysis`; `resume_analysis.py`; `ResumeManager.tsx` | Có; tái sử dụng |
| Chọn JD từ hệ thống | `JobSelector.tsx`, trang `student/skill-gap`, `coaching_target()` | Có; khi chưa chọn, backend tự lấy việc được gợi ý đầu tiên |
| Chọn một phiên bản CV cho ca tư vấn | `matching_input()` và `/api/resumes/current` lấy CV mới nhất; `CoachingRequest` chỉ có `jobId`, `hoursPerWeek` | Chưa có trong luồng coaching |
| Kỹ năng khớp/thiếu, must-have và bằng chứng | `services/ai/app/engine.py`: `match()` trả `matchedSkills`, `missingSkills`, `missingMustHaveSkills`, `unknownRequirements`, `evidence` | Có nền tảng; chưa phải ma trận tư vấn từng yêu cầu |
| Giải thích khoảng trống kỹ năng | `/api/skill-gap` lấy `missingSkills`, gắn mô tả chung; `generate_skill_gap()` chỉ thêm summary và roadmap | Có một phần; các thẻ gap chưa giải thích riêng bằng trích dẫn JD/CV |
| Tái cấu trúc Outline CV | AI `ResumeExtraction` chỉ có skills/experience/education/projects/unknown; `Plan` chỉ có summary/roadmap; không có endpoint/schema/UI outline | Chưa có |
| BI cho ca tư vấn của sinh viên | `analytics.py` đã tính nhu cầu kỹ năng; `/api/analytics` yêu cầu recruiter | Có BI nền tảng; chưa có phần BI riêng cho ca tư vấn sinh viên |
| Lưu bản phân tích CV–JD để trình bày | Có snapshot khi ứng tuyển, learning plan theo input hash; chưa có bảng ca tư vấn/outline | Chưa có; không dùng đơn ứng tuyển để thay thế ca tư vấn |
| Kịch bản video, kiểm tra 6 mục | Chưa có route/schema/UI tương ứng | Chưa có |

Các thẻ skill-gap hiện chưa phản ánh ưu tiên must-have: mặc định `importance='recommended'`.
Nhãn hiện tại “Chưa nhận diện trong hồ sơ” chưa phân biệt thiếu minh chứng CV và thiếu kỹ năng thực sự.
Trang skill-gap còn hiển thị điểm bằng `%`; nên thống nhất `/100` theo ý nghĩa điểm matching.

### Phạm vi đã xác minh

- Kiểm tra tĩnh source API/AI/frontend, schema SQLite và tài liệu/báo cáo hiện có.
- Lượt kiểm tra trước cùng ngày: 72/72 Python tests, ESLint và TypeScript đạt.
- Artifact `artifacts/e2e/results.json` ngày 05/11: 30 ca đạt, 0 lỗi/skip/flaky;
  attachment có provenance `gemini:*`. Báo cáo sửa provider tại
  [Gemini reliability](../reports/gemini-reliability-2026-11-05.md).
- Docker daemon chưa chạy, chưa kiểm thử lại stack live hoặc đọc database trong volume Docker.
- SQLite local đọc bằng kết nối read-only: 67 users, 39 resumes, 638 jobs;
  chưa có các bảng `resume_analysis`, `learning_plans`, `entity_metadata` của schema mới.
  Đây là database local cũ, không được suy ra trạng thái dữ liệu Docker. Không chạy migration trong lượt kiểm tra này.
- Chưa xác minh được một cặp CV thật–JD và video đáp ứng đủ đề bài. Sự tồn tại của PDF/video
  không chứng minh nội dung phù hợp. Phụ đề `media/TranVanTai-0548.srt` mô tả bài giới thiệu
  hệ thống đến khoảng 09:37; chưa xem/nghe hết các video khác.

## 2. Phạm vi bản bổ sung

Tạo chức năng **Tư vấn CV theo JD**, dùng chung tài khoản, CV, matching và Gemini hiện có.
Mục tiêu bắt buộc là chọn đầu vào rõ ràng, phân tích có bằng chứng và đề xuất Outline CV có thể chỉnh sửa/lưu.
Phần kịch bản/checklist là hỗ trợ chuẩn bị bài nộp, không thay việc người học quay và nộp video.

Không cần thay kiến trúc database, làm lại matching, thêm AST/voice, tự quay video hoặc
tích hợp cổng nộp bài trong đợt này. Không cần gold dataset mới để nghiệm thu chức năng outline;
đánh giá độ chính xác model thực tế vẫn là backlog riêng.

Luồng người dùng:

`Chọn CV → chọn/nhập JD → kiểm tra trích xuất → xem ma trận gap và BI → chỉnh Outline đề xuất → lưu/xuất → chuẩn bị video`

## 3. Backlog theo thứ tự triển khai

### P0.1 — Chọn và lưu cố định CV–JD

- Thêm danh sách metadata CV của chính tài khoản; cho chọn phiên bản và xem PDF.
- Bắt buộc chọn JD rõ ràng khi tạo ca tư vấn; không âm thầm lấy job đứng đầu danh sách.
- Cho dán JD ngoài hệ thống với tên vị trí, công ty, nội dung; URL/ngày truy cập tùy chọn.
  JD này lưu riêng trong ca tư vấn, không tạo tin công khai hoặc giả owner nhà tuyển dụng.
- Lưu snapshot CV text, analysis đã xác nhận, JD, tín hiệu profile dùng bổ trợ,
  content hashes, schema/scorer version và thời điểm tạo. CV file vẫn tham chiếu bản PDF gốc.
- Chọn CV cũ phải truyền đúng `resumeId` đến matcher; không dùng helper mặc định CV mới nhất.
- Khi người dùng xác nhận extraction thủ công, phân biệt kỹ năng có trích dẫn và tự khai báo;
  xác nhận của người dùng không tự biến thành bằng chứng trong PDF.

Nghiệm thu: tải CV mới hoặc sửa JD/profile không làm đổi báo cáo đã lưu; có thể chủ động tạo bản mới.
Người khác không đọc/đổi được CV, JD riêng hoặc ca tư vấn.

### P0.2 — Ma trận yêu cầu, bằng chứng và khoảng trống

- Mỗi dòng: yêu cầu JD + câu trích, kỹ năng chuẩn hóa, must-have/nice-to-have/không rõ,
  bằng chứng CV hoặc tự khai báo, trạng thái đối chiếu, giải thích và hành động.
- Tách trạng thái: **có minh chứng trong CV / chỉ tự khai báo / chưa thấy minh chứng /
  người dùng xác nhận cần học thêm / chưa đủ dữ liệu để đánh giá**.
- Không suy ra thiếu năng lực chỉ từ việc CV không nhắc tới kỹ năng; không suy ra trình độ thành thạo
  hoặc số năm kinh nghiệm từ keyword.
- Tái sử dụng matching để dựng dữ liệu định lượng; Gemini chỉ diễn giải từ đầu vào được kiểm chứng.
  Yêu cầu ngoài taxonomy chuyển “chưa đánh giá”, cho người dùng kiểm tra/bổ sung có provenance.
- Ưu tiên must-have trước, sau đó tham khảo tần suất trong dataset BI; cho chọn gap dùng để trình bày.
- Hiện số gap có căn cứ. Nếu ít hơn 3, báo chưa đủ cho yêu cầu bài tập và hướng dẫn rà soát CV/JD;
  không sinh thêm gap giả, không tách alias thành nhiều kỹ năng để đủ số lượng.

Nghiệm thu: mỗi gap dẫn về yêu cầu JD thật và tình trạng bằng chứng; trả 0/1/2/3+ gap đúng dữ liệu.

### P0.3 — Đề xuất Outline CV theo JD

- Nhận diện các section hiện có từ heading/text; cho người dùng sửa/xác nhận nếu PDF mất bố cục
  hoặc OCR chỉ đọc được một phần. Không mặc định projects/education trích xuất chính là toàn bộ Outline cũ.
- Gemini trả JSON theo schema: thứ tự section mới, mục đích, lý do đổi vị trí,
  bullet đề xuất, tham chiếu bằng chứng và gap liên quan.
- Bố cục tùy CV/JD; ví dụ cho sinh viên: Thông tin liên hệ → Tóm tắt mục tiêu →
  Kỹ năng liên quan → Dự án nổi bật → Kinh nghiệm → Học vấn/chứng chỉ.
  Không bắt buộc mọi người dùng theo cùng thứ tự.
- Mỗi hành động thuộc một trong ba loại: **đưa minh chứng sẵn có lên trước / viết rõ hơn từ dữ kiện có thật /
  cần học hoặc làm dự án trước khi bổ sung**.
- Gợi ý mới chưa có chứng cứ nằm trong kế hoạch học, không nằm như thành tích đã đạt trong CV đề xuất.
  Không tự thêm số %, doanh thu, số người dùng, chứng chỉ hay số năm kinh nghiệm.
- UI đối chiếu “Bố cục hiện tại / Bố cục đề xuất”, cho sửa text/thứ tự bằng nút lên/xuống,
  chấp nhận/bỏ gợi ý, lưu draft và đánh dấu đã xem lại.
- API kiểm tra schema và trích dẫn/source IDs; đầu ra không có căn cứ không được gắn nhãn đã xác minh.
  Lỗi Gemini giữ nguyên draft và cho thử lại theo cơ chế provider đang có.

Nghiệm thu: ít nhất một ca có gap dẫn tới thay đổi Outline/bullet cụ thể; kỹ năng thực sự thiếu
được gắn hành động học/thực hành, không được “khắc phục” bằng cách ghi thêm kỹ năng vào CV.

### P0.4 — Kết nối BI và lưu/xuất báo cáo

- Bổ sung endpoint student chỉ trả thống kê tổng hợp về các kỹ năng trong ca tư vấn,
  tái sử dụng chuẩn hóa/dedup/dataset real trong `analytics.py`.
- Hiển thị `jobCount / totalJobs`, tỷ lệ demand, bộ lọc, nguồn và thời điểm truy vấn,
  khoảng ngày đăng/quan sát nếu có; lưu cùng snapshot phân tích.
- Nêu rõ số liệu của dataset hệ thống, không phải xác suất được tuyển hay thống kê toàn thị trường.
  Dataset rỗng/ít mẫu phải có trạng thái rõ; không tự sinh tỷ lệ hoặc trộn demo/test.
- Không mở quyền recruiter analytics/funnel cho student; không đưa CV/PII vào mart.
- Lưu lịch sử ca tư vấn và bản chỉnh sửa; xuất Markdown hoặc trang in để dùng khi quay video.
  Tải xuống phải xác thực owner, escape nội dung, có lựa chọn ẩn thông tin liên hệ.

Nghiệm thu: số BI đối soát được với query trên cùng bộ lọc; bản xuất giữ cùng CV/JD/gaps/Outline/BI snapshot.

### P1 — Hỗ trợ video 2–3 phút và checklist bài nộp

- Tạo kịch bản từ bản phân tích đã được xem lại, gồm mở đầu, CV/JD, 3+ gap và Outline mới.
- Gợi ý phân bổ 150 giây: 15s giới thiệu, 20s CV/JD và cách dùng BI/AI,
  65s phân tích 3 gap, 40s Outline mới, 10s kết thúc.
- Cho sửa tên/lời thoại, copy/xuất; ghi thời lượng chỉ là ước lượng, cần đọc thử/quay thực tế.
- Checklist: CV thật và quyền sử dụng do người dùng xác nhận; JD cụ thể; số gap có căn cứ;
  Outline đã xem lại; người dùng xác nhận video dài 120–180s; người dùng xác nhận đã nộp.
- Có thể nhập hạn nộp; không tự đoán thời hạn, không tự đánh dấu đã nộp hoặc gọi kết quả là được giảng viên nghiệm thu.
- Nếu chưa đủ 3 gap, vẫn cho lưu/xuất bản nháp nhưng không đánh dấu phần này đã đủ yêu cầu.

## 4. Thiết kế kỹ thuật dự kiến

Đề xuất module riêng, tránh tiếp tục dồn logic vào `main.py`:

| Thành phần | Thay đổi dự kiến |
|---|---|
| API | `services/api/app/consultations.py`, `consultation_schemas.py`, `consultation_service.py`; mount router trong `main.py` |
| Persistence | Migration additive sau v4: `cv_consultations` lưu owner/resume/input snapshot/hash/status; `cv_consultation_revisions` lưu output, edits, provenance và thời điểm |
| AI | `services/ai/app/cv_outline.py`: schema/generator; thêm endpoint `/resume/outline` dùng `generate_json` và metadata provider thực tế |
| Frontend | `/student/cv-review` và `/student/cv-review/[id]`; link từ profile và skill-gap; component dùng lại PDF/JobSelector, API client, toast, workspace tokens |
| Kiểm thử | `services/api/tests/test_consultations.py`, `services/ai/tests/test_cv_outline.py`, bổ sung workflow E2E |

API dự kiến:

- `GET /api/resumes`: metadata các phiên bản CV thuộc tài khoản; không trả BLOB hàng loạt.
- `POST /api/cv-consultations`: tạo snapshot từ `resumeId` và `jobId` **hoặc** `customJd`.
- `GET /api/cv-consultations` và `GET /api/cv-consultations/{id}`: danh sách/chi tiết theo owner.
- `POST /api/cv-consultations/{id}/analyze`: dựng ma trận gap/BI và sinh Outline; xử lý lặp/idempotency theo input hash và version.
- `PATCH /api/cv-consultations/{id}`: lưu lựa chọn gap, Outline edits và trạng thái xem lại bằng revision check.
- `GET /api/cv-consultations/{id}/export`: tải bản Markdown có lựa chọn ẩn liên hệ.
- P1: `POST …/{id}/script`, `PATCH …/{id}/checklist`.

Snapshot bất biến; thay input tạo ca/bản mới. Output giữ cả AI gốc và bản người dùng sửa,
`schemaVersion`, `scorerVersion`, `method`, prompt version và refs hợp lệ. Không dùng model tự khai provenance.
Ngăn hai tab ghi đè bằng `revision`/409; UI xử lý đang chạy, lỗi, rỗng, thiếu CV/JD, OCR một phần,
chưa xác nhận và thay đầu vào trong khi request đang chạy. Không overwrite draft khi đổi lựa chọn hoặc retry.

Kiểm tra trường hợp schema local cũ: backup trước migration, chạy trên bản sao và thử khởi tạo lặp.
Không tự chuyển dữ liệu local sang volume Docker hoặc đánh đồng hai nguồn dữ liệu.

## 5. Tiêu chí kiểm thử và bàn giao

- [ ] Ownership: không đọc/xuất/sửa CV hoặc ca tư vấn tài khoản khác; student không gọi recruiter funnel.
- [ ] Snapshot: chọn đúng CV cũ; upload CV mới, sửa profile/JD/analysis không làm đổi ca đã lưu.
- [ ] Gaps: must-have đúng, alias không nhân đôi; 0/1/2 gap không bị ép thành 3;
  unknown requirements và tự khai báo không bị coi là minh chứng CV.
- [ ] Outline: quote/source ID không có thật bị loại; thành tích/số liệu thiếu căn cứ không được duyệt tự động;
  prompt trong CV/JD không điều khiển system instructions.
- [ ] Failure: provider 503/timeout/JSON sai giữ draft, lỗi rõ; request lặp và revision conflict xử lý đúng.
- [ ] BI: đối soát count/denominator/filter; rỗng/ít mẫu; không lọt dữ liệu test/demo hoặc dữ liệu cá nhân người khác.
- [ ] Migration: database v1/v4 trên bản sao, idempotency, giữ CV/đơn ứng tuyển cũ và foreign keys.
- [ ] E2E desktop/mobile: chọn CV/JD → xác nhận → gap/BI → Outline → sửa/lưu → reload/xuất;
  keyboard, focus, nút có nhãn, text dài, không tràn ngang. Trạng thái loading/success/error hiển thị rõ.
- [ ] Offline E2E fixture và live Gemini được ghi riêng; kiểm tra metadata provider thật;
  Python/lint/typecheck/build đạt; không biến lỗi live thành pass bằng fixture.
- [ ] Ca nghiệm thu thực: người dùng chọn một CV có quyền sử dụng, một JD cụ thể,
  kiểm tra thủ công ít nhất 3 gap có căn cứ và bản Outline trước/sau. Không commit CV cá nhân vào Git.
- [ ] Cập nhật API docs, implementation status và báo cáo bằng chứng đúng những phần thực sự đã chạy.

## 6. Thứ tự và ước lượng

| Chặng | Phạm vi | Ước lượng sơ bộ cho một người |
|---|---|---|
| 1 | P0.1 snapshot + chọn CV/JD + migration | 0,5–1 ngày công |
| 2 | P0.2 ma trận gap + P0.3 AI Outline/validation | 1–1,5 ngày công |
| 3 | UI chỉnh Outline + P0.4 BI/lưu/xuất | 1–1,5 ngày công |
| 4 | QA, E2E, kiểm tra live và tài liệu P0 | 0,5–1 ngày công |
| 5 | P1 kịch bản/checklist và kiểm chứng bổ sung | 0,5–1 ngày công |

Tổng P0 khoảng **3–5 ngày công**; thêm P1 khoảng **0,5–1 ngày công**.
Đây là ước lượng ban đầu, không phải cam kết thời hạn; chưa gồm chờ người dùng chọn CV/JD,
review dữ liệu cá nhân, thời gian chờ provider hoặc quay/nộp video.

Điểm chốt P0: có ca tư vấn lưu bền, gap có bằng chứng, BI có nguồn/cỡ mẫu và Outline mới sửa được.
Điểm chốt bài tập: người học xác minh nội dung, quay video đúng 2–3 phút và nộp theo hạn giảng viên.
