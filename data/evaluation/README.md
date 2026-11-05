# Đánh giá matching và gán nhãn

`npm run ai:benchmark` tạo 576 cặp synthetic, split theo family thành 512 train/32 validation/32 test, không chia sẻ candidate/job ID giữa các tập. TF-IDF fit train; model logistic học features trên train; chỉ chọn bằng validation (macro-F1 và NDCG không giảm). Test chỉ báo cáo. `matching-selection.json` xác định artifact runtime. Chưa có human gold labels.

Artifacts trong `benchmark/`: từng split JSONL, report.json (metrics/errors/ablation/latency/hash), human-label-template.csv. Các mẫu synthetic có `annotationSource=synthetic-family-rule`, `gold=false`. Precision@5 chia 5 dù held-out pool chỉ có 4 job; chỉ 4 relevant queries, ranking dễ bão hòa. NDCG=1 ở tập nhỏ này không chứng minh tuyển dụng chính xác. Baseline v2 cũng được train từ fixture synthetic nhỏ; mô hình mới bị từ chối khi validation kém hơn.

## Quy trình gold độc lập của nhóm

1. Lấy CV/JD đã được phép dùng, xóa tên/email/điện thoại, giữ kỹ năng/experience/evidence. Không commit CV cá nhân. Tạo IDs giả danh.
2. Chia theo ứng viên, job, công ty và template trước khi xem kết quả model; giữ cùng người/template trong một split. Công cụ tự kiểm tra ID; kiểm tra gần trùng công ty/template cần người đối chiếu.
3. Hai người đọc độc lập, chưa nhìn matching score. Relevance 0 = không liên quan/thiếu các yêu cầu cốt lõi; 1 = liên quan một phần/còn thiếu bắt buộc; 2 = có bằng chứng đáp ứng phần lớn yêu cầu cốt lõi. Ghi câu trích CV/JD và điều thiếu, không suy đoán từ trường học/tên/giới tính. Chưa biết không mặc định là có.
4. Điền reviewer_1 và reviewer_2 trong CSV. Bất đồng phải có adjudicated_label và lý do/evidence do người thứ ba hoặc nhóm thảo luận. Ghi rubric version và thời điểm; báo số bất đồng/tỷ lệ đồng thuận trong báo cáo.
5. Tạo JSONL cùng schema split files với `gold=true, annotationSource=human-reviewed` sau khi thực sự review. Chạy `python scripts/benchmark_matching.py --gold <reviewed.jsonl>`; báo cáo vào `gold-benchmark`, không overwrite báo cáo synthetic. Không gán nhãn Gemini thành human-reviewed.

Mỗi row có `id`, `candidateId`, `profileText` (thông tin bổ sung), `resumeText` (CV chính), `job` (id/title/tags/requirements/description), `label` (0/1/2), `split` (train/validation/test), `annotationSource`, `gold`. Dữ liệu mới phải tách CV/hồ sơ để benchmark đúng CV-first; train/evaluate legacy 10 mẫu coi `profileText` cũ là CV khi chưa có `resumeText`. Input ablation trong report kiểm tra CV-only/profile-only/combined. Đặt vài trăm cặp là mục tiêu thu thập; số gold hiện tại là 0. Tách kết quả synthetic và gold trong báo cáo đồ án; không dùng E2E pass làm model accuracy.

False-positive/negative hiện được ghi trong report: những hồ sơ chỉ khớp một kỹ năng có thể nhận điểm thấp dù nhãn relevance=1; candidate v3 chưa học tốt các nhóm ngôn ngữ không có trong train. Đây là lý do giữ baseline và cần corpus đa dạng/người gán nhãn trước khi tuyên bố chất lượng thực tế.
