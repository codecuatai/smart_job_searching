# Báo cáo đánh giá mô hình Matching Score

**Cập nhật TH3 04/11/2026:** báo cáo tái lập mới tại [benchmark/report.json](../../data/evaluation/benchmark/report.json), chạy `npm run ai:benchmark`. 576 mẫu synthetic, train/validation/test 512/32/32; không chia sẻ candidate/job IDs. Baseline test macro-F1 0,8756; candidate-v3 0,3077. Candidate validation macro-F1 0,4867 thấp hơn baseline 0,5867 nên runtime giữ hybrid-v2 theo selection manifest. P@5 0,4, Recall@5/NDCG@5 1,0 trên chỉ 4 relevant queries và 4-job pool; không đủ làm kết luận thực tế. Report có ablation, lỗi và latency. Gold human labels hiện 0; [labeling guide](../../data/evaluation/README.md). Nội dung fixture 10 mẫu bên dưới là lịch sử baseline train=evaluation, không phải held-out quality estimate.

## Phạm vi

UniTalent dùng model `hybrid-v2`: skill coverage, cosine similarity và một bộ trọng số logistic nhỏ được huấn luyện bằng gradient descent. `baseline-v1` vẫn là fallback nếu không đọc được model artifact. Điểm chỉ hỗ trợ sắp xếp/gợi ý, không tự động loại ứng viên.

Model artifact: `services/ai/models/matching-v2.json`.

## Tập đánh giá

Fixture tái lập nằm ở `data/evaluation/matching_pairs.jsonl`, gồm 10 cặp CV–JD mẫu:

- 4 mẫu không phù hợp (`label=0`).
- 3 mẫu phù hợp một phần (`label=1`).
- 3 mẫu phù hợp cao (`label=2`).

Đây là tập mẫu phục vụ kiểm thử kỹ thuật, chưa đại diện cho thị trường lao động và chưa đủ để công bố chất lượng production.

## Chạy đánh giá

```powershell
npm run ai:train
npm run ai:evaluate
```

Lệnh đánh giá hiện tại in model version, số mẫu, accuracy, macro precision/recall/F1 và MAE trên thang ordinal. Ngưỡng quy đổi mặc định:

```text
score < 35  → không phù hợp
35–74       → phù hợp một phần
score >= 75 → phù hợp cao
```

## Kết quả fixture hiện tại

```text
modelVersion: hybrid-v2
samples: 10
accuracy: 0.8000
macroPrecision: 0.8500
macroRecall: 0.7778
macroF1: 0.7487
MAE ordinal: 6.3000
```

Kết quả này chỉ chứng minh pipeline train/evaluate chạy được trên fixture nhỏ. Trước khi dùng để ra quyết định tuyển dụng cần thu thập cặp CV–JD có sự đồng ý, gán nhãn bởi nhiều người, tách train/validation/test, kiểm tra bias và báo cáo confidence interval.

## Hạn chế

- Từ điển kỹ năng hữu hạn; đã thêm phủ định cơ bản và OCR tối đa 3 trang. Ngữ cảnh phức tạp vẫn có thể sai.
- Dataset hiện nhỏ và do nhóm tạo, có nguy cơ bias và overfit.
- Có ranking benchmark synthetic, chưa có tập gold lớn/đa dạng hoặc confidence đủ tin cậy cho thực tế.
- Không dùng AST, giọng nói, số năm kinh nghiệm hay GitHub như bằng chứng năng lực.
