# Công cụ nghiên cứu — scripts/research

Các script Python hỗ trợ báo cáo học phần, sơ đồ và phụ đề. Đây là công cụ chạy thủ công, tách khỏi runtime web/API/AI; `npm run setup` không cài các dependency nghiên cứu tùy chọn.

Chạy từ root dự án. Mọi báo cáo DOCX đặt ở `docs/research/`, sơ đồ dùng chung ở `docs/diagrams/`. Không còn bản sao `tools/assets/`.

| Script | Mục đích | Dependency riêng |
| --- | --- | --- |
| generate_diagrams.py | Star schema, AI matching flow, skill graph | matplotlib |
| generate_dfd_diagrams.py | DFD và ETL pipeline | matplotlib |
| generate_docx.py | Báo cáo nghiên cứu | python-docx |
| generate_proposal_docx.py | Bản đề xuất kỹ thuật | python-docx |
| expand_proposal.py | Mở rộng bản đề xuất, tạo bản chi tiết | python-docx, matplotlib |
| build_consolidated_proposal.py | Tổng hợp đề xuất từ các nguồn có sẵn | python-docx |
| build_full_consolidated_proposal.py | Tổng hợp đầy đủ từ bản chi tiết | python-docx |
| deepen_part2_research.py | Cập nhật nội dung nghiên cứu phần 2 | python-docx |
| transcribe_video.py | Nhận diện tiếng Việt từ audio | faster-whisper, soundfile |
| format_srt.py | Chuẩn hóa/ngắt dòng phụ đề | Python standard library |

Ví dụ:

```powershell
python scripts/research/generate_diagrams.py
python scripts/research/generate_dfd_diagrams.py
python scripts/research/generate_docx.py
```

Các script biên tập tổng hợp đọc bản nháp trung gian như `De_Xuat_He_Thong_Tim_Viec_Thong_Minh_Chi_Tiet.docx`; cần tạo đầu vào theo chuỗi tương ứng trước khi chạy. Chúng có thể ghi đè báo cáo cùng tên, nên chỉ chạy khi muốn tái tạo/chỉnh tài liệu; không được gọi từ setup/test ứng dụng.

Script phụ đề giữ tham số đầu vào của quy trình cũ (`audio_16k.wav`, `subtitles.srt` từ working directory). Chuẩn bị file đúng tên hoặc chỉnh tham số trước khi chạy. Video/phụ đề cá nhân lưu trong `media/`, bị Git bỏ qua. Các script này không tự chạy lại hoặc chỉnh media khi khởi động ứng dụng.

Báo cáo hiện có được giữ nguyên nội dung trong `docs/research`; các sơ đồ trong docs có cả thiết kế nghiên cứu tương lai. Tình trạng MVP thực tế ở [implementation-status.md](../../docs/guides/implementation-status.md).
