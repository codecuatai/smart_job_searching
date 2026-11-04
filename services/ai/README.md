# AI — Ghép việc có giải thích, chạy cục bộ

Python + FastAPI, không cần khóa API, GPU, tải model hoặc gửi CV tới nhà cung cấp bên ngoài. Đây là **baseline NLP và rule-based**, chưa phải mô hình đã huấn luyện hay LLM.

```powershell
# Tại gốc repository, sau npm run setup
.venv/Scripts/python.exe -m services.run ai --reload
```

Đọc duy nhất `.env` gốc qua `services/config.py`; cổng lấy từ AI_PORT. Swagger ở `/docs` trên cổng đó (mặc định 8001). Chỉ backend gọi AI trong luồng ứng dụng. Dịch vụ AI không có cơ chế đăng nhập riêng: giữ trong mạng nội bộ, không mở cổng ra Internet.

## Thuật toán

`app/engine.py` cung cấp `extract_skills`, `match`, `evaluate`.

1. Chuẩn hóa chữ thường, bỏ dấu Unicode tiếng Việt, đổi `đ` thành `d`.
2. Tìm alias với ranh giới từ: `k8s` → Kubernetes, `postgres` → PostgreSQL. JavaScript không bị nhận nhầm thành Java, Django không thành Go.
3. Kỹ năng yêu cầu được trích từ `tags` + `requirements`. Kỹ năng ứng viên lấy từ vị trí mong muốn, kỹ năng khai báo, mô tả dự án và văn bản CV gần nhất.
4. `coverage = số kỹ năng khớp / số kỹ năng yêu cầu nhận diện được`.
5. Tạo bag-of-words đếm token rồi tính cosine giữa văn bản hồ sơ và văn bản yêu cầu/mô tả việc.
6. `score = round(100 × (0.85 × coverage + 0.15 × cosine))`. Nếu JD không có kỹ năng nào trong từ điển, chỉ dùng cosine.
7. Trả điểm, `matchedSkills`, `missingSkills`, coverage, cosine, method và giải thích số kỹ năng khớp.

Không cộng điểm AST hoặc số năm kinh nghiệm giả. Điểm phản ánh từ khóa trong văn bản, dễ bị tác động bởi tự khai báo; không xác minh kỹ năng thực tế. Không hiểu phủ định (ví dụ “chưa biết Python”), không đánh giá mức độ thành thạo; từ điển hữu hạn nên không bao phủ mọi ngành.

## Endpoint

| Method | Path | Payload / kết quả |
| --- | --- | --- |
| GET | `/health` | Trạng thái engine |
| POST | `/skills` | `{ "text": "Python, SQL" }` → danh sách kỹ năng |
| POST | `/match` | `{ "profileText": "...", "jobs": [{ "id": "1", "tags": [], "requirements": [], "description": "..." }] }` → kết quả theo ID |
| GET | `/interview/questions` | Ba câu hỏi cố định, ID `api`, `database`, `project` |
| POST | `/interview/evaluate` | `{ "questionId": "api", "answer": "..." }` → score, feedback, concepts |

Rubric phỏng vấn: tối đa 30 điểm theo độ dài (đạt ngưỡng 100 từ), 70 điểm theo tỷ lệ khái niệm từ khóa. Kết quả chưa kiểm tra logic hay tính đúng đắn; thêm từ khóa có thể tăng điểm dù câu trả lời sai. Không sử dụng để tự động loại ứng viên. Lịch sử được backend lưu theo tài khoản, AI không giữ dữ liệu.

Lộ trình kỹ năng được backend sinh từ `missingSkills`: mỗi kỹ năng là một chặng ôn nền tảng → xây ví dụ có test → cập nhật hồ sơ. Mục tiêu bao phủ 100% không phải dự báo điểm tương lai. Không có đề xuất khóa học cá nhân hóa hoặc dữ liệu khóa học bên ngoài.

## Mở rộng

Có thể bổ sung taxonomy kỹ năng, negation detection, embeddings và bộ dữ liệu đánh giá đã gán nhãn. Giữ nguyên API để frontend không phụ thuộc model. Đánh giá ranking bằng tập hồ sơ–JD thực có sự đồng ý, tách train/test, báo cáo Recall@K/NDCG trước khi dùng quyết định tuyển dụng. Các mô hình S-BERT/GNN, voice và AST trong báo cáo hiện thuộc lộ trình nghiên cứu.

Tham khảo thư viện trích xuất CV: [pypdf](https://github.com/py-pdf/pypdf). PDF scan cần OCR riêng; pypdf không nhận diện chữ từ ảnh.
