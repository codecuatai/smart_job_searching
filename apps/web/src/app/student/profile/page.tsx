'use client';
import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { api } from '@/lib/api';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import ResumeManager from '@/components/ResumeManager';
import { PageHeader } from '@/components/WorkspaceUI';

interface Profile {
  university: string; major: string; year: string; gpa: number; targetRole: string;
  skills: string[]; projectTitle: string; projectSummary: string; projectRepo: string;
}
const empty: Profile = { university: '', major: '', year: '', gpa: 0, targetRole: '', skills: [], projectTitle: '', projectSummary: '', projectRepo: '' };
export default function ProfilePage() {
  const { user } = useAuth(); const { showToast } = useToast();
  const { data, error, reload } = useResource<{ profile: Profile }>('/profile');
  const [form, setForm] = useState<Profile>(empty);
  const [skills, setSkills] = useState(''); const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState('');
  useEffect(() => { if (data) { setForm({ ...empty, ...data.profile }); setSkills((data.profile.skills || []).join(', ')); } }, [data]);
  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setSaveError('');
    try {
      await api('/profile', { method: 'PUT', body: JSON.stringify({ ...form, skills: skills.split(',').map(s => s.trim()).filter(Boolean) }) });
      showToast('Đã lưu hồ sơ', 'Mức phù hợp việc làm sẽ được tính lại từ hồ sơ và văn bản CV.', 'success');
    } catch (err) { setSaveError(err instanceof Error ? err.message : 'Không lưu được hồ sơ.'); }
    finally { setBusy(false); }
  };
  if (!data || error) return <DataState error={error} retry={reload} />;
  return <div className="live-page">
    <PageHeader title="Hồ sơ năng lực" description={`${user?.name} · CV là bằng chứng chính để gợi ý việc làm.`} action={<Link href="/student/cv-review">So sánh từng CV với việc làm →</Link>} />
    <nav className="section-tabs" aria-label="Các phần hồ sơ"><a href="#resume-heading">CV & phân tích</a><a href="#profile-fields">Thông tin bổ sung</a></nav>
    <ResumeManager />
    <form id="profile-fields" className="live-panel live-form" onSubmit={save}>
      <p className="field-hint">Thông tin bổ sung giúp hệ thống hiểu định hướng của bạn. Dữ liệu này không thay thế bằng chứng trong CV.</p>
      <h2>Học vấn & định hướng</h2>
      <div className="live-grid">
        {(['university', 'major', 'year', 'targetRole'] as const).map(key => <label className="live-field" key={key}>
          {{ university: 'Trường học', major: 'Chuyên ngành', year: 'Năm học', targetRole: 'Vị trí mong muốn' }[key]}
          <input value={form[key]} maxLength={key === 'year' ? 100 : 200} onChange={e => setForm({ ...form, [key]: e.target.value })} />
        </label>)}
        <label className="live-field">GPA / 4<input type="number" min={0} max={4} step="0.01" value={form.gpa} onChange={e => setForm({ ...form, gpa: Number(e.target.value) })} /></label>
        <label className="live-field">Kỹ năng (cách nhau bằng dấu phẩy)<input value={skills} onChange={e => setSkills(e.target.value)} placeholder="Java, SQL, Docker" /></label>
      </div>
      <h2>Dự án tiêu biểu</h2>
      <label className="live-field">Tên dự án<input maxLength={200} value={form.projectTitle} onChange={e => setForm({ ...form, projectTitle: e.target.value })} /></label>
      <label className="live-field">Repository GitHub<input type="url" value={form.projectRepo} onChange={e => setForm({ ...form, projectRepo: e.target.value })} placeholder="https://github.com/owner/repo" /></label>
      <label className="live-field">Mô tả dự án và công nghệ<textarea rows={5} maxLength={5000} value={form.projectSummary} onChange={e => setForm({ ...form, projectSummary: e.target.value })} /></label>
      {saveError && <p role="alert" className="form-error">{saveError}</p>}
      <button className="live-primary" disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu hồ sơ'}</button>
    </form>
  </div>;
}
