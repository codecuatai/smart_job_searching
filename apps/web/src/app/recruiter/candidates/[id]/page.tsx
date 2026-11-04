'use client';
import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Candidate, ApplicationStage } from '@/types';
import { api, download } from '@/lib/api';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import { useToast } from '@/context/ToastContext';
import { useResume } from '@/context/ResumeContext';

interface Schedule { date: string; time: string; format: string; interviewer: string }
export default function CandidatePage() {
  const params = useParams(); const id = String(params.id);
  const { data: candidate, error, reload } = useResource<Candidate & { interviewSchedule?: Schedule }>(`/candidates/${id}`);
  const { showToast } = useToast(); const { refresh } = useResume();
  const [stage, setStage] = useState<ApplicationStage>('reviewing');
  const [schedule, setSchedule] = useState<Schedule>({ date: '', time: '09:00', format: 'Trực tuyến', interviewer: '' });
  const [busy, setBusy] = useState(false); const [saveError, setSaveError] = useState('');
  useEffect(() => { if (candidate) { setStage(candidate.status); if (candidate.interviewSchedule) setSchedule(candidate.interviewSchedule); } }, [candidate]);
  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setSaveError('');
    try {
      await api(`/applications/${id}`, { method: 'PATCH', body: JSON.stringify({ stage, interviewSchedule: stage === 'interview' ? schedule : null }) });
      showToast('Đã lưu trạng thái', 'Ứng viên có thể xem cập nhật trong trang Đơn ứng tuyển.', 'success');
      reload(); await refresh();
    } catch (err) { setSaveError(err instanceof Error ? err.message : 'Không lưu được trạng thái.'); }
    finally { setBusy(false); }
  };
  if (!candidate || error) return <DataState error={error} retry={reload} />;
  return <div className="live-page">
    <Link href="/recruiter/candidates">← Danh sách ứng viên</Link>
    <header><h1>{candidate.name}</h1><p>{candidate.email} · {candidate.targetRole}</p></header>
    <section className="live-panel"><h2>Hồ sơ & dự án</h2>
      <p>{candidate.university || 'Chưa bổ sung trường học'} · {candidate.major} · GPA {candidate.gpa}/4</p>
      <h3>{candidate.featuredProject.title || 'Chưa bổ sung dự án'}</h3><p>{candidate.featuredProject.summary}</p>
      <p>{candidate.featuredProject.techStack.join(' · ') || 'Chưa bổ sung kỹ năng'}</p>
      {candidate.featuredProject.repo && <a href={candidate.featuredProject.repo} target="_blank" rel="noreferrer">Xem repository ↗</a>}
      <p>Điểm phù hợp khi nộp: <strong>{candidate.matchScore}%</strong>. Chưa thẩm định AST, đạo văn hay chất lượng mã nguồn.</p>
      <button className="live-primary" onClick={() => download(`/applications/${id}/resume`, `${candidate.name}-cv.pdf`).catch(err => showToast('Không tải được CV', err.message, 'warning'))}>Tải CV đã ứng tuyển</button>
    </section>
    <form className="live-panel live-form" onSubmit={save}><h2>Cập nhật đơn ứng tuyển</h2>
      <label className="live-field">Trạng thái<select value={stage} onChange={e => setStage(e.target.value as ApplicationStage)}><option value="submitted">Mới ứng tuyển</option><option value="reviewing">Đang xem xét</option><option value="interview">Phỏng vấn</option><option value="offered">Đã gửi offer</option></select></label>
      {stage === 'interview' && <div className="live-grid">
        <label className="live-field">Ngày<input type="date" required value={schedule.date} onChange={e => setSchedule({ ...schedule, date: e.target.value })} /></label>
        <label className="live-field">Giờ (Việt Nam)<input type="time" required value={schedule.time} onChange={e => setSchedule({ ...schedule, time: e.target.value })} /></label>
        <label className="live-field">Địa điểm / thông tin cuộc họp<input required value={schedule.format} onChange={e => setSchedule({ ...schedule, format: e.target.value })} /></label>
        <label className="live-field">Người phỏng vấn<input value={schedule.interviewer} onChange={e => setSchedule({ ...schedule, interviewer: e.target.value })} /></label>
      </div>}
      <p className="data-notice">Lịch được lưu trong ứng dụng. Hãy gửi thông tin cuộc họp cho ứng viên qua kênh liên hệ của bạn.</p>
      {saveError && <p className="form-error" role="alert">{saveError}</p>}
      <button className="live-primary" disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu cập nhật'}</button>
    </form>
  </div>;
}
