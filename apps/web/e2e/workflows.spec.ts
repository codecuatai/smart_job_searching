import { test, expect, Page, TestInfo, BrowserContext } from '@playwright/test';
import { randomUUID, createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import passwordPdfs from './fixtures/pdf-password-variants.json';

const password = 'E2E-test-12345';
const aiMethod = process.env.E2E_AI_MODE === 'offline' ? /^test-fixture:/ : /^gemini:/;
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
  return encodePdf(objects);
}

function encodePdf(objects: string[]) {
  let output = '%PDF-1.4\n';
  const offsets = [0];
  for (const [index, object] of objects.entries()) {
    offsets.push(Buffer.byteLength(output));
    output += `${index + 1} 0 obj\n${object}\nendobj\n`;
  }
  const xref = Buffer.byteLength(output);
  output += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n${offsets.slice(1).map(n => `${String(n).padStart(10, '0')} 00000 n \n`).join('')}`;
  output += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(output);
}

function blankPdf(pageCount: number) {
  return encodePdf([
    '<< /Type /Catalog /Pages 2 0 R >>',
    `<< /Type /Pages /Kids [${Array.from({ length: pageCount }, (_, i) => `${i + 3} 0 R`).join(' ')}] /Count ${pageCount} >>`,
    ...Array.from({ length: pageCount }, () => '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << >> >>'),
  ]);
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

async function liveAIAction(page:Page,info:TestInfo,path:string,button:string){
  for(let attempt=0;attempt<3;attempt++){
    const pending=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST',{timeout:60000});
    await page.getByRole('button',{name:button,exact:true}).click();
    const response=await pending;
    if(response.status()!==503||attempt===1)return response;
    // Exercise the real user-visible retry path on transient provider failure.
    await expect(page.getByRole('alert').first()).toBeVisible();
    await info.attach('upstream-transient-retry',{body:JSON.stringify({path,status:503,attempt:attempt+1}),contentType:'application/json'});
    await expect(page.getByRole('button',{name:button,exact:true})).toBeEnabled();
  }
  throw new Error('Unreachable');
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
  const uploadError = page.locator('.resume-card').getByRole('alert');
  await expect(uploadError).toContainText('Nội dung file không có định dạng PDF');
  const response = page.waitForResponse(r => r.url().endsWith('/api/resumes') && r.request().method() === 'POST' && r.status() === 201);
  await input.setInputFiles({ name: 'e2e-cv.pdf', mimeType: 'application/pdf', buffer: pdf('Python SQL portfolio') });
  expect((await (await response).json()).textExtracted).toBe(true);
  await expect(page.locator('.resume-file-info')).toContainText('e2e-cv.pdf');
  await expect(uploadError).not.toBeVisible();
  await page.reload();
  await expect(page.locator('.resume-file-info')).toContainText('e2e-cv.pdf');
  await input.setInputFiles({ name: 'corrupt.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4\nnot a document') });
  await expect(uploadError).toContainText('Không đọc được cấu trúc PDF');
  await expect(page.locator('.resume-file-info')).toContainText('e2e-cv.pdf');
  await input.setInputFiles({ name: 'exported.pdf', mimeType: 'application/pdf', buffer: Buffer.concat([Buffer.from('\xef\xbb\xbf\r\n', 'latin1'), pdf('Python SQL Docker')]) });
  await expect(page.locator('.resume-file-info')).toContainText('exported.pdf');
  await expect(uploadError).not.toBeVisible();
  await page.reload();
  await expect(page.locator('.resume-file-info')).toContainText('exported.pdf');
  await noHorizontalOverflow(page);
  await evidence(page, info, 'cv-persisted');
});

const pdfCases = [
  { label: 'empty PDF', filename: 'empty.pdf', bytes: () => Buffer.alloc(0), status: 422, message: 'File PDF rỗng' },
  { label: 'password required', filename: 'locked.pdf', bytes: () => Buffer.from(passwordPdfs.locked, 'base64'), status: 422, message: 'PDF yêu cầu mật khẩu' },
  { label: 'permission restricted but opens without password', filename: 'restricted.pdf', bytes: () => Buffer.from(passwordPdfs.restricted, 'base64'), status: 201, message: 'CV đã lưu nhưng PDF không có lớp văn bản' },
  { label: '31 pages', filename: 'pages.pdf', bytes: () => blankPdf(31), status: 422, message: 'file này có 31 trang' },
  { label: 'PDF over 5MB', filename: 'large.pdf', bytes: () => Buffer.concat([pdf('Python'), Buffer.alloc(5 * 1024 * 1024)]), status: 413, message: 'CV tối đa 5 MB' },
  { label: 'PDF without extractable text', filename: 'scan-like.pdf', bytes: () => blankPdf(1), status: 201, message: 'CV đã lưu nhưng PDF không có lớp văn bản' },
];

for (const item of pdfCases) {
  test(`CV upload: ${item.label}, persist result and retain previous CV on failure`, async ({ page }) => {
    await register(page, 'student', `E2E PDF ${unique()}`);
    const input = page.getByLabel('Chọn CV dạng PDF', { exact: true });
    const initial = pdf('Python SQL baseline');
    await input.setInputFiles({ name: 'previous.pdf', mimeType: 'application/pdf', buffer: initial });
    await expect(page.locator('.resume-file-info')).toContainText('previous.pdf');
    const received = page.waitForResponse(r => r.url().endsWith('/api/resumes') && r.request().method() === 'POST');
    await input.setInputFiles({ name: item.filename, mimeType: 'application/pdf', buffer: item.bytes() });
    const response = await received;
    expect(response.status()).toBe(item.status);
    await expect(page.locator('.resume-card').getByRole('alert')).toContainText(item.message);
    const expectedName = item.status === 201 ? item.filename : 'previous.pdf';
    await expect(page.locator('.resume-file-info')).toContainText(expectedName);
    await page.reload();
    await expect(page.locator('.resume-file-info')).toContainText(expectedName);
    const metadata = await (await page.request.get('/api/resumes/current')).json();
    const download = await page.request.get(`/api/resumes/${metadata.id}/download`);
    expect(download.status()).toBe(200);
    const expectedBytes = item.status === 201 ? item.bytes() : initial;
    expect(createHash('sha256').update(await download.body()).digest('hex')).toBe(createHash('sha256').update(expectedBytes).digest('hex'));
    await noHorizontalOverflow(page);
  });
}

test('account validation, profile validation, job filters and empty state', async ({ page, browser, baseURL }) => {
  const email = await register(page, 'student', `E2E Validation ${unique()}`);
  const other = await browser.newContext({ baseURL });
  try {
    expect((await other.request.post('/api/auth/register', { data: { name: 'Duplicate', email, password, role: 'student' } })).status()).toBe(409);
    expect((await other.request.post('/api/auth/login', { data: { email, password: 'incorrect-12345' } })).status()).toBe(401);
    expect((await page.request.put('/api/profile', { data: { gpa: 5 } })).status()).toBe(422);
    expect((await page.request.get('/api/analytics')).status()).toBe(403);
    await page.goto('/student/jobs');
    await expect(page.locator('.job-row').first()).toBeVisible();
    const filters = page.getByRole('group', { name: 'Lọc lĩnh vực' });
    await filters.getByRole('button', { name: 'Frontend', exact: true }).click();
    await expect(filters.getByRole('button', { name: 'Frontend', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await page.getByRole('textbox', { name: 'Tìm việc làm', exact: true }).fill(`no-match-${unique()}`);
    await expect(page.locator('.job-row')).toHaveCount(0);
    await expect(page.getByText('Chưa tìm thấy vị trí phù hợp', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Xóa bộ lọc', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Tìm việc làm', exact: true })).toHaveValue('');
    await expect(page.locator('.job-row').first()).toBeVisible();
  } finally { await other.close(); }
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
    expect((await student.request.post('/api/applications', { data: { jobId: job.id } })).status()).toBe(422);
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
    const targetJobRow = () => student.locator('.job-row').filter({ hasText: title });
    const initialScore = Number((await targetJobRow().locator('.job-score strong').innerText()).replace('%', ''));
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

    await student.getByLabel('Giờ học mỗi tuần').selectOption('6');
    const planResponse = await liveAIAction(student,info,'/api/skill-gap','Tạo lộ trình AI');
    expect(planResponse.status()).toBe(200);
    const plan = await planResponse.json();
  expect(plan.method).toMatch(aiMethod);
    expect(plan.roadmap.length).toBeGreaterThan(0);
    expect(plan.projectedScore).toBeUndefined();
    await expect(student.getByText('Match Sau 2 tuần', { exact: true })).toHaveCount(0);
    const checked = student.waitForResponse(r => r.url().includes(`/api/skill-gap/${plan.planId}/progress`) && r.request().method() === 'PATCH');
    await student.getByRole('checkbox').first().check();
    expect((await checked).status()).toBe(200);
    await student.reload();
    await student.getByLabel('Vị trí mục tiêu').selectOption(job.id);
    await expect(student.getByRole('checkbox').first()).toBeChecked();
    await evidence(student, info, 'gemini-roadmap');
    await info.attach('gemini-learning-plan', { body: JSON.stringify(plan, null, 2), contentType: 'application/json' });

    // Updating the current CV improves recommendations, while submitted CV stays unchanged.
    await student.goto('/student/profile');
    await student.getByLabel('Chọn CV dạng PDF', { exact: true }).setInputFiles({ name: 'version-two.pdf', mimeType: 'application/pdf', buffer: pdf('Python SQL Docker portfolio version two') });
    await expect(student.locator('.resume-file-info')).toContainText('version-two.pdf');
    await student.goto('/student/jobs');
    await student.getByRole('textbox', { name: 'Tìm việc làm', exact: true }).fill(token);
    await expect.poll(async () => Number((await targetJobRow().locator('.job-score strong').innerText()).replace('%', ''))).toBeGreaterThan(initialScore);
    await student.goto('/student/skill-gap');
    await student.getByLabel('Vị trí mục tiêu').selectOption(job.id);
    await expect(student.getByRole('heading', { name: '0 kỹ năng cần bổ sung', exact: true })).toBeVisible();

    await recruiter.reload();
    if (info.project.name === 'mobile') await recruiter.getByRole('button', {name:'Tìm kiếm & bộ lọc', exact:true}).click();
    await recruiter.getByRole('textbox', { name: 'Tìm ứng viên', exact: true }).fill(`absent-${unique()}`);
    await expect(recruiter.locator('.candidate-result')).toHaveCount(0);
    await recruiter.getByRole('button', { name: 'Xóa tất cả bộ lọc', exact: true }).click();
    await expect(recruiter.locator('.candidate-result')).toHaveCount(1);
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
  const generatedResponse = await liveAIAction(page,info,'/api/interview/questions','Tạo bộ câu hỏi AI');
  expect(generatedResponse.status()).toBe(200);
  const questions = await generatedResponse.json();
  expect(questions).toHaveLength(3);
  expect(questions.every((q: { method: string }) => aiMethod.test(q.method))).toBe(true);
  await expect(page.getByRole('heading', { name: questions[0].question, exact: true })).toBeVisible();
  await page.getByLabel('Câu trả lời của bạn', { exact: true }).fill('Use idempotency key with a unique database constraint and transaction. Add a concurrency test and retry test to verify duplicate requests create one order.');
  const response = await liveAIAction(page,info,'/api/interview/evaluate','Phân tích câu trả lời');
  expect(response.status()).toBe(200);
  const assessment = await response.json();
  expect(assessment.score).toBeGreaterThanOrEqual(0);
  expect(assessment.score).toBeLessThanOrEqual(100);
  expect(assessment.method).toMatch(aiMethod);
  expect(assessment.question).toBe(questions[0].question);
  await info.attach('gemini-interview', { body: JSON.stringify({ questions, assessment }, null, 2), contentType: 'application/json' });
  await expect(page.getByRole('heading', { name: /Kết quả rubric: \d+\/100/ })).toBeVisible();
  await expect(page.locator('details')).toHaveCount(1);
  await page.locator('summary').click();
  await expect(page.locator('details')).toContainText('concurrency test');
  await noHorizontalOverflow(page);
  await evidence(page, info, 'interview-feedback');
  await page.reload();
  await expect(page.locator('details')).toHaveCount(1);
  const databaseQuestion = questions.find((q: { topic: string }) => q.topic === 'database');
  await page.getByRole('combobox', { name: 'Chủ đề', exact: true }).selectOption(databaseQuestion.id);
  await expect(page.getByRole('heading', { name: databaseQuestion.question, exact: true })).toBeVisible();
});

test('Gemini CV extraction, editable confirmation and matching explanation persist', async ({page},info) => {
  await register(page,'student',`E2E Analysis ${unique()}`);
  await page.getByLabel('Chọn CV dạng PDF',{exact:true}).setInputFiles({name:'analysis.pdf',mimeType:'application/pdf',buffer:pdf('Built Python SQL API projects. I do not know Java. 2 years experience.')});
  await expect(page.locator('.cv-analysis-panel')).toBeVisible();
  const analyzed=page.waitForResponse(r => r.url().includes('/analyze') && r.request().method()==='POST',{timeout:60000});
  await page.getByRole('button',{name:'Phân tích CV bằng AI',exact:true}).click();
  const response=await analyzed;
  expect(response.status()).toBe(200);
  const extraction=(await response.json()).analysis;
  expect(extraction.method).toMatch(aiMethod);
  expect(extraction.skills.some((s:{name:string}) => s.name==='Python')).toBe(true);
  expect(extraction.skills.some((s:{name:string}) => s.name==='Java')).toBe(false);
  await page.getByLabel('Kỹ năng xác nhận từ CV',{exact:true}).fill('Python, SQL, Docker');
  await page.getByRole('button',{name:'Xác nhận phân tích CV',exact:true}).click();
  await expect(page.locator('.cv-analysis-panel')).toContainText('Đã xác nhận bởi bạn');
  await page.reload();
  await expect(page.getByLabel('Kỹ năng xác nhận từ CV',{exact:true})).toHaveValue('Docker, Python, SQL');
  await noHorizontalOverflow(page);
  await evidence(page,info,'gemini-cv-confirmed');
  // Seed IDs are resolved from the public list to avoid coupling the analysis test to seed naming.
  const listing=await (await page.request.get('/api/jobs/search?pageSize=1')).json();
  await page.goto(`/student/jobs/${listing.items[0].id}`);
  await expect(page.getByRole('heading',{name:'Cách tính độ phù hợp',exact:true})).toBeVisible();
  await page.getByText('Xem hệ số và bằng chứng',{exact:true}).click();
  await expect(page.getByText('Điểm xếp hạng tham khảo, không phải xác suất được tuyển.',{exact:false})).toBeVisible();
  await noHorizontalOverflow(page);
  await evidence(page,info,'matching-explanation');
});

test('scanned CV is read by real Docker OCR before Gemini', async ({page,browser},info) => {
  await register(page,'student',`E2E OCR ${unique()}`);
  const image=await browser.newPage({viewport:{width:1000,height:700}});
  await image.setContent('<html><body style="background:white;color:black;font:32px Arial;padding:40px"><h1>Candidate CV</h1><p>Built Python and SQL API projects.</p><p>2 years experience with Python.</p></body></html>');
  const jpeg=await image.screenshot({type:'jpeg',quality:95});
  await image.close();
  const objects:Buffer[]=[
    Buffer.from('<< /Type /Catalog /Pages 2 0 R >>'),
    Buffer.from('<< /Type /Pages /Kids [3 0 R] /Count 1 >>'),
    Buffer.from('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1000 700] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>'),
    Buffer.concat([Buffer.from(`<< /Type /XObject /Subtype /Image /Width 1000 /Height 700 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`),jpeg,Buffer.from('\nendstream')]),
    Buffer.from('<< /Length 31 >>\nstream\nq 1000 0 0 700 0 0 cm /Im0 Do Q\nendstream'),
  ];
  const parts:Buffer[]=[Buffer.from('%PDF-1.4\n')];const offsets=[0];
  for(const [i,obj] of objects.entries()){offsets.push(Buffer.concat(parts).length);parts.push(Buffer.from(`${i+1} 0 obj\n`),obj,Buffer.from('\nendobj\n'));}
  const xref=Buffer.concat(parts).length;
  parts.push(Buffer.from(`xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map(n=>`${String(n).padStart(10,'0')} 00000 n \n`).join('')}trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`));
  await page.getByLabel('Chọn CV dạng PDF',{exact:true}).setInputFiles({name:'scanned.pdf',mimeType:'application/pdf',buffer:Buffer.concat(parts)});
  await expect(page.locator('.cv-analysis-panel')).toContainText('CV chưa có lớp chữ');
  const result=page.waitForResponse(r=>r.url().includes('/analyze')&&r.request().method()==='POST',{timeout:90000});
  await page.getByRole('button',{name:'Phân tích CV bằng AI',exact:true}).click();
  const response=await result;expect(response.status()).toBe(200);
  const extraction=(await response.json()).analysis;
  expect(extraction.ocrUsed).toBe(true);
  expect(extraction.skills.some((s:{name:string})=>s.name==='Python')).toBe(true);
  await expect(page.locator('.cv-analysis-panel')).toContainText('Đã nhận diện chữ bằng OCR');
  await info.attach('ocr-extraction',{body:JSON.stringify(extraction,null,2),contentType:'application/json'});
});

test('Metabase dashboard questions execute against aggregate-only warehouse',async ({page},info)=>{
  const url=process.env.BI_TEST_URL||'http://127.0.0.1:3001';
  const login=await page.request.post(`${url}/api/session`,{data:{username:process.env.BI_ADMIN_EMAIL||'bi-admin@unitalent.local',password:process.env.BI_ADMIN_PASSWORD||'Local-BI-Admin-4829!'}});
  expect(login.status()).toBe(200);
  const headers={'X-Metabase-Session':(await login.json()).id};
  const cardsResponse=await page.request.get(`${url}/api/card`,{headers});
  const payload=await cardsResponse.json();
  const cards=(Array.isArray(payload)?payload:payload.data).filter((c:{name:string})=>c.name.startsWith('TH3 · '));
  expect(cards).toHaveLength(6);
  const evidenceRows=[];
  for(const card of cards){
    const response=await page.request.post(`${url}/api/card/${card.id}/query`,{headers,data:{parameters:[]}});
    expect(response.status()).toBe(202);
    const result=await response.json();
    expect(result.status).toBe('completed');
    evidenceRows.push({name:card.name,rows:result.data.rows});
  }
  await info.attach('metabase-query-results',{body:JSON.stringify(evidenceRows,null,2),contentType:'application/json'});
});
