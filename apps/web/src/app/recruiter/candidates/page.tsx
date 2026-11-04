'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight, CalendarDays, Check, ChevronDown, Download, FileText,
  Filter, Search, SlidersHorizontal, Users, X,
} from 'lucide-react';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import { useToast } from '@/context/ToastContext';
import { useResume } from '@/context/ResumeContext';
import { Candidate } from '@/types';

type RoleFilter = 'all' | 'backend' | 'data' | 'frontend' | 'devops';
type StageFilter = 'all' | Candidate['status'];

const roleMatches: Record<Exclude<RoleFilter, 'all'>, string[]> = {
  backend: ['backend', 'java', 'go'],
  data: ['data', 'analyst', 'bi'],
  frontend: ['frontend', 'react'],
  devops: ['devops', 'cloud', 'sre'],
};

const stageLabels: Record<Candidate['status'], string> = {
  submitted: 'Mới ứng tuyển', reviewing: 'Đang xem xét', interview: 'Phỏng vấn', offered: 'Đã gửi offer',
};

function candidateMatchesRole(role: string, selected: RoleFilter) {
  if (selected === 'all') return true;
  const normalized = role.toLocaleLowerCase('vi');
  return roleMatches[selected].some(keyword => normalized.includes(keyword));
}

function applicationTimestamp(date: string) {
  return new Date(date).getTime();
}

export default function RecruiterCandidatesPage() {
  const { showToast } = useToast();
  const { submissions, isLoaded, downloadSubmittedResume } = useResume();
  const { data, error, loading, reload } = useResource<Candidate[]>('/candidates');
  const allCandidates = useMemo(() => data || [], [data]);
  const [query, setQuery] = useState('');
  const [role, setRole] = useState<RoleFilter>('all');
  const [stage, setStage] = useState<StageFilter>('all');
  const [minMatch, setMinMatch] = useState('0');
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sortBy, setSortBy] = useState<'match' | 'recent'>('match');

  const candidates = useMemo(() => {
    const term = query.trim().toLocaleLowerCase('vi');
    return allCandidates
      .filter(candidate => !term || [candidate.name, candidate.university, candidate.targetRole, candidate.featuredProject.title, ...candidate.featuredProject.techStack]
        .some(value => value.toLocaleLowerCase('vi').includes(term)))
      .filter(candidate => candidateMatchesRole(candidate.targetRole, role))
      .filter(candidate => stage === 'all' || candidate.status === stage)
      .filter(candidate => candidate.matchScore >= Number(minMatch))
      .filter(candidate => !verifiedOnly || candidate.astAudit.cleanCodeScore >= 88)
      .sort((a, b) => sortBy === 'match' ? b.matchScore - a.matchScore : applicationTimestamp(b.appliedDate) - applicationTimestamp(a.appliedDate));
  }, [allCandidates, query, role, stage, minMatch, verifiedOnly, sortBy]);

  const hasFilters = Boolean(query || role !== 'all' || stage !== 'all' || minMatch !== '0' || verifiedOnly);
  const clearFilters = () => { setQuery(''); setRole('all'); setStage('all'); setMinMatch('0'); setVerifiedOnly(false); };

  if (loading || error) return <DataState error={error} retry={reload} />;
  return <div className="recruiter-candidates-page">
    <header className="recruiter-page-heading">
      <div>
        <div className="recruiter-eyebrow"><Users size={14} /> Tuyển dụng</div>
        <h1>Ứng viên</h1>
        <p>Tìm người phù hợp qua kỹ năng, dự án và kết quả đánh giá.</p>
      </div>
      <Link className="recruiter-primary-link" href="/recruiter/post-job">Đăng tin tuyển dụng <ArrowRight size={16} /></Link>
    </header>

    <section className="recruiter-stats" aria-label="Tổng quan ứng viên">
      <div><span>Tổng đơn ứng tuyển</span><strong>{allCandidates.length}</strong><small>ứng viên trong danh sách</small></div>
      <div><span>Thẩm định mã nguồn</span><strong>—</strong><small>Chưa triển khai dịch vụ AST</small></div>
      <div><span>CV trên máy chủ</span><strong>{submissions.length}</strong><small>tệp có thể tải xuống</small></div>
      <div className="recruiter-stats-note"><span>Gợi ý hôm nay</span><p>Ưu tiên hồ sơ có dự án sát với vị trí đang tuyển.</p></div>
    </section>

    {isLoaded && submissions.length > 0 && <section className="received-resumes recruiter-inbox" aria-labelledby="received-resumes-heading">
      <div className="received-resumes-heading"><div><h2 id="received-resumes-heading">CV mới nhận</h2><p>CV được đính kèm vào các đơn ứng tuyển tin của bạn</p></div><span>{submissions.length} CV</span></div>
      {submissions.map(application => <article className="received-resume-row" key={application.id}>
        <div className="received-resume-avatar">{application.applicantName.slice(0, 1)}</div>
        <div className="received-resume-main"><strong>{application.applicantName}</strong><span>{application.jobTitle} · {application.company}</span></div>
        <div className="received-resume-file"><FileText size={15} /><span>{application.resumeName}</span></div>
        <time dateTime={application.submittedAt}>{new Date(application.submittedAt).toLocaleDateString('vi-VN')}</time>
        <button type="button" onClick={() => downloadSubmittedResume(application.id).catch(error => showToast('Không thể tải CV', error instanceof Error ? error.message : 'Vui lòng thử lại.', 'warning'))}><Download size={15} /> Tải CV</button>
      </article>)}
    </section>}

    <section className="candidate-worklist" aria-labelledby="candidate-list-heading">
      <div className="candidate-worklist-heading">
        <div><div className="recruiter-eyebrow"><SlidersHorizontal size={13} /> Bộ lọc ứng viên</div><h2 id="candidate-list-heading">Danh sách ứng viên</h2><p>{candidates.length} kết quả phù hợp với bộ lọc</p></div>
        <label className="candidate-sort">Sắp xếp
          <select value={sortBy} onChange={event => setSortBy(event.target.value as 'match' | 'recent')} aria-label="Sắp xếp ứng viên">
            <option value="match">Độ phù hợp cao nhất</option><option value="recent">Ứng tuyển gần đây</option>
          </select><ChevronDown size={14} />
        </label>
      </div>

      <div className="candidate-filters">
        <label className="candidate-search"><Search size={17} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Tên, trường, kỹ năng hoặc dự án" aria-label="Tìm ứng viên" />{query && <button type="button" onClick={() => setQuery('')} aria-label="Xóa nội dung tìm kiếm"><X size={14} /></button>}</label>
        <label className="candidate-select"><span>Vị trí</span><select value={role} onChange={event => setRole(event.target.value as RoleFilter)}><option value="all">Tất cả vị trí</option><option value="backend">Backend</option><option value="data">Data & BI</option><option value="frontend">Frontend</option><option value="devops">Cloud & DevOps</option></select><ChevronDown size={14} /></label>
        <label className="candidate-select"><span>Trạng thái</span><select value={stage} onChange={event => setStage(event.target.value as StageFilter)}><option value="all">Tất cả trạng thái</option><option value="submitted">Mới ứng tuyển</option><option value="reviewing">Đang xem xét</option><option value="interview">Phỏng vấn</option><option value="offered">Đã gửi offer</option></select><ChevronDown size={14} /></label>
        <label className="candidate-select candidate-score-filter"><span>Độ phù hợp</span><select value={minMatch} onChange={event => setMinMatch(event.target.value)}><option value="0">Mọi mức điểm</option><option value="80">Từ 80%</option><option value="90">Từ 90%</option></select><ChevronDown size={14} /></label>
      </div>

      <div className="candidate-filter-footer">
        <label className={`candidate-verified-toggle ${verifiedOnly ? 'is-on' : ''}`}><input type="checkbox" disabled checked={verifiedOnly} onChange={event => setVerifiedOnly(event.target.checked)} /><span className="candidate-check"><Check size={12} /></span><span>Thẩm định AST <small>Chưa triển khai</small></span></label>
        <div className="candidate-filter-meta"><span><Filter size={13} /> {hasFilters ? 'Đang áp dụng bộ lọc' : 'Tất cả hồ sơ'}</span>{hasFilters && <button type="button" onClick={clearFilters}>Xóa bộ lọc <X size={13} /></button>}</div>
      </div>

      <div className="candidate-result-list">
        {candidates.length ? candidates.map(candidate => <article className="candidate-result" key={candidate.id}>
          <div className="candidate-result-avatar" data-candidate={candidate.id}>{candidate.avatarText}</div>
          <div className="candidate-result-main">
            <div className="candidate-result-title"><Link href={`/recruiter/candidates/${candidate.id}`}>{candidate.name}</Link><span className={`candidate-stage stage-${candidate.status}`}>{stageLabels[candidate.status]}</span></div>
            <p className="candidate-result-role">{candidate.targetRole}</p><p className="candidate-result-school">{candidate.university} <span>·</span> GPA {candidate.gpa.toFixed(2)}</p>
            <div className="candidate-result-project"><span>DỰ ÁN NỔI BẬT</span><strong>{candidate.featuredProject.title}</strong></div>
            <div className="candidate-tech-tags">{candidate.featuredProject.techStack.slice(0, 4).map(skill => <span key={skill}>{skill}</span>)}</div>
          </div>
          <div className="candidate-result-scores"><div className="candidate-match-score"><strong>{candidate.matchScore}<small>%</small></strong><span>phù hợp</span></div><div><strong>—</strong><span>AST code</span></div><div><strong>—</strong><span>phỏng vấn AI</span></div></div>
          <div className="candidate-result-actions"><Link href={`/recruiter/candidates/${candidate.id}`}>Xem hồ sơ <ArrowRight size={14} /></Link><Link href={`/recruiter/candidates/${candidate.id}`}><CalendarDays size={14} /> Lên lịch phỏng vấn</Link></div>
        </article>) : <div className="candidate-empty"><div><Search size={21} /></div><h3>Chưa có hồ sơ phù hợp</h3><p>Thử đổi từ khóa hoặc nới lỏng một vài tiêu chí lọc.</p><button type="button" onClick={clearFilters}>Xóa tất cả bộ lọc</button></div>}
      </div>
    </section>
  </div>;
}
