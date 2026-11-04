# Một repository cho toàn bộ dự án, không đưa media cá nhân lên Git

## Trạng thái tổ chức

Không có `.git` riêng trong `apps/web`. Metadata Git frontend cũ được chuyển ra backup ngoài dự án để có thể phục hồi. Toàn bộ source nằm trong cùng root; bạn chạy `git init` tại root khi muốn bắt đầu. Vị trí backup được ghi ở [verification.md](verification.md).

Không đưa bản backup `.git` vào repository. Nếu có lịch sử cũ chứa media, bắt đầu repository gốc mới sẽ không mang lịch sử đó theo.

## Ba lớp bảo vệ

1. **`.gitignore`**: bỏ qua toàn bộ `media/`, `uploads/`, `recordings/`, `videos/`, `audio/`; đuôi video/âm thanh/phụ đề phổ biến ở mọi nơi; ảnh cá nhân; database, CV lưu trong DB, environment, cache, thư mục render báo cáo, archive và agent tooling.
2. **Git hooks**: pre-commit quét file staged; pre-push quét file đang tracked. Chặn thư mục media, đuôi media phổ biến, ảnh ngoài danh sách cho phép, `.env` thật, key/database và file >20 MB.
3. **CI**: khi chạy GitHub Actions, bước `check-staged.mjs --all` kiểm tra file được theo dõi trước test/build.

Ảnh code/tài liệu được cho phép: `apps/web/public/` và `docs/diagrams/`. Chỉ đưa asset đã chọn vào hai thư mục này. `var/`, `artifacts/` và mọi `.env*` đều bị hook chặn khi cố tình stage. Không lưu ảnh riêng tư dưới các đường dẫn cho phép.

`.gitignore` mặc định phân biệt hoa/thường tùy môi trường; hooks dùng kiểm tra không phân biệt hoa/thường cho media. File video `.ts` trùng đuôi TypeScript nên không bị chặn toàn cục; đặt mọi transport-stream video trong `media/`. Các định dạng lạ hoặc file đổi tên giả vẫn cần xem `git status` trước khi commit.

## Khởi tạo

```powershell
git init
git branch -M main
npm run git:hooks
git config --get core.hooksPath
git add .
npm run git:check
node scripts/check-staged.mjs --all
git status --short
git commit -m "Initialize UniTalent full-stack project"
```

Hook path phải là `.githooks`. Git clone không tự bật hook trên máy mới; chạy `npm run setup` sau clone hoặc `npm run git:hooks`. Trên Linux/macOS, nếu hook không chạy, dùng `chmod +x .githooks/pre-commit .githooks/pre-push`.

## Kiểm tra một file

```powershell
git check-ignore -v media/TranVanTai-0548_subtitled.mp4
git check-ignore -v .env
git check-ignore -v var/data/unitalent.db
git check-ignore -v apps/web/public/landing/cv-review-editorial.png
```

Ba dòng đầu phải trỏ tới quy tắc ignore. Ảnh asset cuối thuộc ngoại lệ được commit; `check-ignore` có thể in quy tắc phủ định `!`, cần xem kết quả `git status`/`git check-ignore -q` khi xác định ignored.

## Nếu đã lỡ stage media

Repository đã có commit:

```powershell
git restore --staged -- media/
```

Repository chưa có commit đầu, hoặc file đã tracked:

```powershell
git rm -r --cached -- media/
```

`--cached` chỉ gỡ khỏi index, vẫn giữ file trên ổ đĩa. Áp dụng đúng path đã bị guard báo, không chạy lệnh xóa file. Kiểm tra lại `npm run git:check` và `git status`.

## Giới hạn

Hook và ignore là bảo vệ phía máy phát triển, có thể bị người dùng bỏ qua bằng `git add -f`, `--no-verify` hoặc cấu hình Git khác. Pre-push quét cây file hiện tại, không phân tích mọi commit lịch sử. Không thể đảm bảo tuyệt đối không bao giờ đưa file lên server chỉ bằng `.gitignore`; nếu media từng được commit và cần giữ repository cũ, cần kiểm tra/làm sạch lịch sử bằng quy trình riêng, sao lưu trước khi viết lại lịch sử. Với repository gốc mới, hãy bật hooks trước commit đầu.

CI chỉ phát hiện sau khi push; không thay thế kiểm tra cục bộ. GitHub giới hạn file không phải là cơ chế bảo vệ dữ liệu cá nhân. Video / media vẫn ở ổ đĩa, không bị xóa hoặc nén vào tài liệu bàn giao.
