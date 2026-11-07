import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';

function pdf(text: string) {
  const stream = `BT /F1 12 Tf 30 100 Td (${text}) Tj ET`;
  const objects = ['<< /Type /Catalog /Pages 2 0 R >>', '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`];
  let output = '%PDF-1.4\n'; const offsets = [0];
  objects.forEach((o, i) => { offsets.push(Buffer.byteLength(output)); output += `${i + 1} 0 obj\n${o}\nendobj\n`; });
  const xref = Buffer.byteLength(output);
  output += `xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map(n => `${String(n).padStart(10, '0')} 00000 n \n`).join('')}trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(output);
}

test('CV consultation preserves selected version, evidence, editable outline and export', async ({ page }, info) => {
  if (process.env.E2E_AI_MODE !== 'offline') test.setTimeout(300000);
  const registration = await page.request.post('/api/auth/register', { data: { name: 'E2E CV review', email: `cv-review-${randomUUID()}@example.test`, password: 'Test-password-123', role: 'student' } });
  expect(registration.status()).toBe(201);
  const upload = await page.request.post('/api/resumes', { multipart: { file: { name: 'original-python.pdf', mimeType: 'application/pdf', buffer: pdf('Python project with API tests') } } });
  expect(upload.status()).toBe(201); const cv = await upload.json();
  expect((await page.request.patch(`/api/resumes/${cv.id}/analysis`, { data: { skills: ['Python'], experienceYears: null } })).status()).toBe(200);
  await page.request.post('/api/resumes', { multipart: { file: { name: 'newer-full.pdf', mimeType: 'application/pdf', buffer: pdf('Python SQL Docker Git project') } } });
  await page.goto(`/student/cv-review?cvId=${cv.id}`);
  await expect(page.getByRole('heading', { name: 'So sánh từng CV với việc làm', exact: true })).toBeVisible();
  await page.getByLabel('Phiên bản CV').selectOption(cv.id);
  const created = await page.request.post('/api/cv-consultations', { data: { resumeId: cv.id, customJd: { title: 'Backend Python Internship', company: 'E2E Example', text: 'Python required\nSQL required\nDocker required\nGit required', mustHaveSkills: ['SQL'] } } });
  expect(created.status()).toBe(201);
  const record = await created.json();
  await page.goto(`/student/cv-review/${record.id}`);
  await expect(page).toHaveURL(/\/student\/cv-review\/[^/]+$/, { timeout: 30000 });
  await expect(page.getByText('3 kỹ năng được ưu tiên cải thiện.', { exact: false })).toBeVisible();
  await expect(page.getByText('Checklist 6 yêu cầu bài nộp')).toHaveCount(0);
  await expect(page.getByText('original-python.pdf', { exact: false }).first()).toBeVisible();
  await expect(page.getByRole('tabpanel')).toContainText('Đối chiếu yêu cầu và bằng chứng');
  await expect(page.getByRole('tabpanel')).not.toContainText('Outline CV trước và sau');
  await page.getByRole('tab', { name: 'Outline CV', exact: true }).click();
  const pending = page.waitForResponse(r => /\/cv-consultations\/[^/]+\/analyze$/.test(r.url()) && r.request().method() === 'POST', { timeout: 85000 });
  await page.getByRole('button', { name: 'Tạo Outline bằng AI' }).click();
  const response = await pending; expect(response.status()).toBe(200);
  const result = await response.json();
  expect(result.data.outlineMethod).toMatch(process.env.E2E_AI_MODE === 'offline' ? /^test-fixture:/ : /^gemini:/);
  await page.getByLabel('Tiêu đề mục 1', { exact: true }).fill('Dự án Python có minh chứng');
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).first().click();
  await expect(page.getByText('Đã lưu thay đổi.', { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole('tab', { name: 'Outline CV', exact: true }).click();
  await expect(page.getByLabel('Tiêu đề mục 1', { exact: true })).toHaveValue('Dự án Python có minh chứng');
  await expect(page.getByText('Chuẩn bị video')).toHaveCount(0);
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Xuất báo cáo Markdown', exact: true }).first().click();
  expect((await download).suggestedFilename()).toMatch(/\.md$/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: info.outputPath('cv-review.png'), fullPage: true });
  await info.attach('outline-provider', { body: JSON.stringify({ method: result.data.outlineMethod }), contentType: 'application/json' });
});

test('Outline failure keeps saved input and never invents three gaps', async ({ page }, info) => {
  await page.request.post('/api/auth/register', { data: { name: 'E2E CV failure', email: `cv-error-${randomUUID()}@example.test`, password: 'Test-password-123', role: 'student' } });
  const upload = await page.request.post('/api/resumes', { multipart: { file: { name: 'python.pdf', mimeType: 'application/pdf', buffer: pdf('Python project') } } });
  const cv = await upload.json();
  await page.request.patch(`/api/resumes/${cv.id}/analysis`, { data: { skills: ['Python'], experienceYears: null } });
  const created = await page.request.post('/api/cv-consultations', { data: { resumeId: cv.id, customJd: { title: 'Python Intern', company: 'E2E Example', text: 'Python required\nSQL required' } } });
  expect(created.status()).toBe(201); const record = await created.json();
  await page.goto(`/student/cv-review/${record.id}`);
  await expect(page.getByText('1 kỹ năng được ưu tiên cải thiện.', { exact: false })).toBeVisible();
  await page.getByRole('tab', { name: 'Outline CV', exact: true }).click();
  const current = page.getByLabel('Bố cục hiện tại');
  await current.fill('Projects\nEducation');
  await page.route(`**/api/cv-consultations/${record.id}/analyze`, route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'E2E provider unavailable' }) }));
  await page.getByRole('button', { name: 'Tạo Outline bằng AI' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'E2E provider unavailable' })).toBeVisible();
  await expect(current).toHaveValue('Projects\nEducation');
  await page.reload();
  await page.getByRole('tab', { name: 'Outline CV', exact: true }).click();
  await expect(current).toHaveValue('Projects\nEducation');
  await page.unroute(`**/api/cv-consultations/${record.id}/analyze`);
  await page.getByRole('tab', { name: 'Outline CV', exact: true }).click();
  await page.getByRole('button', { name: 'Tạo Outline bằng AI' }).click();
  await expect(page.getByLabel('Tiêu đề mục 1', { exact: true })).toBeVisible({ timeout: 85000 });
  await page.getByRole('tab', { name: 'Đối chiếu kỹ năng', exact: true }).click();
  await expect(page.getByText('1 kỹ năng được ưu tiên cải thiện.', { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: info.outputPath('insufficient-gaps.png'), fullPage: true });
});

test('job matching outage keeps the selected CV visible', async ({ page }) => {
  expect((await page.request.post('/api/auth/register', { data: { name: 'E2E independent inputs', email: `cv-inputs-${randomUUID()}@example.test`, password: 'Test-password-123', role: 'student' } })).status()).toBe(201);
  const uploaded = await page.request.post('/api/resumes', { multipart: { file: { name: 'python.pdf', mimeType: 'application/pdf', buffer: pdf('Python project') } } });
  expect(uploaded.status()).toBe(201); const cv = await uploaded.json();
  await page.route(`**/api/resumes/${cv.id}/matches*`, route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Injected match outage' }) }));
  await page.goto(`/student/cv-review?cvId=${cv.id}`);
  await expect(page.getByLabel('Phiên bản CV')).toHaveValue(cv.id);
  await expect(page.getByRole('alert').filter({ hasText: 'Injected match outage' })).toBeVisible();
  await expect(page.getByText('Bạn chưa tải CV lên.')).toHaveCount(0);
});

test('each CV ranks jobs separately and opens its own skill-gap page', async ({ page }, info) => {
  const token = randomUUID().slice(0, 8);
  expect((await page.request.post('/api/auth/register', { data: { name: 'E2E recruiter', email: `cv-recruiter-${randomUUID()}@example.test`, password: 'Test-password-123', role: 'recruiter' } })).status()).toBe(201);
  const post = async (skill: string) => {
    const response = await page.request.post('/api/jobs', { data: { title: `E2E ${skill} ${token}`, location: 'Hà Nội', category: 'backend', description: `Build ${skill} services for this role.`, requirements: [`${skill} required`], tags: [skill] } });
    expect(response.status()).toBe(201); return response.json();
  };
  const pythonJob = await post('Python');
  const sqlJob = await post('SQL');
  expect((await page.request.post('/api/auth/register', { data: { name: 'E2E CV comparison', email: `cv-compare-${randomUUID()}@example.test`, password: 'Test-password-123', role: 'student' } })).status()).toBe(201);
  const upload = async (name: string, content: string) => {
    const response = await page.request.post('/api/resumes', { multipart: { file: { name, mimeType: 'application/pdf', buffer: pdf(content) } } });
    expect(response.status()).toBe(201); return response.json();
  };
  const pythonCv = await upload('python-cv.pdf', 'Python API project');
  const sqlCv = await upload('sql-cv.pdf', 'SQL database project');
  await page.goto('/student/jobs');
  await page.getByRole('textbox', { name: 'Tìm việc làm' }).fill(`E2E Python ${token}`);
  const card = page.locator('.job-row').filter({ hasText: pythonJob.title });
  await expect(card).toBeVisible();
  await card.getByRole('link', { name: 'So sánh với CV' }).click();
  await expect(page.getByRole('heading', { name: 'So sánh từng CV với việc làm' })).toBeVisible();
  await expect(page.getByLabel('Phiên bản CV')).toHaveValue(sqlCv.id);
  const featured = page.locator('.review-match.is-featured');
  await expect(featured).toContainText(pythonJob.title);
  await expect(featured).toContainText('Python');
  expect(Number(await featured.locator('.job-score strong').innerText())).toBe(0);
  await page.getByLabel('Phiên bản CV').selectOption(pythonCv.id);
  await expect(featured).toContainText('Nhận diện trong CV: Python');
  expect(Number(await featured.locator('.job-score strong').innerText())).toBeGreaterThan(0);
  const pending = page.waitForResponse(r => r.url().endsWith('/api/cv-consultations') && r.request().method() === 'POST');
  await featured.getByRole('button', { name: 'Xem skill gaps' }).click();
  const created = await pending; expect(created.status()).toBe(201);
  const record = await created.json();
  expect(record.snapshot.resumeId).toBe(pythonCv.id);
  expect(record.snapshot.job.id).toBe(pythonJob.id);
  await expect(page.getByRole('heading', { level: 1, name: pythonJob.title })).toBeVisible();
  await expect(page.getByText('CV: python-cv.pdf', { exact: false })).toBeVisible();
  await page.getByRole('link', { name: 'Job phù hợp với CV này' }).click();
  await expect(page.getByLabel('Phiên bản CV')).toHaveValue(pythonCv.id);
  await expect(page.locator('.review-match.is-featured')).toHaveCount(0);
  await expect(page.getByText(sqlJob.title, { exact: true }).first()).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: info.outputPath('cv-specific-matches.png'), fullPage: true });
});
