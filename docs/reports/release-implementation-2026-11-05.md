# Triển khai CV-first, UI và kiểm chứng TH3 — 05/11/2026

Triển khai từ baseline `99323c3`, theo [kế hoạch/audit](../plans/th3-release-and-ui-refactor.md). Đây là kết quả kiểm chứng tại máy dev, không phải xác nhận production hoặc cam kết điểm đồ án.

## Đã thay đổi

- Matching `cv-evidence-v4`: CV là bằng chứng chính; chỉ profile tối đa 20% coverage, CV đầy đủ đạt 100% coverage. Giới hạn điểm theo độ phủ, chất lượng/số yêu cầu nhận diện, must-have và số năm kinh nghiệm khi JD cung cấp. Giữ raw CV/context sau xác nhận; kỹ năng bị xóa khỏi analysis không tự được thêm lại từ PDF. List/detail/application snapshot dùng chung input/scorer.
- API trả raw/final score, adjustments có delta, scorerVersion, trạng thái thiếu CV, kỹ năng theo nguồn và yêu cầu chưa nhận diện. Chất lượng yêu cầu tính theo từng item, không bị alias expansion tăng giả. UI jobs dùng `/100`, không thể hiện điểm như xác suất tuyển.
- Phân tích CV nhận kết quả API trực tiếp để cập nhật UI, trạng thái xử lý rõ, lỗi có request ID, khóa chỉnh/upload khi đang xác nhận. CV lên đầu profile, evidence dạng chip mở rộng, PDF preview bên cạnh tùy chọn, kích thước KB cho file nhỏ. Thông tin bổ sung vẫn truy cập bằng anchor; chưa chuyển thành tab ẩn nội dung.
- Jobs bỏ hero lớn; tìm kiếm debounce 300ms; thêm địa điểm/hình thức/điểm tối thiểu, giữ filter và trang trong URL. Chuẩn hóa ngày, địa điểm/lương thiếu dữ liệu, thêm nguồn gốc và diễn giải score; bỏ khối AST/SOLID/plagiarism tĩnh trên job detail.
- Navigation mobile giữ focus, Esc/khôi phục focus, khóa nền; sửa lỗi logout do focus trong lúc drawer đang dịch chuyển. Chiều cao drawer theo dynamic viewport, logout 44px. Recruiter mobile có nút mở bộ lọc; bỏ score AST/voice khỏi kết quả chính. Post-job AST thành nội dung tham khảo thu gọn.
- BI mặc định 8 kỹ năng, mở tất cả khi cần, đưa lương/funnel lên trước; cảnh báo mẫu nhỏ và tỷ lệ salary đọc được; advanced filters/cohort thu gọn. Coaching/interview có tìm kiếm trong job selector thay vì chọn từ 640 options.
- Token/spacing/type trong `workspace.css`, shared PageHeader/ScoreSummary/JobSelector; giữ nhận diện xanh, landing và avatar hiện có. Sửa contrast một số nhãn, hàng việc làm và filter mobile.
- Lỗi Gemini phân loại configuration/quota/timeout/invalid output/unavailable; log code/requestId an toàn, retry hữu hạn. Proxy 90s/API tối thiểu 70s/provider mặc định 60s. Không retry lồng ở API.
- Offline Docker E2E luôn chạy trong CI, không cần key. Chỉ tác vụ sinh nội dung dùng provider `test-fixture:offline-v1` khi `APP_ENV=test`; auth/SQLite/matching/OCR/PostgreSQL/Metabase chạy thật. Live Gemini riêng khi có key. Fixture ngoài test làm service từ chối startup. Giữ báo cáo offline riêng khi CI chạy tiếp live.
- Test reset đúng volume project `unitalent-test`, timeout cài npm 300s, cleanup container/network trong finally. Main volume giữ nguyên. Thêm `npm run db:verify-recovery` kiểm tra SQLite và mart restore trên bản sao.
- Benchmark truyền CV riêng, thêm input ablation CV/profile/combined; legacy train/evaluate map fixture text thành CV. Không deploy candidate v3 do validation kém hơn baseline.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Python API/AI/unit/regression | 58 passed; gồm thiếu CV, thêm CV, kinh nghiệm, loại bỏ skill, adjustment reconciliation, alias quality, fixture guard và lỗi provider |
| ESLint, TypeScript, production Docker build | Passed |
| Docker offline E2E desktop/mobile | 28/28 passed, lần cuối 49,8s; login/register/role/session/logout, biến thể PDF, CV xác nhận/OCR, tuyển dụng hai user/CV snapshot/lịch, coaching/interview, BI SQL |
| BI verify | Passed: parity, idempotency, aggregate-only role, không raw PII columns; facts job 640, candidate skill 97, stage 8 |
| Restore bản sao | Passed: SQLite integrity/count users 218, jobs 640, applications 5, resumes 178; PostgreSQL mart counts 640/97/8 khớp; file/database tạm được dọn |
| UI snapshots | 10 routes × 4 widths (1440/768/390/375), không JS pageerror; phát hiện tràn jobs mobile ở lượt đầu, đã sửa và chạy lại không còn tràn ở 40 snapshot |
| Filter URL/Escape | Manual Playwright: minScore giữ sau reload; menu đóng Esc và trả focus về nút mở |
| Search 640 jobs | 12 request tuần tự localhost/Docker Desktop Windows; p50 80ms, p95 theo nearest-rank 1657ms (cold/cache miss); 11 warm 72–111ms; chưa phải load/concurrency benchmark |
| Matching synthetic | 576 mẫu, baseline test macro-F1 0,8756; candidate 0,3077 bị từ chối. Gold labels = 0; không suy ra model chính xác thực tế |
| Live Gemini HTTP | `/resume/analyze` 200, method `gemini:gemini-3.5-flash-lite`, ~5s; `/roadmap` và `/interview/questions` 503 provider-unavailable sau retry, ~3–3,5s. Không đổi expected status để coi pass |

Artifact local: `artifacts/e2e/results.json`, `artifacts/e2e/report`, `artifacts/release-2026-11-05/ui-audit.json` và ảnh cùng thư mục. Không commit ảnh có dữ liệu CV. Landing inspector có các nhận xét art direction theo app mode (shadow/title/icon) không phù hợp để kết luận lỗi landing; không dùng exit code đó để tuyên bố UI pass toàn bộ. Source lint của ba phần refactor chính không có findings. Chưa audit đầy đủ keyboard/contrast/zoom 200% trên mọi tương tác.

## Cách chạy

```powershell
npm run env:init
# Điền GEMINI_API_KEY trong .env
npm run docker:up
# Mặc định offline, không gọi Gemini
npm run docker:test
npm run bi:verify
npm run db:verify-recovery
```

Live Gemini: `$env:E2E_AI_MODE='live'`, `npm run docker:test`, sau đó `Remove-Item Env:E2E_AI_MODE`. Linux/macOS dùng `E2E_AI_MODE=live npm run docker:test`. Web chính ở http://127.0.0.1:3000, Metabase :3001. E2E sử dụng volume mới mỗi lần; đã kiểm chứng seed/migration/bootstrap trên volume test trống, chưa diễn tập clone trên một máy vật lý khác.

## Nghiệm thu còn lại

1. **Gold labels và đánh giá thực tế:** nhóm cần thu thập 200–300 cặp CV/JD hợp lệ, hai người chấm độc lập, adjudication và provenance. Công cụ/template đã có trong `data/evaluation`; không thể thay bằng gán nhãn AI rồi ghi human-reviewed. Báo calibration/false positives theo role/seniority và đánh giá trước khi chỉnh ngưỡng tiếp.
2. **Live provider:** roadmap/interview cần đạt live E2E thành công ổn định với key/quota/model đã chọn. Code xử lý lỗi đã có; chưa có bằng chứng dịch vụ Gemini luôn khả dụng. Offline E2E không thay thế bằng chứng này.
3. **Dữ liệu BI:** dataset real có 635 jobs ITviec, 1 candidate và ~4% salary đủ parser. Cần thêm mẫu ứng viên/lương hợp lệ và thời gian quan sát trước khi gọi là xu hướng thị trường. Chưa có TopCV từ lần crawl bị 403; không gán nguồn giả.
4. **Backlog UI/kiến trúc:** chưa tách hết globals thành CSS module, chưa refactor toàn bộ candidate detail/application timeline; chưa thêm salary/level filters theo dữ liệu chuẩn hóa, freshness/expiry đầy đủ hoặc chuẩn hóa JD bằng Gemini lúc import. Đây là các mục cải thiện tiếp, không được đánh dấu đã làm.
5. **Vận hành:** thêm diễn tập phục hồi host mới gồm Metabase metadata, concurrency/load, accessibility đầy đủ/zoom 200% và release CI trên GitHub. Kết quả local không xác nhận workflow remote đã chạy xanh.

Với 5 checklist TH3, các luồng chức năng và tài liệu nền tảng đã có; mục AI và đánh giá vẫn cần dữ liệu độc lập/live evidence để nghiệm thu vững chắc. Chưa tuyên bố hoàn tất 100% toàn bộ kế hoạch hoặc chắc chắn đạt 10 điểm.
