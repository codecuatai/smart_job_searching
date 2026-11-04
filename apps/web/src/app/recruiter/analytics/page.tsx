'use client';

import { ArrowUpRight, BarChart3, RefreshCw } from 'lucide-react';
import { useResource } from '@/lib/useResource';
import { MarketStatItem, CategoryDistribution } from '@/types';
import DataState from '@/components/DataState';

export default function RecruiterAnalyticsPage() {
  const { data, error, loading, reload } = useResource<{marketStats: MarketStatItem[]; categoryDistribution: CategoryDistribution[]; scope: string; updatedAt: string}>('/analytics');
  const market = data?.marketStats || [];
  const distribution = data?.categoryDistribution || [];
  const totalJobs = distribution.reduce((sum, item) => sum + item.jobCount, 0);
  const largestGap = market.reduce((largest, item) => item.shortagePercentage > largest.shortagePercentage ? item : largest, {skill: 'Chưa có dữ liệu', shortagePercentage: 0});
  const averageGap = Math.round(market.reduce((sum, item) => sum + item.shortagePercentage, 0) / Math.max(1, market.length));

  if (loading || error) return <DataState error={error} retry={reload} />;
  return <div className="analytics-page"><p className="data-notice">{data?.scope} Cập nhật: {data && new Date(data.updatedAt).toLocaleString('vi-VN')}</p>
    <div className="jobs-intro"><div><div className="page-eyebrow"><BarChart3 size={14} /> Phân tích thị trường</div><h1>Nhu cầu kỹ năng trong hệ thống</h1><p>Khoảng cách giữa kỹ năng doanh nghiệp cần và năng lực ứng viên hiện có.</p></div><button className="analytics-refresh" onClick={reload}><RefreshCw size={15} /> Làm mới dữ liệu</button></div>
    <div className="analytics-summary"><div><span>Tin tuyển dụng trong mẫu</span><strong>{totalJobs.toLocaleString('vi-VN')}</strong><small>vị trí IT</small></div><div><span>Khoảng cách kỹ năng trung bình</span><strong>{averageGap}<small>%</small></strong><small>trên {market.length} nhóm kỹ năng</small></div><div className="analytics-insight"><span>ĐIỂM CẦN CHÚ Ý</span><h2>{largestGap.skill}</h2><p>Thiếu hụt lớn nhất: <strong>{largestGap.shortagePercentage} điểm phần trăm</strong> giữa nhu cầu tuyển dụng và năng lực hiện có.</p></div></div>
    <div className="analytics-grid"><section className="analytics-gap-panel"><div className="analytics-panel-head"><div><h2>Khoảng cách kỹ năng</h2><p>Tỷ lệ doanh nghiệp yêu cầu so với tỷ lệ ứng viên sở hữu</p></div><div className="analytics-legend"><span><i /> Nhu cầu</span><span><i /> Nguồn cung</span></div></div><div className="analytics-bars">{market.map(item => <div className="analytics-bar-row" key={item.skill}><div className="analytics-bar-title"><strong>{item.skill}</strong><span>Thiếu {item.shortagePercentage} điểm</span></div><div className="analytics-bar-track"><div className="analytics-demand" style={{ width: `${item.demandPercentage}%` }} /><div className="analytics-supply" style={{ width: `${item.supplyPercentage}%` }} /></div><div className="analytics-bar-values"><span>{item.demandPercentage}%</span><span>{item.supplyPercentage}%</span></div></div>)}</div></section><section className="analytics-category-panel"><div className="analytics-panel-head"><div><h2>Cơ cấu vị trí</h2><p>{totalJobs.toLocaleString('vi-VN')} tin tuyển dụng theo nhóm</p></div></div><div className="analytics-category-list">{distribution.map((item, index) => <div key={item.category} className="analytics-category"><div><span className="analytics-category-index">0{index + 1}</span><strong>{item.category}</strong><b>{item.percentage}%</b></div><div className="analytics-category-track"><span style={{ width: `${item.percentage}%` }} /></div><small>{item.jobCount.toLocaleString('vi-VN')} vị trí</small></div>)}</div></section></div>
    <section className="analytics-table-section"><div className="analytics-panel-head"><div><h2>Dữ liệu chi tiết</h2><p>So sánh các nhãn kỹ năng trong cơ sở dữ liệu</p></div><ArrowUpRight size={18} /></div><div className="analytics-table-scroll"><table><thead><tr><th>Kỹ năng</th><th>Doanh nghiệp cần</th><th>Ứng viên có</th><th>Thiếu hụt</th></tr></thead><tbody>{market.map(item => <tr key={item.skill}><td>{item.skill}</td><td>{item.demandPercentage}%</td><td>{item.supplyPercentage}%</td><td className="gap-value">+{item.shortagePercentage} điểm</td></tr>)}</tbody></table></div></section>
  </div>;
}
