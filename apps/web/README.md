# Web — apps/web

Next.js 15.5.28, React 19, TypeScript strict và Tailwind. Chứa giao diện hai vai trò, API client, context và các test E2E.

## Cấu hình và chạy

Chỉ đọc `.env` ở gốc repository qua `../../scripts/lib/env.mjs`. Không tạo `.env` hoặc `.env.local` trong thư mục này. Chạy từ root:

```powershell
npm run setup
npm run dev
npm run build
npm --prefix apps/web start
```

Có thể chạy `npm run dev/build/start` ngay trong `apps/web`: script wrapper vẫn tìm đúng `.env` gốc và nhận cổng. Docker đặt hostname nội bộ `0.0.0.0`; local mặc định bind `127.0.0.1`.

`WEB_PORT` quyết định cổng web. `API_URL` tùy chọn; nếu không đặt, proxy tới `http://127.0.0.1:API_PORT`. Docker tính API_URL từ tên service `api`. Đổi API_URL/API_PORT cần build lại vì rewrite của Next được chốt lúc build. Xem [configuration.md](../../docs/guides/configuration.md).

## Mã nguồn

- `src/app/`: landing, login/register, student và recruiter.
- `src/context/`: Auth, Resume và Toast; CV/đơn được đọc theo tài khoản từ API.
- `src/lib/api.ts`: request cùng origin `/api/*`, cookie, lỗi và tải CV.
- `src/lib/useResource.ts`: hủy request khi rời trang, tải/lỗi/thử lại.
- `src/data/mockData.ts`: chỉ dùng cho preview minh họa ở landing. Trang nghiệp vụ lấy dữ liệu API thật; seed được giữ tại `services/api/seed/demo.json`.
- `e2e/`, `playwright.config.mjs`: kiểm thử trình duyệt desktop/mobile.

`RoleGuard` chuyển hướng giao diện; kiểm tra quyền thực vẫn do API thực hiện. Session không lưu ở localStorage. `ResumeContext` bỏ kết quả request cũ khi đổi tài khoản. Checklist học còn lưu trong state trang, chưa lưu bền.

## Routes

`/`, `/login`, `/register`; sinh viên: `/student/jobs`, `/student/jobs/[id]`, `/student/profile`, `/student/applications`, `/student/skill-gap`, `/student/mock-interview`; recruiter: `/recruiter/post-job`, `/recruiter/candidates`, `/recruiter/candidates/[applicationId]`, `/recruiter/analytics`.

## Kiểm tra

Từ root: `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e`. E2E cần đủ dịch vụ đang chạy, nhận E2E_BASE_URL hoặc suy ra WEB_PORT từ `.env` gốc. Báo cáo được ghi vào `artifacts/e2e/`, không đặt trong source. [Hướng dẫn E2E](../../docs/guides/e2e.md).
