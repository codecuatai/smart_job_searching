# Hợp đồng API v1

Backend local: `http://127.0.0.1:8000`. Qua Next: `http://localhost:3000/api/...`. Swagger tự sinh tại `/docs` trên backend. Dùng cookie `unitalent_session`, không dùng bearer token. JSON UTF-8 trừ endpoint upload (multipart) và tải CV (PDF).

## Xác thực

| Method | Path | Quyền | Nội dung |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | Công khai | `name`, `email`, `password` (8–128), `role` (`student` / `recruiter`), trả 201 + cookie |
| POST | `/api/auth/login` | Công khai | `email`, `password`, trả user + cookie |
| GET | `/api/auth/me` | Đã đăng nhập | `{id,name,email,role}` |
| POST | `/api/auth/logout` | Có/không phiên | Thu hồi cookie hiện tại, trả 204 |
| GET | `/api/health` | Công khai | `{status,database,ai}`, status có thể `degraded` |

Ví dụ kiểm tra bằng Python sau setup, chạy tại thư mục gốc:

```python
import httpx
with httpx.Client(base_url='http://127.0.0.1:8000') as client:
    result = client.post('/api/auth/login', json={
        'email': 'nam.nguyen@hcmut.edu.vn', 'password': 'demo12345'
    })
    result.raise_for_status()
    print(client.get('/api/jobs').json())
```

Client phải giữ cookie giữa các request. Qua trình duyệt, mutation cần Origin nằm trong `ALLOWED_ORIGINS`; ví dụ frontend port 3000. Swagger cùng cổng backend có thể bị kiểm tra Origin khi gửi mutation; thêm `http://127.0.0.1:8000` vào danh sách khi cần thử trực tiếp từ Swagger.

## Hồ sơ và việc làm

| Method | Path | Quyền | Nội dung |
| --- | --- | --- | --- |
| GET | `/api/profile` | student | Hồ sơ dạng Candidate, kèm `profile` với trường chỉnh sửa |
| PUT | `/api/profile` | student | Thay toàn bộ trường hồ sơ theo schema dưới |
| GET | `/api/jobs` | Đã đăng nhập | Mọi tin; student được tính điểm riêng, sắp xếp giảm dần |
| GET | `/api/jobs/{job_id}` | Đã đăng nhập | Chi tiết, 404 nếu sai ID |
| POST | `/api/jobs` | recruiter | Tạo tin thuộc tài khoản hiện tại, trả 201 |
| GET | `/api/skill-gap?jobId=...` | student | Kỹ năng thiếu và roadmap; bỏ jobId để chọn tin phù hợp nhất |

PUT hồ sơ là **replace**, các trường không gửi sẽ về mặc định:

```json
{
  "university": "Đại học của bạn", "major": "CNTT", "year": "Năm 4", "gpa": 3.5,
  "targetRole": "Backend Engineer", "skills": ["Python", "SQL", "Docker"],
  "projectTitle": "Ứng dụng quản lý việc làm",
  "projectSummary": "REST API bằng FastAPI, PostgreSQL, kiểm thử pytest",
  "projectRepo": "https://github.com/owner/repo"
}
```

POST tin tuyển dụng:

```json
{
  "title": "Junior Python Engineer", "location": "TP.HCM",
  "workType": "Full-time", "salary": "Thỏa thuận", "category": "backend",
  "description": "Xây dựng API và xử lý dữ liệu cho sản phẩm.",
  "requirements": ["Python", "SQL", "Docker"],
  "tags": ["Python", "SQL", "Docker"], "benefits": ["Đào tạo nội bộ"],
  "projectSubstituteNote": "Ưu tiên đồ án có kiểm thử", "astThreshold": 0
}
```

`category`: services/api/apps/web/ai/devops/mobile. `workType`: Full-time/Internship/Part-time. `company`, owner và ID do backend gán. `astThreshold` chỉ là trường tham khảo, chưa có engine thẩm định. Điểm AI trả `matchScore`, `matchedSkills`, `missingSkills`, `coverage`, `cosineSimilarity`, `method`, `explanation`. Tin seed có `isDemo=true`.

## CV và đơn ứng tuyển

| Method | Path | Quyền | Nội dung |
| --- | --- | --- | --- |
| POST | `/api/resumes` | student | multipart trường `file`; PDF ≤5 MB / 30 trang, trả `{id,name,size,textExtracted}` |
| GET | `/api/resumes/current` | student | Metadata CV gần nhất hoặc JSON `null` |
| GET | `/api/resumes/{id}/download` | Chủ CV | PDF attachment |
| POST | `/api/applications` | student | `{ "jobId": "..." }`; lấy CV gần nhất, trả 201 `{id,stage}` |
| GET | `/api/applications` | Đã đăng nhập | Student: đơn của mình; recruiter: đơn thuộc tin của mình |
| GET | `/api/applications/{id}/resume` | Chủ đơn hoặc chủ tin | Bản CV đã đính kèm lúc nộp |
| PATCH | `/api/applications/{id}` | Recruiter chủ tin | Stage và lịch hẹn |
| GET | `/api/candidates` | recruiter | Hồ sơ ứng viên theo từng đơn thuộc tin của mình |
| GET | `/api/candidates/{id}` | recruiter chủ tin | `id` là **application ID**, không phải user ID |

Các trạng thái hợp lệ: submitted → reviewing → interview → offered. MVP cho phép recruiter sửa về bất kỳ trạng thái hợp lệ nào để chỉnh sai sót. Sinh viên không có quyền sửa stage.

```json
{
  "stage": "interview",
  "interviewSchedule": {
    "date": "2026-11-01", "time": "09:30",
    "format": "Văn phòng công ty / đường dẫn cuộc họp",
    "interviewer": "Người phụ trách kỹ thuật"
  }
}
```

Ngày/giờ theo giờ Việt Nam. Gửi stage khác có thể bỏ schedule; lịch cũ được giữ nếu không cung cấp lịch mới. Chưa gửi email, tạo cuộc họp hoặc gọi Google Calendar.

## Phỏng vấn và thống kê

| Method | Path | Quyền | Nội dung |
| --- | --- | --- | --- |
| GET | `/api/interview/questions` | student | Danh sách `{id,question}` |
| POST | `/api/interview/evaluate` | student | `{questionId,answer}` (1–10.000 ký tự); lưu lịch sử |
| GET | `/api/interview/history` | student | Tối đa 50 lượt mới nhất của mình |
| GET | `/api/analytics` | recruiter | `totalJobs,totalStudents,marketStats,categoryDistribution,salaryStats,hiringFunnel,totalApplications,scope,updatedAt`; hỗ trợ `category` |
| GET | `/api/analytics/export.csv` | recruiter | Xuất các quan sát skill demand và salary dạng CSV; hỗ trợ `category` |

Analytics dùng nhãn kỹ năng chính xác, tỷ lệ lấy mẫu số là tổng jobs / tổng student trong database. Thiếu hụt = max(0, nhu cầu − nguồn cung); đây là điểm phần trăm, không phải tỷ lệ tăng trưởng. `salaryStats` tổng hợp khoảng lương trung bình theo ngành từ tin có chuỗi lương phân tích được; `hiringFunnel` đếm số hồ sơ từng đạt đến mỗi giai đoạn và tỷ lệ so với giai đoạn liền trước, còn `totalApplications` là số đơn thuộc các tin của nhà tuyển dụng đang đăng nhập. Giai đoạn được ghi vào `application_stage_events`; dữ liệu đơn cũ được khởi tạo từ trạng thái hiện tại khi nâng schema. Các thống kê lương vẫn chỉ phản ánh tin trong hệ thống, không đại diện thị trường lao động bên ngoài. Xem [AI README](../../services/ai/README.md) về điểm rubric.

## Lỗi và giới hạn

| HTTP | Ý nghĩa |
| --- | --- |
| 401 | Chưa đăng nhập / phiên hết hạn / đăng nhập sai |
| 403 | Sai vai trò hoặc Origin mutation không được phép |
| 404 | ID không tồn tại hoặc không thuộc quyền truy cập |
| 409 | Email đã có / đơn ứng tuyển bị trùng |
| 413 | File CV quá 5 MB |
| 422 | Payload không hợp lệ / CV không đọc được / chưa có CV |
| 503 | AI không kết nối được / timeout / trả lỗi ngoài dự kiến |

Phần lớn lỗi trả `{ "detail": "thông báo" }`; Pydantic trả mảng chi tiết ở `detail`. File scan không có text vẫn được lưu; frontend thông báo nhập kỹ năng thủ công. API chưa có pagination (trừ history), rate limit, reset mật khẩu hoặc xóa tài khoản; không dùng trực tiếp ở quy mô công khai khi chưa bổ sung.
