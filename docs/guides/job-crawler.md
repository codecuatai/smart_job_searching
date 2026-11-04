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

### Nhập vào database đang phục vụ giao diện

Local và Docker có database riêng. File `var/data/unitalent.db` trên máy không
tự đồng bộ với volume của API Docker. Khi giao diện chạy bằng Docker, dùng:

```powershell
npm run jobs:import -- --target docker --input var/data/crawled-jobs.json
```

`--target docker` yêu cầu API container đang chạy, không tự ghi sang local nếu
container không tồn tại. `--target local` chọn database trên máy. Mặc định
`--target auto` ưu tiên API Docker đang chạy và in rõ target trước khi ghi.
Import tạo backup trong thư mục `backups` cạnh database, cập nhật cùng URL
không làm mất ứng tuyển và đồng bộ chỉ mục kỹ năng.

Chỉ nhập sau khi xem file JSON:

```powershell
npm run jobs:crawl -- --source itviec --limit 100 --output var/data/itviec-jobs.json --import-db --owner-email recruitment@vng.com.vn
```

Có thể thêm `--target docker` vào lệnh trên để chọn tường minh. Wrapper npm
crawl ra JSON trước rồi import vào target đã chọn. Khi chạy trực tiếp Python
`scripts/crawl_jobs.py --import-db`, database vẫn là database local của tiến
trình Python; ưu tiên lệnh npm khi dùng Docker.

Job được gán cho recruiter nội bộ chỉ để hệ thống hiện tin và xử lý quyền truy cập. Mỗi URL có ID ổn định nên chạy lại sẽ cập nhật bản ghi cùng nguồn, không tạo bản sao. Dữ liệu crawl không được xem là dữ liệu thị trường đầy đủ; cần kiểm tra quyền sử dụng nội dung và điều khoản của từng nguồn trước khi triển khai công khai.

## Dọn job E2E

```powershell
npm run jobs:cleanup-e2e -- --target docker
npm run jobs:cleanup-e2e -- --target docker --apply
```

Lệnh đầu chỉ đếm. Lệnh thứ hai sao lưu rồi xóa job có đủ ba dấu hiệu fixture:
title `E2E Python SQL <token>`, company `E2E Company <cùng token>` và tài khoản
recruiter `recruiter-<token>@example.test`. Các ứng tuyển/skill index/prediction
thuộc job đó được dọn theo; tài khoản, hồ sơ và CV được giữ. E2E workflow cũng
xóa job mình tạo trong `finally` qua endpoint DELETE có kiểm tra chủ sở hữu.

## Kiểm tra ngày 04/11/2026

Database Docker hiện có 639 job: 635 tin ITviec và 4 job mẫu; không còn job
E2E. Lần crawl gần nhất đã lấy 100 URL ITviec và upsert an toàn theo URL, nên
không tạo bản sao khi chạy lại. Các bản sao lưu import nằm trong thư mục
`backups` cạnh database Docker.

Danh sách ứng viên gửi tối đa 500 tin mỗi lần tới dịch vụ AI rồi xếp hạng chung
tất cả kết quả, nên nguồn dữ liệu trên 500 tin không làm `/api/jobs` trả 422.

TopCV trả HTTP 403 tại sitemap khi kiểm tra từ máy này; số tin TopCV nhập là 0.
Không gán nhãn TopCV cho tin ITviec hay dữ liệu mẫu. Cần feed/API hoặc đường
truy cập được nguồn cho phép để bổ sung TopCV. Khi crawl thất bại, script giữ
nguyên file JSON crawl thành công trước đó thay vì ghi đè thành `jobs: []`.
