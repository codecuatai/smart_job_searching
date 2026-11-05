# Tài liệu UniTalent AI

- [README gốc](../README.md): cài đặt và chạy.
- [Chạy dự án từ đầu](guides/getting-started.md): clone, Docker, E2E, cấu hình và xử lý lỗi.
- [Cấu trúc dự án](guides/project-layout.md): đánh giá tên cũ, tên mới và nội dung đã dọn.
- [Một file cấu hình](guides/configuration.md): root .env, cổng, local/Docker và dữ liệu.
- [Kiến trúc](guides/architecture.md) · [API](guides/api.md).
- [Yêu cầu, ERD và định nghĩa dữ liệu v4](guides/requirements-and-data.md).
- [Docker, Metabase, ETL và backup/restore](guides/bi-and-recovery.md).
- [Benchmark và hướng dẫn gold labels](../data/evaluation/README.md).
- [Crawl job công khai](guides/job-crawler.md).
- [Trạng thái triển khai](guides/implementation-status.md).
- [Kế hoạch hoàn thiện 5 checklist TH3](plans/th3-completion-roadmap.md): backlog, phụ thuộc, tiêu chí nghiệm thu và mốc bàn giao AI/BI.
- [Audit 05/11 và kế hoạch nghiệm thu/refactor UI](plans/th3-release-and-ui-refactor.md): lỗi matching tái hiện được, kết quả chạy lại, ưu tiên P0/P1 và thiết kế từng màn hình.
- [Triển khai và kiểm chứng 05/11](reports/release-implementation-2026-11-05.md): thay đổi CV-first/UI/CI, kết quả offline/live và điều kiện nghiệm thu còn thiếu.
- [Triển khai/sao lưu](guides/deployment.md) · [Git/media](guides/git-and-media.md).
- [Kiểm thử](guides/testing.md) · [E2E](guides/e2e.md) · [Kết quả kiểm tra](guides/verification.md).
- [Báo cáo model](reports/model-evaluation.md) · [Báo cáo BI](reports/bi-evaluation.md).
- [Lộ trình học và phỏng vấn Gemini](reports/gemini-coaching.md): cách tạo, lưu tiến độ và kiểm chứng provider AI.
- [Luồng luyện phỏng vấn và xử lý lỗi](guides/interview-flow.md): tạo câu hỏi, chấm câu trả lời, giữ draft và phân biệt offline/live.
- [Nguyên nhân và sửa lỗi Gemini quá tải](reports/gemini-reliability-2026-11-05.md): xác minh tên model/key, retry có giới hạn, model dự phòng thật và kiểm chứng trên app chính.

Tài liệu thành phần: [web](../apps/web/README.md), [API](../services/api/README.md), [AI](../services/ai/README.md), [công cụ nghiên cứu](../scripts/research/README.md).

Báo cáo DOCX gốc tại `research/`, sơ đồ chính thức dùng chung tại `diagrams/`. Báo cáo nghiên cứu có thể mô tả kiến trúc đích lớn hơn MVP; hướng dẫn kỹ thuật Markdown phản ánh code đang chạy. Các bản render QA cũ đã được dọn khỏi dự án; kết quả E2E mới nằm ở `artifacts/e2e/` tại root.
