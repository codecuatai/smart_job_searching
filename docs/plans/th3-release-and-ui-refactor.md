# Kế hoạch nghiệm thu TH3 và refactor giao diện

Ngày kiểm tra: 05/11/2026. Baseline: commit `99323c3`.
Phạm vi: đánh giá, chạy lại Docker, kiểm thử và lập kế hoạch. Chưa triển khai refactor trong đợt đánh giá này.

**Cập nhật triển khai tiếp theo 05/11:** đã sửa M01–M06, T01/T02 (xử lý/kiểm thử lỗi; availability live vẫn chưa ổn định), O01 và refactor các luồng UI chính. Báo cáo nghiệm thu, thay đổi thực tế và backlog còn lại tại [release-implementation-2026-11-05.md](../reports/release-implementation-2026-11-05.md). Các phần dưới là kế hoạch gốc, không phải tuyên bố đã hoàn tất mọi mục.

## 1. Định nghĩa hoàn thành

Không dùng “đã có màn hình” hoặc CI xanh làm tiêu chí đủ. Mỗi checklist cần chức năng chạy được, dữ liệu giải thích được, kiểm thử tái lập và báo cáo đúng phiên bản bàn giao. Không có cam kết 10 điểm hoặc độ chính xác tuyệt đối.

| Checklist | Điều kiện đóng |
|---|---|
| Yêu cầu/CSDL | FR/NFR → màn hình/API → bảng → test; ERD/data dictionary đúng schema; migration và restore kiểm chứng trên bản sao |
| CV/Matching | Tín hiệu CV/hồ sơ tách riêng, xử lý thiếu dữ liệu nhất quán; giải thích đúng điểm cuối; benchmark có CV/JD và tập kiểm định độc lập |
| BI | Kỹ năng, lương theo thời gian, funnel chạy được; số khớp SQL; dataset/cohort/currency/sample size/freshness rõ |
| Frontend/API | Luồng candidate/recruiter chạy trọn vẹn; đọc được trên mobile; có loading/empty/error/success và kiểm tra quyền |
| Test/Báo cáo | Bộ test hồi quy xanh; live AI test ghi kết quả thật; lỗi nghiêm trọng đóng; benchmark, screenshot và hướng dẫn clone chạy cùng release |

Gold labels do người đánh giá và CV/JD được phép sử dụng là phần nhóm cần tham gia. Không tạo nhãn synthetic rồi gọi đó là nhãn người thật.

## 2. Kết quả kiểm tra trực tiếp

- Đã khởi động Docker Desktop, chạy `npm run docker:up`; 6 services healthy. Web cổng 3000, Metabase cổng 3001.
- `python -m pytest -q`: 48 passed; frontend typecheck/lint passed.
- Playwright host Edge chạy trên server Docker: 18/18 E2E desktop/mobile cho auth/session/role guard, PDF validation/persistence và search/filter. Đây là tập con, không phải full suite.
- `npm run bi:verify`: passed; parity SQL, ETL idempotent, role aggregate read-only và dashboard provisioning passed. Snapshot có 640 jobs trong mart, gồm các dataset; real jobs = 635 theo web.
- Chụp 20 trạng thái trang: 10 route ở 1440 và 390px. Không thấy page overflow hoặc JavaScript pageerror trong lần chụp. Đây là kiểm tra trạng thái trang, chưa bao phủ mọi tương tác.
- Landing inspector bổ sung 1440/768/390: một số nhãn chỉ đạt 3.7–3.8:1 contrast; tablet lệch margin 30/47px. Cảnh báo motion/ảnh của skill mang tính art direction, không phải bug chức năng và không cần thêm video để đủ TH3.
- Artifact local: `artifacts/audit-2026-11-05/ui-audit.json`, screenshots cùng thư mục; `landing-inspector/report.json`; `artifacts/ui-source-audit.txt`. Không commit ảnh chứa dữ liệu CV.
- E2E desktop bổ sung: 3/5 passed (interview, scan OCR/Gemini và Metabase); 2 failed (roadmap generation và CV text analysis, HTTP 503). Log AI ghi upstream `HTTPStatusError status=503`, có cả hai lần retry thất bại. Không phải mọi lỗi đều do timeout; tăng timeout chưa đủ xử lý availability của provider.
- Tổng hai lượt E2E: 21 pass / 23 ca đã chạy; chưa chạy lại 5 ca mobile live-AI/BI còn lại. Tài khoản fixture mới do E2E tạo được phân loại test; job tuyển dụng tạm có cleanup trong finally. Dữ liệu hồ sơ cá nhân không dùng để ghi kết quả live extraction.

## 3. Lỗi và khoảng trống cần ưu tiên

| ID | Mức | Bằng chứng hiện tại | Việc cần làm |
|---|---|---|---|
| M01 | P0 | Với JD Python/SQL/Docker/FastAPI/Git: profile-only=92, thêm CV cùng kỹ năng=84 | Sửa quy tắc thiếu CV; thêm CV có bằng chứng không làm giảm điểm chỉ vì đổi nguồn |
| M02 | P0 | JD yêu cầu 5 năm: CV 1 năm và 8 năm cùng 84; experienceFit có weight 0 | Chốt experience có ảnh hưởng hay chỉ thông tin; nếu ảnh hưởng phải có feature/gate được đánh giá, không đoán số năm từ chức danh |
| M03 | P0 | Xác nhận CV thay văn bản matching bằng danh sách skill và experience | Giữ context dự án/kinh nghiệm; danh sách chỉnh sửa điều khiển skill có quyền loại bỏ kỹ năng sai; giữ raw text riêng và evidence nguồn |
| M04 | P0 | `scoreFactors` giải thích logistic trước các cap/quality/must-have penalty; modelVersion vẫn hybrid-v2 | Trả rawScore/finalScore, adjustmentReasons và scorerVersion; tổng đóng góp giải thích được điểm cuối |
| M05 | P1 | Benchmark gọi `match(profileText, job)` mà không truyền resumeText | Đánh giá đúng pipeline CV-first, có ablation CV-only/profile-only/combine và nhóm sparse/unseen skills |
| M06 | P1 | `requirement_quality` lấy số canonical skills chia số raw strings | Đánh giá coverage theo từng yêu cầu; tránh alias làm tăng độ đầy đủ giả; giữ unknown requirements |
| T01 | P0 | CI thiếu key sẽ skip cả Docker E2E | Tách offline E2E bắt buộc với fixture provider và live Gemini integration riêng; ghi skipped rõ; không dùng mock làm bằng chứng live |
| T02 | P0 | Live AI đã có 500/503; tăng timeout chưa chứng minh ổn định | Ghi request ID/error category an toàn; đối chiếu timeout browser/proxy/API/provider; test quota/timeout/invalid JSON/missing key và retry có hạn |
| O01 | P1 | Script test reset volume test và để stack chạy sau test; lần trước npm ci treo | finally cleanup container/network, giữ artifact khi fail; timeout cài dependency, cache hoặc image runner có dependency sẵn |
| U01 | P1 | Job đầu nằm ở y≈639 desktop, y≈906 mobile viewport 900 | Thu gọn banner; đưa search/filter/list vào first fold |
| U02 | P1 | Ảnh jobs có nhiều metadata/CTA nhỏ; phép đếm DOM thấy 187 phần tử <12px desktop | Chuẩn hóa body 14–16px, meta 12–13px; kiểm tra vùng bấm mobile ≥44px và contrast |
| U03 | P1 | Hồ sơ: CV/analysis dưới form dài, 19 skill thành 19 hàng full-width; nút xác nhận cuối trang | CV workspace riêng/đưa CV lên đầu, nhóm chip skill và evidence panel, lưu/xác nhận gần nội dung chỉnh |
| U04 | P1 | BI có skill list dài kéo giãn cột ngành, salary/funnel ở sâu dưới fold | Top skills mặc định 8–10, xem tất cả; dùng grid cân đối, salary/funnel xuất hiện ở phần trên |
| D01 | P1 | BI real có 1 candidate, chỉ 4% job có lương đủ parser | Hiển thị cỡ mẫu và thiếu dữ liệu; thu thập thêm dữ liệu hợp lệ; không hứa xu hướng thị trường từ mẫu này |
| D02 | P1 | UI còn `You'll love it`, `Not Available`, salary thiếu đơn vị và ISO date raw | Chuẩn hóa nhãn thiếu dữ liệu, currency/period, ngày locale; có nguồn và hạn tuyển |

P0 = trước nghiệm thu; P1 = trước chốt giao diện/báo cáo; P2 = sau bản nộp nếu chưa cần.

## 4. Thứ tự triển khai

### Đợt A — Đóng lỗi logic, hợp đồng API và CI (ước lượng 2–3 ngày công)

1. Viết regression cho M01–M04 bằng CV/JD cố định: thiếu CV, CV rỗng/scan, profile mâu thuẫn, sửa skill, seniority/experience, job ít dữ liệu, từ khóa phủ định.
2. Chốt công thức theo nguồn. Đề xuất bắt đầu thử nghiệm: 80% CV + 20% bổ sung hồ sơ, CV thiếu thì trạng thái “chưa đủ dữ liệu”/điểm sơ bộ; không tái chuẩn hóa thành 100% profile. Chọn công thức cuối bằng validation và kiểm thử monotonicity.
3. Dùng structured CV: skills/evidence, projects, experience; raw CV lưu riêng, phần người dùng loại bỏ không bị raw text thêm lại.
4. JD phải có must-have/nice-to-have, experience khi nguồn cung cấp, unknowns. Không tự coi vài tag là toàn bộ JD. Có thể dùng Gemini để chuẩn hóa JD một lần khi import, lưu cache/version và nguồn.
5. Phiên bản hóa scorer/calibration. API job list/detail/application snapshot phải dùng cùng scorer.
6. Tách CI: unit/type/lint/build; offline browser E2E luôn chạy; live Gemini khi có secret; lưu log và artifact, không xuất key/CV vào log.

Nghiệm thu: M01–M04 có test tái hiện trước và pass sau; điểm giải thích được; offline E2E không cần key; lỗi AI hiển thị đúng nguyên nhân và giữ dữ liệu đã lưu.

### Đợt B — Refactor UI (ước lượng 4–6 ngày công)

Giữ Next.js/React/Tailwind, routes/API và nhận diện xanh hiện tại. Thay đổi theo component, không rewrite toàn bộ stack. Hướng visual: workspace tuyển dụng sáng, rõ, mật độ vừa; trắng/xám trung tính, xanh rừng cho hành động/kỹ năng chính, amber cho thiếu dữ liệu. Lucide thống nhất; giữ avatar người/công ty có fallback ổn định.

Tokens: body 14–16, label 14, meta 12–13, page title 24–28; khoảng cách 4/8/12/16/24/32; border radius control 6–8/panel 10–12; content tối đa khoảng 1200; sidebar 224–240; mobile gutter 16. Đây là đề xuất, kiểm chứng bằng screenshot trước khi đóng.

| Thứ tự | Màn hình | Bố cục và tương tác đề xuất | Nghiệm thu |
|---|---|---|---|
| B1 | Shell và shared UI | PageHeader, Button, Field, Select, Panel, Badge, EmptyState, ErrorState, Skeleton, Avatar, ScoreSummary | Cùng thang font/spacing; keyboard focus; mobile drawer giữ focus/đóng Esc |
| B2 | Profile/CV | Tabs Hồ sơ / CV & phân tích; desktop PDF trái–evidence phải; mobile chuyển tab; tóm tắt trạng thái Tải lên→Phân tích→Kiểm tra→Xác nhận | Không cuộn qua form mới tìm CV; trạng thái AI/confirmed rõ; bản sửa được giữ khi lỗi |
| B3 | Job list/detail | Search đầu trang; bỏ hero banner lớn, thay bằng CV status strip; filter địa điểm/level/lương/hình thức; list/detail có nguồn và freshness | Row đầu y≤500 ở mobile cao 844; score có lý do/evidence confidence; lương có đơn vị; filter giữ URL |
| B4 | Recruiter | Candidate list mật độ vừa, filter sheet mobile; detail chia CV / skill gaps / timeline; post-job review gọn | Một action chính; ẩn AST chưa triển khai khỏi form chính; không tạo cảm giác đã đánh giá AST |
| B5 | BI | KPI strip ngắn; top skills + salary trend + funnel; filter nâng cao đóng/mở; bảng ở tab Chi tiết | Mẫu số, sample size, cohort, nguồn, kỳ lương và updatedAt rõ; chart không kéo giãn cột rỗng |
| B6 | Coaching/interview | Select job có search; roadmap theo tuần + checklist; interview question/answer/feedback/history rõ | Không dropdown 640 option khó tìm; lưu trạng thái; feedback loading/retry rõ |
| B7 | Landing/login/register | Giữ hero/công ty theo yêu cầu trước đây; tăng contrast, giảm lặp demo score; CTA theo vai trò; mobile compact | 375/390/768/1440 không tràn; demo ghi rõ; không thêm chuyển động/video không cần thiết |

Component CSS: chia globals.css thành tokens/base/shell và module theo feature; bỏ màu và kích thước inline trùng; tách file JSX một dòng dài thành component đọc được. Giữ selector test theo role/label; thêm data-testid khi cần cho dữ liệu động.

### Đợt C — Dữ liệu và đánh giá AI (ước lượng 3–5 ngày công + thời gian nhóm gán nhãn)

1. Dùng JD đầy đủ hợp lệ, nguồn URL/ngày/validThrough rõ; kiểm tra duplicates, taxonomy aliases và lỗi ngành.
2. Mục tiêu 200–300 cặp CV/JD đa dạng, tối thiểu hai người đánh giá, không xem score model. Đây là mục tiêu thu thập, không phải dữ liệu đã có.
3. Chia theo người/job/company/template trước khi train; báo agreement, adjudication và provenance. Dùng pseudonym và không commit CV gốc.
4. So sánh taxonomy baseline, CV-first và semantic embedding nếu có; không thêm mô hình chỉ vì phức tạp hơn. TF-IDF/embedding/LLM phải ghi version.
5. Báo Precision@5, Recall@5, NDCG@5, macro-F1, phân bố score, false positive/negative và latency. Thang điểm 0–100 là ranking score; hiển thị rõ, không coi là xác suất tuyển.
6. Đặt mục tiêu nghiệm thu trước đánh giá; không tối ưu theo test. Kiểm tra riêng: junior gặp senior JD, nhiều skill chung nhưng sai role, unknown skills, scan và missing CV.

### Đợt D — Nghiệm thu cuối và bàn giao (ước lượng 1–2 ngày công)

- Clone vào thư mục/máy sạch, điền key, chạy 1–2 script; migration/seed idempotent, không ghi đè .env.
- Chạy full desktop/mobile E2E sau UI refactor; offline và live AI tách báo cáo. Không bỏ lỗi bằng đổi expected status thành 503.
- SQL parity cả filters/cohort, refresh sau thêm/sửa dữ liệu; thử backup/recovery trên volume bản sao.
- Audit keyboard/focus/contrast, 375/390/768/1440 và reduced motion; so sánh screenshot trước/sau; thêm 200% zoom.
- Kiểm thử tải search/job scoring 600+ jobs trên cấu hình ghi rõ; debounce 250–350ms và không re-score toàn bộ database mỗi phím; đo p50/p95 trước/sau.
- Cập nhật ERD, API, model/report/known issues, bảng checklist và kịch bản demo 5–7 phút.

Ước lượng tổng 10–16 ngày công cho một người, chưa tính thời gian chờ dữ liệu/gán nhãn; điều chỉnh sau đợt A. Đây là lịch đề xuất, chưa phải cam kết ngày giao.

## 5. Ma trận kiểm thử bổ sung

| Nhóm | Ca nghiệm thu chính |
|---|---|
| CV | PDF text/scan/password/hỏng/quá giới hạn; mất mạng; đổi CV đang phân tích; xác nhận rỗng/chỉnh skill; reload; đúng account |
| Matching | CV/profile đồng nhất và mâu thuẫn; missing CV; không tự nâng 100% profile; thay CV không giảm vô lý; job ít tag/JD dài; skills unknown; must-have; experience |
| Tuyển dụng | 2 account độc lập, duplicate apply, CV immutable, recruiter outsider, stage/schedule, refresh và lỗi AI không chặn luồng gửi CV |
| BI | real/demo/test, filter/date/cohort/currency, unique candidate, nguồn cung ít, thiếu salary, ETL parity/idempotent và scope |
| AI | live success, provider timeout/429/5xx/invalid JSON, key missing; không ghi log secrets; retry hữu hạn, giữ draft |
| UI | mobile navigation/modal keyboard, form labels/errors, loading/empty/error/success, long titles/tags/file names, unit/date formats, visual regression |
| CI/ops | fresh clone, no-key offline E2E, live-key integration, runner install bounded, finally cleanup, persistent main data |

## 6. Thứ tự chốt

A (logic + tests) → B1/B2/B3 (shell + CV + jobs) → B4/B5/B6/B7 → C (benchmark/data, có thể chuẩn bị từ đầu) → D (full acceptance). Không coi số job trên 80% ít đi là bằng chứng model đã chính xác.
