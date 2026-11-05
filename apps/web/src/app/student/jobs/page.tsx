'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, MapPin, Search, SlidersHorizontal } from 'lucide-react';
import { useResource } from '@/lib/useResource';
import { useResume } from '@/context/ResumeContext';
import DataState from '@/components/DataState';
import { Job, JobCategory } from '@/types';
import ApplyWithResumeButton from '@/components/ApplyWithResumeButton';
import { PageHeader, ScoreSummary } from '@/components/WorkspaceUI';
import { jobDate, jobLocation, jobSalary } from '@/lib/jobPresentation';

const categories: { id: JobCategory; label: string }[] = [
  {id:'all',label:'Tất cả'}, {id:'backend',label:'Backend'}, {id:'ai',label:'Data & BI'},
  {id:'frontend',label:'Frontend'}, {id:'devops',label:'Cloud & DevOps'}, {id:'mobile',label:'Mobile'},
];

export default function StudentJobsPage() {
  const [category, setCategory] = useState<JobCategory>('all');
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [page, setPage] = useState(1);
  const [location, setLocation] = useState('');
  const [workType, setWorkType] = useState('all');
  const [minScore, setMinScore] = useState('0');
  const [initialized, setInitialized] = useState(false);
  const {resume, analysis} = useResume();
  useEffect(() => {
    const search = new URLSearchParams(window.location.search);
    setQuery(search.get('q') || ''); setDebounced(search.get('q') || '');
    const chosen = search.get('category');
    if (categories.some(c => c.id === chosen)) setCategory(chosen as JobCategory);
    setLocation(search.get('location') || '');
    const type = search.get('workType') || 'all';
    if (['all','Full-time','Part-time','Internship'].includes(type)) setWorkType(type);
    const score = search.get('minScore') || '0';
    if (['0','50','70','80'].includes(score)) setMinScore(score);
    const savedPage = Number(search.get('page') || 1);
    if (Number.isInteger(savedPage) && savedPage > 0) setPage(savedPage);
    setInitialized(true);
  }, []);
  useEffect(() => { const timer = setTimeout(() => { setDebounced(query); }, 300); return () => clearTimeout(timer); }, [query]);
  useEffect(() => {
    if (!initialized) return;
    const search = new URLSearchParams();
    if (debounced) search.set('q', debounced);
    if (category !== 'all') search.set('category', category);
    if (location) search.set('location', location);
    if (workType !== 'all') search.set('workType', workType);
    if (minScore !== '0') search.set('minScore', minScore);
    if (page > 1) search.set('page', String(page));
    window.history.replaceState(null, '', `${window.location.pathname}${search.size ? `?${search}` : ''}`);
  }, [initialized,debounced,category,location,workType,minScore,page]);
  const params = new URLSearchParams({q:debounced,category,location,workType,minScore,page:String(page),pageSize:'20'});
  const {data,error,loading,reload} = useResource<{items:Job[];total:number}>(`/jobs/search?${params}`);
  const jobs = data?.items || [];
  const clear = () => {setQuery('');setCategory('all');setLocation('');setWorkType('all');setMinScore('0');setPage(1);};
  return <div className="jobs-page jobs-page-v2">
    <PageHeader title="Việc làm dành cho bạn" description="Đối chiếu bằng chứng CV với yêu cầu của từng vị trí." action={<Link href="/student/profile">Quản lý CV <ArrowRight size={16}/></Link>}/>
    <div className="cv-status-strip"><span>{resume ? `${resume.name} · ${analysis?.confirmed ? 'Đã xác nhận kỹ năng' : 'Chờ kiểm tra kỹ năng'}` : 'Chưa có CV. Điểm hiện tại chỉ là gợi ý sơ bộ.'}</span><Link href="/student/profile">{resume?'Xem phân tích':'Tải CV lên'}</Link></div>
    <div className="jobs-toolbar"><label className="jobs-search"><Search size={18}/><input value={query} onChange={e=>{setQuery(e.target.value);setPage(1);}} placeholder="Vị trí, công ty hoặc kỹ năng" aria-label="Tìm việc làm"/></label>
      <details className="jobs-advanced"><summary><SlidersHorizontal size={16}/> Bộ lọc nâng cao</summary><div className="live-grid">
        <label className="live-field">Địa điểm<select value={location} onChange={e=>{setLocation(e.target.value);setPage(1);}}><option value="">Tất cả địa điểm</option><option>Hà Nội</option><option>Hồ Chí Minh</option><option>Đà Nẵng</option><option>Remote</option></select></label>
        <label className="live-field">Hình thức<select value={workType} onChange={e=>{setWorkType(e.target.value);setPage(1);}}><option value="all">Tất cả hình thức</option>{['Full-time','Part-time','Internship'].map(t=><option key={t}>{t}</option>)}</select></label>
        <label className="live-field">Điểm tối thiểu<select value={minScore} onChange={e=>{setMinScore(e.target.value);setPage(1);}}><option value="0">Mọi mức điểm</option><option value="50">Từ 50/100</option><option value="70">Từ 70/100</option><option value="80">Từ 80/100</option></select></label>
      </div></details></div>
    <div className="jobs-categories" role="group" aria-label="Lọc lĩnh vực">{categories.map(item=><button key={item.id} className={category===item.id?'active':''} onClick={()=>{setCategory(item.id);setPage(1);}} aria-pressed={category===item.id}>{item.label}</button>)}</div>
    <div className="jobs-results-heading"><h2>Khám phá cơ hội</h2><span aria-live="polite">{data?.total??'…'} kết quả · trang {page}{loading&&' · Đang cập nhật…'}</span></div>
    {error&&<DataState error={error} retry={reload}/>}{!data&&loading&&<p className="data-state" role="status">Đang đối chiếu CV với các vị trí…</p>}
    <div className="jobs-list">{jobs.map(job=><article key={job.id} className="job-row">
      <div className="job-identity"><div className="job-logo" aria-hidden="true">{job.logoText}</div><div className="job-info"><div className="job-company">{job.company}{job.isDemo&&' (Dữ liệu mẫu)'} <span>· {jobDate(job.postedAt)}</span></div><Link href={`/student/jobs/${job.id}`} className="job-title">{job.title}</Link><div className="job-meta"><span><MapPin size={14}/> {jobLocation(job.location)}</span><span>{job.workType}</span><span>{jobSalary(job.salary)}</span></div><div className="job-tags">{job.tags.slice(0,4).map(tag=><span key={tag}>{tag}</span>)}</div><p className="job-match-note">{job.scoreStatus==='insufficient-cv'?'Cần bổ sung CV để đánh giá đầy đủ':`${job.matchedSkills?.length||0} kỹ năng khớp · ${job.missingSkills?.length||0} cần bổ sung`}</p></div></div>
      <div className="job-actions"><ScoreSummary score={job.matchScore} provisional={job.scoreStatus==='insufficient-cv'}/><ApplyWithResumeButton job={job} className="job-apply-button">Nộp đơn <ArrowRight size={15}/></ApplyWithResumeButton><Link href={`/student/jobs/${job.id}`}>Xem chi tiết</Link></div>
    </article>)}{data&&!loading&&!jobs.length&&<div className="jobs-empty"><SlidersHorizontal size={28}/><h3>Chưa tìm thấy vị trí phù hợp</h3><p>Thử một từ khóa hoặc lĩnh vực khác.</p><button onClick={clear}>Xóa bộ lọc</button></div>}</div>
    <nav className="list-pagination" aria-label="Phân trang việc làm"><button disabled={page<=1||loading} onClick={()=>setPage(p=>p-1)}>Trang trước</button><span>{page} / {Math.max(1,Math.ceil((data?.total||0)/20))}</span><button disabled={page*20>=(data?.total||0)||loading} onClick={()=>setPage(p=>p+1)}>Trang sau</button></nav>
  </div>;
}
