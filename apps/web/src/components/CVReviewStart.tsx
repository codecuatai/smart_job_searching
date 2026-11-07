'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { CVConsultation, ResumeJobMatch, ResumeMatches, ResumeVersion, ReviewSummary } from '@/lib/cvReview';
import { PageHeader, ScoreSummary } from '@/components/WorkspaceUI';

export default function CVReviewStart({ initialJobId = '', initialResumeId = '' }: { initialJobId?: string; initialResumeId?: string }) {
  const router = useRouter();
  const [resumes, setResumes] = useState<ResumeVersion[]>([]);
  const [history, setHistory] = useState<ReviewSummary[]>([]);
  const [resumeId, setResumeId] = useState(initialResumeId);
  const [matches, setMatches] = useState<ResumeMatches | null>(null);
  const [loading, setLoading] = useState(true);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [opening, setOpening] = useState('');
  const [error, setError] = useState('');
  const [matchesError, setMatchesError] = useState('');
  const chosen = resumes.find(resume => resume.id === resumeId);

  useEffect(() => {
    let active = true;
    Promise.allSettled([api<ResumeVersion[]>('/resumes'), api<ReviewSummary[]>('/cv-consultations')]).then(([cv, cases]) => {
      if (!active) return;
      if (cv.status === 'fulfilled') {
        setResumes(cv.value);
        setResumeId(current => cv.value.some(item => item.id === current) ? current : cv.value[0]?.id || '');
      } else setError('Không tải được CV đã lưu. Hãy tải lại trang.');
      if (cases.status === 'fulfilled') setHistory(cases.value);
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!resumeId) { setMatches(null); return; }
    let active = true;
    setMatches(null); setMatchesError(''); setMatchesLoading(true);
    const query = new URLSearchParams({ limit: '12' });
    if (initialJobId) query.set('targetJobId', initialJobId);
    api<ResumeMatches>(`/resumes/${encodeURIComponent(resumeId)}/matches?${query}`).then(result => {
      if (active) setMatches(result);
    }).catch(cause => { if (active) setMatchesError((cause as Error).message); })
      .finally(() => { if (active) setMatchesLoading(false); });
    return () => { active = false; };
  }, [resumeId, initialJobId]);

  async function compare(job: ResumeJobMatch, forceNew = false) {
    if (!chosen || opening) return;
    setOpening(job.id); setError('');
    try {
      const saved = history.find(item => item.resumeId === chosen.id && item.jobId === job.id);
      if (saved && !forceNew) { router.push(`/student/cv-review/${saved.id}`); return; }
      const review = await api<CVConsultation>('/cv-consultations', {
        method: 'POST', body: JSON.stringify({ resumeId: chosen.id, jobId: job.id }),
      });
      router.push(`/student/cv-review/${review.id}`);
    } catch (cause) { setError((cause as Error).message); setOpening(''); }
  }

  function matchCard(job: ResumeJobMatch, featured = false) {
    const saved = history.find(item => item.resumeId === resumeId && item.jobId === job.id);
    return <article className={`review-match ${featured ? 'is-featured' : ''}`} key={job.id}>
      <div className="review-match-main">
        {featured && <span className="review-match-kicker">Job bạn vừa chọn</span>}
        <h3><Link href={`/student/jobs/${job.id}`}>{job.title}</Link></h3>
        <p>{job.company}{job.isDemo ? ' · Dữ liệu mẫu' : ''}{job.location ? ` · ${job.location}` : ''}</p>
        <p><strong>Nhận diện trong CV:</strong> {job.matchedSkills.length ? job.matchedSkills.join(', ') : 'Chưa có kỹ năng khớp được nhận diện'}</p>
        <p><strong>Cần kiểm tra thêm:</strong> {job.missingSkills.length ? job.missingSkills.join(', ') : 'Chưa phát hiện khoảng trống trong các kỹ năng nhận diện được'}</p>
      </div>
      <div className="review-match-actions">
        <ScoreSummary score={job.matchScore} provisional={job.scoreStatus === 'insufficient-cv'} caption="Điểm tham khảo" />
        <button type="button" className="live-primary" disabled={!!opening} onClick={() => void compare(job)}>{opening === job.id ? 'Đang mở…' : saved ? 'Mở phân tích đã lưu' : 'Xem skill gaps'}</button>
        {saved && <button type="button" disabled={!!opening} onClick={() => void compare(job, true)}>Phân tích lại</button>}
      </div>
    </article>;
  }

  const suggested = (matches?.items || []).filter(job => job.id !== matches?.target?.id);
  const savedForCv = history.filter(item => item.resumeId === resumeId);
  return <div className="live-page cv-review">
    <PageHeader title="So sánh từng CV với việc làm" description="Mỗi phiên bản CV có danh sách job và kết quả kỹ năng riêng." />
    {error && <p className="form-error" role="alert">{error}</p>}
    <section className="review-panel review-cv-picker" aria-labelledby="review-cv-heading">
      <div className="review-heading-row"><h2 id="review-cv-heading">Chọn CV đã tải lên</h2><Link href="/student/profile">Quản lý CV →</Link></div>
      {loading ? <p role="status">Đang tải CV…</p> : resumes.length ? <>
        <label className="live-field" id="cv-selection">Phiên bản CV<select value={resumeId} onChange={event => { setResumeId(event.target.value); setShowAll(false); }}>{resumes.map(resume => <option key={resume.id} value={resume.id}>{resume.name} · {new Date(resume.createdAt).toLocaleDateString('vi-VN')}</option>)}</select></label>
        {chosen && <p className="review-muted">Đang dùng nội dung của <strong>{chosen.name}</strong> để xếp hạng. {chosen.confirmed ? 'Kỹ năng đã được bạn xác nhận.' : 'Kết quả sơ bộ từ văn bản CV; bạn có thể kiểm tra kỹ năng trong Hồ sơ năng lực.'}</p>}
      </> : <p>Bạn chưa tải CV lên. <Link href="/student/profile">Tải CV tại Hồ sơ năng lực</Link> để bắt đầu.</p>}
    </section>
    <section className="review-panel" aria-labelledby="review-matches-heading">
      <div className="review-heading-row"><div><h2 id="review-matches-heading">Việc làm phù hợp với CV này</h2>{matches && <p className="review-muted">{matches.total} job có tín hiệu khớp trong {matches.evaluatedJobs} job đã đối chiếu · hiển thị tối đa 12.</p>}</div><Link href="/student/jobs">Xem tất cả việc làm →</Link></div>
      {!resumeId ? <p>Chọn một CV để xem việc làm phù hợp.</p> : matchesLoading ? <p role="status">Đang so sánh CV này với các job…</p> : matchesError ? <p role="alert" className="form-error">{matchesError}</p> : matches ? <>
        {matches.target && matchCard(matches.target, true)}
        {suggested.length ? <div className="review-matches">{suggested.slice(0, showAll ? 12 : 5).map(job => matchCard(job))}</div> : !matches.target && <p>Chưa tìm thấy job có kỹ năng khớp với CV này. Hãy kiểm tra nội dung CV hoặc <Link href="/student/jobs">xem tất cả việc làm</Link>.</p>}
        {suggested.length > 5 && <button type="button" onClick={() => setShowAll(value => !value)}>{showAll ? 'Thu gọn danh sách' : 'Xem thêm job phù hợp'}</button>}
        <p className="review-muted">Điểm chỉ phản ánh tín hiệu kỹ năng trong CV, chưa đánh giá đầy đủ cấp bậc và kinh nghiệm. Kỹ năng chưa được nhận diện cần bạn kiểm tra trước khi kết luận mình thiếu kỹ năng.</p>
      </> : null}
    </section>
    {!!savedForCv.length && <details className="review-panel"><summary>Phân tích đã lưu cho CV này ({savedForCv.length})</summary><ul className="review-history">{savedForCv.map(item => <li key={item.id}><Link href={`/student/cv-review/${item.id}`}><strong>{item.title}</strong><span>{item.company} · {item.resumeName}</span></Link></li>)}</ul></details>}
  </div>;
}
