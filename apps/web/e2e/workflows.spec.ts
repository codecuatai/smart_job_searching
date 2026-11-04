import { test, expect, Page, TestInfo, BrowserContext } from '@playwright/test';
import { randomUUID, createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const password = 'E2E-test-12345';
const unique = () => randomUUID().slice(0, 8);

function pdf(text: string) {
  // Small valid, text-bearing PDF fixture generated in memory. No personal CV is used.
  const stream = `BT /F1 12 Tf 30 100 Td (${text}) Tj ET`;
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`,
  ];
  let output = '%PDF-1.4\n';
  const offsets = [0];
  for (const [index, object] of objects.entries()) {
    offsets.push(Buffer.byteLength(output));
    output += `${index + 1} 0 obj\n${object}\nendobj\n`;
  }
  const xref = Buffer.byteLength(output);
  output += `xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map(n => `${String(n).padStart(10, '0')} 00000 n \n`).join('')}`;
  output += `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(output);
}

async function register(page: Page, role: 'student' | 'recruiter', name: string) {
  const email = `${role}-${unique()}@example.test`;
  await page.goto('/register');
  if (role === 'recruiter') await page.getByRole('button', { name: /Nhà tuyển dụng/ }).click();
  await page.getByLabel(role === 'student' ? 'Họ và tên' : 'Tên doanh nghiệp', { exact: true }).fill(name);
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
  await expect(page).toHaveURL(role === 'student' ? /\/student\/profile$/ : /\/recruiter\/post-job$/);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  return email;
}

async function evidence(page: Page, info: TestInfo, name: string) {
  const path = info.outputPath(`${name}.png`);
  await page.screenshot({ path, fullPage: true });
  await info.attach(name, { path, contentType: 'image/png' });
}

async function noHorizontalOverflow(page: Page) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
}

test('authentication, session persistence, role guard and logout', async ({ page }, info) => {
  await page.goto('/student/jobs');
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Mật khẩu', { exact: true }).fill('incorrect12345');
  await page.getByRole('button', { name: 'Vào không gian làm việc' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Email hoặc mật khẩu không đúng' })).toBeVisible();
  await page.getByRole('button', { name: 'Đăng nhập ứng viên ↗' }).click();
  await expect(page).toHaveURL(/\/student\/jobs$/);
  await expect(page.locator('.job-row').first()).toBeVisible();
  await page.reload();
  await expect(page.locator('.job-row').first()).toBeVisible();
  await page.goto('/recruiter/candidates');
  await expect(page).toHaveURL(/\/student\/jobs$/);
  expect((await page.request.get('/api/candidates')).status()).toBe(403);
  await noHorizontalOverflow(page);
  await evidence(page, info, 'authenticated-jobs');
  const menu = page.getByRole('button', { name: 'Mở menu', exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect((await page.request.get('/api/auth/me')).status()).toBe(401);
});

test('register, validate PDF and persist uploaded CV', async ({ page }, info) => {
  await register(page, 'student', `E2E CV ${unique()}`);
  await expect(page.getByText('Chưa có CV. Chọn một tệp PDF tối đa 5 MB.')).toBeVisible();
  const input = page.getByLabel('Chọn CV dạng PDF', { exact: true });
  await input.setInputFiles({ name: 'invalid.pdf', mimeType: 'application/pdf', buffer: Buffer.from('not a PDF') });
  await expect(page.getByText('Vui lòng chọn tệp PDF hợp lệ.')).toBeVisible();
  const response = page.waitForResponse(r => r.url().endsWith('/api/resumes') && r.request().method() === 'POST' && r.status() === 201);
  await input.setInputFiles({ name: 'e2e-cv.pdf', mimeType: 'application/pdf', buffer: pdf('Python SQL portfolio') });
  expect((await (await response).json()).textExtracted).toBe(true);
  await expect(page.locator('.resume-file-info')).toContainText('e2e-cv.pdf');
  await page.reload();
  await expect(page.locator('.resume-file-info')).toContainText('e2e-cv.pdf');
  await noHorizontalOverflow(page);
  await evidence(page, info, 'cv-persisted');
});

test('complete recruitment workflow across two users with immutable CV and schedule', async ({ page: recruiter, browser, baseURL }, info) => {
  const token = unique();
  const studentName = `E2E Student ${token}`;
  const company = `E2E Company ${token}`;
  const title = `E2E Python SQL ${token}`;
  const contexts: BrowserContext[] = [];
  let createdJobId: string | undefined;
  try {
    await register(recruiter, 'recruiter', company);
    await recruiter.getByLabel(/^Tên vị trí/).fill(title);
    await recruiter.getByLabel(/^Nhóm ngành/).selectOption('backend');
    await recruiter.getByLabel(/^Mô tả công việc/).fill('Build Python APIs using SQL and Docker.');
    await recruiter.getByLabel(/^Kỹ năng và yêu cầu/).fill('Python\nSQL\nDocker');
    await noHorizontalOverflow(recruiter);
    const posted = recruiter.waitForResponse(r => r.url().endsWith('/api/jobs') && r.request().method() === 'POST');
    await recruiter.getByRole('button', { name: 'Đăng tin tuyển dụng', exact: true }).click();
    const job = await (await posted).json();
    createdJobId = job.id;
    expect(job.company).toBe(company);
    await expect(recruiter).toHaveURL(/\/recruiter\/candidates$/);

    const studentContext = await browser.newContext({ baseURL, viewport: recruiter.viewportSize()!, locale: 'vi-VN', timezoneId: 'Asia/Bangkok', isMobile: info.project.name === 'mobile', hasTouch: info.project.name === 'mobile' });
    contexts.push(studentContext);
    const student = await studentContext.newPage();
    await register(student, 'student', studentName);
    await student.getByLabel('Trường học', { exact: true }).fill('E2E University');
    await student.getByLabel('Kỹ năng (cách nhau bằng dấu phẩy)', { exact: true }).fill('Python, SQL');
    await student.getByLabel('Tên dự án', { exact: true }).fill('Python SQL portfolio');
    await student.getByRole('button', { name: 'Lưu hồ sơ', exact: true }).click();
    await expect(student.getByRole('heading', { name: 'Đã lưu hồ sơ', exact: true })).toBeVisible();
    const initialPdf = pdf('Python SQL portfolio version one');
    await student.getByLabel('Chọn CV dạng PDF', { exact: true }).setInputFiles({ name: 'version-one.pdf', mimeType: 'application/pdf', buffer: initialPdf });
    await expect(student.locator('.resume-file-info')).toContainText('version-one.pdf');
    await student.goto('/student/jobs');
    await student.getByRole('textbox', { name: 'Tìm việc làm', exact: true }).fill(token);
    await expect(student.locator('.job-row')).toHaveCount(1);
    const initialScore = Number((await student.locator('.job-score strong').innerText()).replace('%', ''));
    expect(initialScore).toBeGreaterThan(0);
    expect(initialScore).toBeLessThan(85);
    await student.getByRole('link', { name: title, exact: true }).click();
    await expect(student.getByRole('heading', { level: 1 })).toHaveText(title);
    await student.getByRole('button', { name: /Nộp|Ứng tuyển|Gửi CV/ }).first().click();
    const dialog = student.getByRole('dialog');
    await expect(dialog).toContainText('version-one.pdf');
    await dialog.getByRole('button', { name: 'Gửi CV ứng tuyển' }).click();
    await expect(dialog).not.toBeVisible();
    await student.goto('/student/applications');
    await expect(student.locator('.submitted-resume-row')).toContainText(title);
    await expect(student.locator('.submitted-resume-row')).toContainText('version-one.pdf');

    // The same UI must show a server-side conflict, rather than silently accepting duplicates.
    await student.goto(`/student/jobs/${job.id}`);
    await student.getByRole('button', { name: /Nộp|Ứng tuyển|Gửi CV/ }).first().click();
    await student.getByRole('dialog').getByRole('button', { name: 'Gửi CV ứng tuyển' }).click();
    await expect(student.getByText('Bạn đã ứng tuyển vị trí này.')).toBeVisible();
    await student.getByRole('dialog').getByRole('button', { name: 'Đóng', exact: true }).click();

    await student.goto('/student/skill-gap');
    await student.getByLabel('Vị trí mục tiêu').selectOption(job.id);
    await expect(student.getByRole('heading', { name: 'Khoảng trống kỹ năng & lộ trình học', exact: true })).toBeVisible();
    await expect(student.getByText('Docker', { exact: true }).first()).toBeVisible();
    await expect(student.getByRole('heading', { name: '1 kỹ năng cần bổ sung', exact: true })).toBeVisible();

    // Updating the current CV improves recommendations, while submitted CV stays unchanged.
    await student.goto('/student/profile');
    await student.getByLabel('Chọn CV dạng PDF', { exact: true }).setInputFiles({ name: 'version-two.pdf', mimeType: 'application/pdf', buffer: pdf('Python SQL Docker portfolio version two') });
    await expect(student.locator('.resume-file-info')).toContainText('version-two.pdf');
    await student.goto('/student/jobs');
    await student.getByRole('textbox', { name: 'Tìm việc làm', exact: true }).fill(token);
    await expect.poll(async () => Number((await student.locator('.job-score strong').innerText()).replace('%', ''))).toBeGreaterThan(initialScore);
    await student.goto('/student/skill-gap');
    await student.getByLabel('Vị trí mục tiêu').selectOption(job.id);
    await expect(student.getByRole('heading', { name: '0 kỹ năng cần bổ sung', exact: true })).toBeVisible();

    await recruiter.reload();
    await recruiter.getByRole('link', { name: studentName, exact: true }).click();
    await expect(recruiter.getByRole('heading', { level: 1 })).toHaveText(studentName);
    const applicationId = new URL(recruiter.url()).pathname.split('/').pop()!;
    const downloaded = recruiter.waitForEvent('download');
    await recruiter.getByRole('button', { name: 'Tải CV đã ứng tuyển' }).click();
    const file = await downloaded;
    const actual = await readFile((await file.path())!);
    expect(createHash('sha256').update(actual).digest('hex')).toBe(createHash('sha256').update(initialPdf).digest('hex'));

    const stageSelect = recruiter.getByRole('combobox', { name: 'Trạng thái', exact: true });
    await stageSelect.selectOption('reviewing');
    const refreshedCandidate = recruiter.waitForResponse(r => r.request().method() === 'GET' && r.url().endsWith(`/api/candidates/${applicationId}`) && r.status() === 200);
    await recruiter.getByRole('button', { name: 'Lưu cập nhật' }).click();
    await expect(recruiter.getByRole('heading', { name: 'Đã lưu trạng thái', exact: true }).first()).toBeVisible();
    await refreshedCandidate;
    await expect(stageSelect).toHaveValue('reviewing');
    await stageSelect.selectOption('interview');
    await expect(recruiter.getByLabel('Ngày', { exact: true })).toBeVisible();
    const date = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
    await recruiter.getByLabel('Ngày', { exact: true }).fill(date);
    await recruiter.getByLabel('Giờ (Việt Nam)', { exact: true }).fill('09:30');
    await recruiter.getByLabel('Địa điểm / thông tin cuộc họp', { exact: true }).fill(`E2E Meeting ${token}`);
    await recruiter.getByLabel('Người phỏng vấn', { exact: true }).fill('E2E Tech Lead');
    await recruiter.getByRole('button', { name: 'Lưu cập nhật' }).click();
    await expect(recruiter.getByRole('heading', { name: 'Đã lưu trạng thái', exact: true }).first()).toBeVisible();
    await student.goto('/student/applications');
    await expect(student.getByText(`E2E Meeting ${token}`, { exact: true })).toBeVisible();
    await expect(student.getByText(`${date} (09:30)`, { exact: true })).toBeVisible();
    await noHorizontalOverflow(student);
    await evidence(student, info, 'student-interview-scheduled');
    await evidence(recruiter, info, 'recruiter-candidate-reviewed');

    const outsider = await browser.newContext({ baseURL });
    contexts.push(outsider);
    await outsider.request.post('/api/auth/register', { data: { name: 'E2E Other Company', email: `other-${unique()}@example.test`, password, role: 'recruiter' } });
    expect((await outsider.request.get(`/api/candidates/${applicationId}`)).status()).toBe(404);
    expect((await outsider.request.get(`/api/applications/${applicationId}/resume`)).status()).toBe(404);
    expect((await outsider.request.patch(`/api/applications/${applicationId}`, { data: { stage: 'offered' } })).status()).toBe(404);
    expect(await (await outsider.request.get('/api/candidates')).json()).toEqual([]);
    await recruiter.goto('/recruiter/analytics');
    await expect(recruiter.getByRole('heading', { name: 'Xu hướng lương đăng tuyển', exact: true })).toBeVisible();
    const salaryPanel = recruiter.locator('section.analytics-category-panel').filter({ has: recruiter.getByRole('heading', { name: 'Xu hướng lương đăng tuyển', exact: true }) });
    await expect(salaryPanel.getByText(/\d+\.\d+–\d+\.\d+ triệu/).first()).toBeVisible();
    await expect(recruiter.getByRole('heading', { name: 'Chuyển đổi tuyển dụng', exact: true })).toBeVisible();
    await expect(recruiter.getByText(/100% so với giai đoạn trước/).first()).toBeVisible();
    const analyticsExport = await recruiter.request.get('/api/analytics/export.csv');
    expect(analyticsExport.status()).toBe(200);
    expect(analyticsExport.headers()['content-type']).toContain('text/csv');
    await noHorizontalOverflow(recruiter);
  } finally {
    try {
      if (createdJobId) {
        const cleanup = await recruiter.request.delete(`/api/jobs/${createdJobId}`);
        expect([204, 404]).toContain(cleanup.status());
      }
    } finally {
      for (const context of contexts) await context.close();
    }
  }
});

test('interview feedback and history survive reload', async ({ page }, info) => {
  await register(page, 'student', `E2E Interview ${unique()}`);
  await page.goto('/student/mock-interview');
  await expect(page.getByText('Chưa có câu trả lời nào được lưu.', { exact: true })).toBeVisible();
  await page.getByLabel('Câu trả lời của bạn', { exact: true }).fill('Use idempotency key with a unique database constraint and transaction. Add a concurrency test and retry test to verify duplicate requests create one order.');
  await page.getByRole('button', { name: 'Phân tích câu trả lời' }).click();
  await expect(page.getByRole('heading', { name: /Kết quả rubric: \d+\/100/ })).toBeVisible();
  await expect(page.locator('details')).toHaveCount(1);
  await page.locator('summary').click();
  await expect(page.locator('details')).toContainText('concurrency test');
  await noHorizontalOverflow(page);
  await evidence(page, info, 'interview-feedback');
  await page.reload();
  await expect(page.locator('details')).toHaveCount(1);
  await page.getByRole('combobox', { name: 'Chủ đề', exact: true }).selectOption('database');
  await expect(page.getByRole('heading', { name: /Một truy vấn SQL chạy chậm/ })).toBeVisible();
});
