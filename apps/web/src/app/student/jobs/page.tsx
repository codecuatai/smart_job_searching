'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowRight, BriefcaseBusiness, MapPin, Search, SlidersHorizontal } from 'lucide-react';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import { Job } from '@/types';
import { JobCategory } from '@/types';
import ApplyWithResumeButton from '@/components/ApplyWithResumeButton';

const categories: { id: JobCategory; label: string }[] = [
  { id: 'all', label: 'Tất cả' }, { id: 'backend', label: 'Backend' },
  { id: 'ai', label: 'Data & BI' }, { id: 'frontend', label: 'Frontend' }, { id: 'devops', label: 'Cloud & DevOps' },
];

export default function StudentJobsPage() {
  const [category, updateCategory] = useState<JobCategory>('all');
  const [query, updateQuery] = useState('');
  const [page, setPage] = useState(1);
  const setCategory = (value: JobCategory) => { updateCategory(value); setPage(1); };
  const setQuery = (value: string) => { updateQuery(value); setPage(1); };
  const params = new URLSearchParams({q: query, category, page: String(page), pageSize: '20'});
  const { data, error, loading, reload } = useResource<{items: Job[]; total: number}>(`/jobs/search?${params}`);
  const allJobs = data?.items || [];
  const jobs = allJobs;

  if (!data && (loading || error)) return <DataState error={error} retry={reload} />;
  return <div className="jobs-page">
    <div className="jobs-intro"><div><div className="page-eyebrow"><BriefcaseBusiness size={14} /> Dành cho bạn</div><h1>Việc làm phù hợp năng lực</h1><p>Khám phá những cơ hội kết nối trực tiếp với kỹ năng và đồ án của bạn.</p></div><Link href="/student/profile" className="jobs-profile-link">Xem hồ sơ năng lực <ArrowRight size={16} /></Link></div>
    <div className="jobs-feature"><div><span>GỢI Ý NỔI BẬT</span><h2>Đồ án của bạn là<br />một lợi thế thực sự.</h2><p>Hệ thống đối chiếu kỹ năng và dự án bạn đã hoàn thành với yêu cầu của từng vị trí.</p><Link href="/student/skill-gap">Xem lộ trình cải thiện <ArrowRight size={16} /></Link></div><div className="jobs-feature-score"><span>Vị trí phù hợp nhất</span><strong>{Math.max(0, ...allJobs.map(job => job.matchScore))}<small>%</small></strong><div><span style={{ width: `${Math.max(0, ...allJobs.map(job => job.matchScore))}%` }} /></div><p>{allJobs[0]?.title || 'Chưa có tin tuyển dụng'}</p></div></div>
    <div className="jobs-section-heading"><div><h2>Khám phá cơ hội</h2><p>{data?.total || 0} kết quả · trang {page}</p></div><Link href="/student/mock-interview">Luyện phỏng vấn <ArrowRight size={15} /></Link></div>
    <div className="jobs-toolbar"><div className="jobs-categories" role="group" aria-label="Lọc lĩnh vực">{categories.map(item => <button key={item.id} className={category === item.id ? 'active' : ''} onClick={() => setCategory(item.id)} aria-pressed={category === item.id}>{item.label}</button>)}</div><label className="jobs-search"><Search size={17} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Tìm vị trí, công ty, kỹ năng" aria-label="Tìm việc làm" /></label></div>
    <div className="jobs-list">{jobs.length ? jobs.map(job => <article key={job.id} className="job-row"><div className="job-identity"><div className="job-logo">{job.logoText}</div><div className="job-info"><div className="job-company">{job.company}{job.isDemo && ' (Dữ liệu mẫu)'} <span>· {job.postedAt}</span></div><Link href={`/student/jobs/${job.id}`} className="job-title">{job.title}</Link><div className="job-meta"><span><MapPin size={13} /> {job.location}</span><span>{job.workType}</span><span>{job.salary}</span></div><div className="job-tags">{job.tags.slice(0, 3).map(tag => <span key={tag}>{tag}</span>)}</div></div></div><div className="job-actions"><div className="job-score"><strong>{job.matchScore}%</strong><span>phù hợp</span></div><ApplyWithResumeButton job={job} className="job-apply-button">Nộp đơn <ArrowRight size={15} /></ApplyWithResumeButton><Link href={`/student/jobs/${job.id}`}>Xem chi tiết</Link></div></article>) : <div className="jobs-empty"><SlidersHorizontal size={28} /><h3>Chưa tìm thấy vị trí phù hợp</h3><p>Thử một từ khóa hoặc lĩnh vực khác.</p><button onClick={() => { setCategory('all'); setQuery(''); }}>Xóa bộ lọc</button></div>}</div>
    {error && <DataState error={error} retry={reload} />}
    <nav className="flex items-center justify-center gap-4 py-5" aria-label="Phân trang việc làm"><button disabled={page <= 1 || loading} onClick={() => setPage(p => p-1)}>Trang trước</button><span>{page} / {Math.max(1, Math.ceil((data?.total || 0)/20))}</span><button disabled={page*20 >= (data?.total || 0) || loading} onClick={() => setPage(p => p+1)}>Trang sau</button></nav>
  </div>;
}
