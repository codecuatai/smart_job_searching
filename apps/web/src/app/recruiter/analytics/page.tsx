'use client';

import { BarChart3, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { useResource } from '@/lib/useResource';
import { MarketStatItem, CategoryDistribution, SalaryStatItem, HiringFunnelItem } from '@/types';
import DataState from '@/components/DataState';

interface Analytics {
  marketStats: MarketStatItem[]; categoryDistribution: CategoryDistribution[]; salaryStats: SalaryStatItem[];
  hiringFunnel: HiringFunnelItem[]; totalApplications: number; totalJobs: number; totalStudents: number;
  dataset: string; scope: string; updatedAt: string; biUrl?: string;
  salaryTrends: {month: string;currency: string;period: string;median: number;sampleSize: number}[];
  salaryGroups: {category: string;currency: string;period: string;median: number;sampleSize: number}[];
  dataQuality: {salaryCoverage: number;missingPostedDate: number};
}
export default function RecruiterAnalyticsPage() {
  const [dataset, setDataset] = useState('');
  const [category, setCategory] = useState('all');
  const [location, setLocation] = useState('');
  const [source, setSource] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [funnelFrom,setFunnelFrom]=useState('');
  const [funnelTo,setFunnelTo]=useState('');
  const [currency, setCurrency] = useState('VND');
  const query = new URLSearchParams({ category, location, source, dateFrom, dateTo,funnelFrom,funnelTo, ...(dataset ? {dataset} : {}) }).toString();
  const { data, error, loading, reload } = useResource<Analytics>('/analytics?' + query);
  const warehouse = useResource<{status: string;refreshedAt?: string}>('/analytics/warehouse');
  const market = data?.marketStats || [];
  const trend = (data?.salaryTrends || []).filter(s => s.currency === currency && s.period === 'MONTH');
  const maximum = Math.max(1, ...trend.map(t => t.median));
  const largest = [...market].sort((a,b) => b.shortagePercentage-a.shortagePercentage)[0];
  return <div className="analytics-page">
    <div className="jobs-intro"><div><div className="page-eyebrow"><BarChart3 size={14} /> Phân tích thị trường</div><h1>Nhu cầu kỹ năng trong hệ thống</h1><p>Số ứng viên, nhu cầu kỹ năng, lương và hiệu quả tuyển dụng.</p></div>
      <div className="analytics-actions"><a className="analytics-refresh" href={'/api/analytics/export.csv?' + query}>Xuất CSV</a>{data?.biUrl && <a className="analytics-refresh" href={data.biUrl} target="_blank" rel="noreferrer">Mở Metabase BI ↗</a>}<button className="analytics-refresh" onClick={() => { reload(); warehouse.reload(); }}><RefreshCw size={15} /> Làm mới dữ liệu</button></div>
    </div>
    <section className="analytics-filters" aria-label="Bộ lọc BI">
      <label className="live-field">Nguồn dữ liệu<select value={dataset} onChange={e => setDataset(e.target.value)}><option value="">Mặc định ({data?.dataset || 'real'})</option><option value="real">Dữ liệu thực</option><option value="demo">Dữ liệu minh họa</option></select></label>
      <label className="live-field">Ngành<select value={category} onChange={e => setCategory(e.target.value)}><option value="all">Tất cả</option>{['backend','frontend','ai','devops','mobile'].map(c => <option key={c} value={c}>{c}</option>)}</select></label>
      <label className="live-field">Địa điểm<input value={location} onChange={e => setLocation(e.target.value)} /></label>
      <label className="live-field">Nguồn tin<select value={source} onChange={e => setSource(e.target.value)}><option value="all">Tất cả</option><option value="itviec">ITviec</option><option value="topcv">TopCV</option><option value="internal">Nội bộ</option></select></label>
      <label className="live-field">Từ ngày<input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} /></label>
      <label className="live-field">Đến ngày<input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} /></label>
    </section>
    {error && <DataState error={error} retry={reload} />}
    {loading && <p role="status">Đang cập nhật báo cáo…</p>}
    <p className="data-notice">{data?.scope} · Cập nhật {data ? new Date(data.updatedAt).toLocaleString('vi-VN') : '…'}. Kho BI: {warehouse.data?.status === 'ok' ? new Date(warehouse.data.refreshedAt || '').toLocaleString('vi-VN') : 'chưa đồng bộ'}.</p>
    <div className="analytics-summary"><div><span>Tin tuyển dụng trong mẫu</span><strong>{data?.totalJobs || 0}</strong><small>{data?.dataset}</small></div><div><span>Ứng viên duy nhất</span><strong>{data?.totalStudents || 0}</strong><small>Không cộng trùng nhiều CV/đơn</small></div><div className="analytics-insight"><span>CHẤT LƯỢNG DỮ LIỆU</span><h2>{data?.dataQuality?.salaryCoverage || 0}% có lương đọc được</h2><p>{data?.dataQuality?.missingPostedDate || 0} tin thiếu ngày đăng. Kỹ năng thiếu nhiều nhất: {largest?.skill || 'Chưa có dữ liệu'}.</p></div></div>
    <div className="analytics-grid">
      <section className="analytics-gap-panel"><div className="analytics-panel-head"><div><h2>Khoảng cách kỹ năng</h2><p>Nhu cầu tin đăng và số ứng viên có kỹ năng</p></div><div className="analytics-legend"><span><i /> Nhu cầu</span><span><i /> Nguồn cung</span></div></div>
        <div className="analytics-bars">{market.map(item => <div className="analytics-bar-row" key={item.skill}><div className="analytics-bar-title"><strong>{item.skill}</strong><span>{item.candidateCount || 0} ứng viên · {item.jobCount || 0} tin</span></div><div className="analytics-bar-track"><div className="analytics-demand" style={{width: item.demandPercentage+'%'}} /><div className="analytics-supply" style={{width: item.supplyPercentage+'%'}} /></div><div className="analytics-bar-values"><span>{item.demandPercentage}%</span><span>{item.supplyPercentage}%</span></div></div>)}</div>
      </section>
      <section className="analytics-category-panel"><h2>Cơ cấu vị trí</h2>{data?.categoryDistribution.map(item => <div className="analytics-category" key={item.category}><div><strong>{item.category}</strong><b>{item.percentage}%</b></div><div className="analytics-category-track"><span style={{width: item.percentage+'%'}} /></div><small>{item.jobCount} vị trí</small></div>)}</section>
    </div>
    <section className="analytics-category-panel"><h2>Lương trung vị theo tháng đăng tin</h2><label className="live-field">Tiền tệ biểu đồ<select value={currency} onChange={e => setCurrency(e.target.value)}><option>VND</option><option>USD</option></select></label>
      <p>Chỉ tính lương tháng có đủ hai cận, theo ngày đăng tin gốc. Không quy đổi USD/VND. {trend.length < 2 && 'Chưa đủ hai kỳ để kết luận xu hướng.'}</p>
      {trend.map(item => <div className="analytics-trend-row" key={item.month}><strong>{item.month}</strong><div className="analytics-category-track"><span style={{width: (100*item.median/maximum)+'%'}} /></div><span>{item.median.toLocaleString('vi-VN')} {currency}/tháng · {item.sampleSize} tin</span></div>)}
      {!!data?.salaryGroups.length && <details><summary>Đối soát tiền tệ và kỳ lương</summary>{data.salaryGroups.map(item => <p key={item.category+item.currency+item.period}>{item.category}: {item.median.toLocaleString('vi-VN')} {item.currency}/{item.period} · {item.sampleSize} tin</p>)}</details>}
    </section>
    <div className="analytics-filters"><label className="live-field">Cohort ứng tuyển từ ngày<input type="date" value={funnelFrom} onChange={e=>setFunnelFrom(e.target.value)}/></label><label className="live-field">Cohort ứng tuyển đến ngày<input type="date" value={funnelTo} onChange={e=>setFunnelTo(e.target.value)}/></label><p>Lọc theo ngày nộp đơn; theo dõi mọi giai đoạn đạt được sau đó. Để trống để xem toàn thời gian.</p></div>
    <div className="analytics-grid analytics-secondary-grid">
      <section className="analytics-category-panel"><h2>Xu hướng lương đăng tuyển</h2><p>Khoảng lương trung bình VND/tháng theo ngành, không trộn USD hoặc năm.</p>{data?.salaryStats.length ? data.salaryStats.map(item => <div className="analytics-category" key={item.category}><div><strong>{item.category}</strong><b>{(item.averageMinimumVnd/1_000_000).toFixed(1)}–{(item.averageMaximumVnd/1_000_000).toFixed(1)} triệu</b></div><small>{item.sampleSize} tin</small></div>) : <p>Chưa có dữ liệu lương VND/tháng đủ hai cận.</p>}</section>
      <section className="analytics-category-panel"><h2>Chuyển đổi tuyển dụng</h2><p>{data?.totalApplications || 0} hồ sơ thuộc các tin của bạn · all-time</p>{data?.totalApplications ? data.hiringFunnel.map((item,index) => <div className="analytics-category" key={item.stage}><div><strong>{item.label}</strong><b>{item.reachedPercentage}%</b></div><div className="analytics-category-track"><span style={{width: item.reachedPercentage+'%'}} /></div><small>{item.count} hồ sơ{index > 0 ? ' · '+item.conversionFromPreviousPercentage+'% so với giai đoạn trước' : ''}</small></div>) : <p>Chưa có hồ sơ để tính chuyển đổi.</p>}</section>
    </div>
    <section className="analytics-table-section"><h2>Dữ liệu chi tiết</h2><div className="analytics-table-scroll"><table><thead><tr><th>Kỹ năng</th><th>Tin yêu cầu</th><th>Ứng viên</th><th>Nhu cầu</th><th>Nguồn cung</th><th>Thiếu hụt</th></tr></thead><tbody>{market.map(item => <tr key={item.skill}><td>{item.skill}</td><td>{item.jobCount || 0}</td><td>{item.candidateCount || 0}</td><td>{item.demandPercentage}%</td><td>{item.supplyPercentage}%</td><td>{item.shortagePercentage} điểm</td></tr>)}</tbody></table></div></section>
  </div>;
}
