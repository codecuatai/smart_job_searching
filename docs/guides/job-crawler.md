# Crawl dữ liệu job công khai

Script `scripts/crawl_jobs.py` lấy các tin tuyển dụng công khai từ sitemap và trang chi tiết của TopCV/ITviec, chuẩn hóa về schema job của UniTalent và xuất JSON. Script không đăng nhập, không gọi API riêng tư, không giải CAPTCHA và không vượt anti-bot. Nó đọc `robots.txt`, nghỉ tối thiểu giữa các request và bỏ qua nguồn nếu website từ chối truy cập.

## Chạy thử

```powershell
npm run jobs:crawl -- --source itviec --limit 20 --output var/data/itviec-jobs.json
```

`--limit 0` crawl toàn bộ URL job có trong sitemap. Vì mỗi trang chi tiết là một request, nên crawl toàn bộ có thể mất nhiều phút và số lượng thay đổi theo sitemap tại thời điểm chạy.

## Crawl cả hai nguồn

```powershell
npm run jobs:crawl -- --source all --limit 0 --output var/data/crawled-jobs.json
```

TopCV có thể trả `403` tùy mạng/IP. Khi đó script ghi lỗi vào trường `errors`, không cố vượt lớp bảo vệ. Chạy lại từ mạng được TopCV cho phép hoặc xin feed/API/thoả thuận dữ liệu chính thức.

## Nhập vào SQLite

Chỉ nhập sau khi xem file JSON:

```powershell
npm run jobs:crawl -- --source itviec --limit 100 --output var/data/itviec-jobs.json --import-db --owner-email recruitment@vng.com.vn
```

Job được gán cho recruiter nội bộ chỉ để hệ thống hiện tin và xử lý quyền truy cập. Mỗi URL có ID ổn định nên chạy lại sẽ cập nhật bản ghi cùng nguồn, không tạo bản sao. Dữ liệu crawl không được xem là dữ liệu thị trường đầy đủ; cần kiểm tra quyền sử dụng nội dung và điều khoản của từng nguồn trước khi triển khai công khai.
