# Đánh giá và tổ chức thư mục

## Đánh giá cấu trúc ban đầu

Tên `frontend`, `backend` và `ai` không sai: chúng diễn tả tầng công nghệ. Điểm chưa thuận tiện là các thành phần ứng dụng đứng lẫn với tools, video và nhiều bản render QA; dữ liệu SQLite đặt trong backend source; ba ảnh sơ đồ được giữ hai nơi; cấu hình có cả mẫu root và mẫu frontend.

Bản mới ưu tiên vai trò và vòng đời của file: source ứng dụng, tài liệu chính thức, dữ liệu riêng và kết quả tạo lại được nằm ở các vị trí khác nhau. Không thêm tầng repository/module không cần thiết.

## Các tên mới

| Trước | Sau | Lý do |
| --- | --- | --- |
| frontend/ | apps/web/ | Một ứng dụng web; có thể thêm app khác mà không trộn với dịch vụ |
| backend/ | services/api/ | Tên thể hiện đúng API nghiệp vụ |
| ai/ | services/ai/ | Dịch vụ AI độc lập cùng nhóm với API |
| tools/ | scripts/research/ | Công cụ tạo báo cáo/sơ đồ/phụ đề, tách khỏi lệnh vận hành ở scripts/ |
| docs/*.md (hướng dẫn) | docs/guides/*.md | Tên kebab-case, đường dẫn nhất quán |
| docs/*.docx | docs/research/*.docx | Giữ báo cáo học thuật gốc riêng |
| tools/assets/ | docs/diagrams/ | Dùng một bộ sơ đồ; đã đối chiếu SHA-256 trước khi bỏ bản sao |
| backend/data/ | var/data/ | Dữ liệu bền vững, private; không phải source |
| .scratch/e2e/ | artifacts/e2e/ | Kết quả test có tên rõ ràng, không đưa lên Git |
| .env.example + frontend/.env.example | `.env.example` ở root + `.env` local | Một template cấu hình không secret; key Gemini chỉ ở `.env` |

`media/` giữ nguyên tên và toàn bộ nội dung vì chứa video/phụ đề cá nhân. `.agents/` giữ lại vì là cấu hình công cụ phát triển đã có, không phải file runtime thừa. `.venv` và node_modules giữ để tiếp tục chạy được; chúng bị Git/Docker context bỏ qua.

## File đã dọn khỏi dự án

Đã bỏ hai file env mẫu và `.gitignore` riêng của web (chính sách Git nằm ở root). Các thư mục `.next`, `.next-dev`, cache TypeScript/pytest cũ, `.taste-skill`, `.scratch` cũ và các bản render QA được đưa ra ngoài workspace. Ba ảnh trùng trong tools/assets cũng được bỏ khỏi source, giữ bản chính tại docs/diagrams.

Để có thể khôi phục, bản dọn dẹp được lưu tại:

```text
C:\Users\admin\.codex\backups\unitalent-layout-cleanup-20261028-115119
```

Danh sách 15 đích được dọn nằm trong `artifacts/layout-cleanup.json`. Cache mới có thể xuất hiện lại sau dev/build/test; đó là kết quả tự sinh, không được commit. Lịch sử Git frontend cũ vẫn có backup riêng được ghi ở [verification.md](verification.md).

## Những đường dẫn đã cập nhật

Python package imports, vị trí seed, database mặc định, Node scripts, Next proxy/config, entrypoints, Dockerfiles/Compose, pytest, Playwright, CI, Git guard, các link Markdown và đường dẫn công cụ nghiên cứu. Đổi tên không thay route người dùng (`/student/*`, `/recruiter/*`, `/api/*`) hoặc cấu trúc dữ liệu SQLite.

Các báo cáo DOCX được chuyển vị trí, không sửa nội dung học thuật. Volume Docker đang có được tham chiếu lại qua DATA_VOLUME để giữ tài khoản/CV sau đổi tên service.
