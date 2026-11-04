'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, Banknote, BriefcaseBusiness, Check, ChevronDown, Clock3, Eye, FileText, MapPin, Plus, ShieldCheck } from 'lucide-react';
import { useToast } from '@/context/ToastContext';
import { api } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function RecruiterPostJobPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();
  const [title, setTitle] = useState('Cloud Platform Engineer');
  const [category, setCategory] = useState('devops');
  const [workType, setWorkType] = useState('Full-time');
  const [experience, setExperience] = useState('Sinh viên / 0–2 năm');
  const [salary, setSalary] = useState('15.000.000 – 22.000.000 VNĐ');
  const [location, setLocation] = useState('TP. Hồ Chí Minh');
  const [astThreshold, setAstThreshold] = useState(85);
  const [projectSubNote, setProjectSubNote] = useState('Chấp nhận đồ án CI/CD và Kubernetes thay cho 1,5 năm kinh nghiệm');
  const [requirements, setRequirements] = useState('Docker, Kubernetes, Linux, Terraform\nCI/CD với GitHub Actions\nTư duy giải quyết vấn đề và làm việc nhóm');
  const [description, setDescription] = useState('Cùng đội ngũ xây dựng nền tảng cloud ổn định, tự động hóa quy trình triển khai và cải thiện khả năng quan sát hệ thống.');
  const [mustHave,setMustHave]=useState('');
  const [niceToHave,setNiceToHave]=useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      await api('/jobs', { method: 'POST', body: JSON.stringify({ title, category, workType, salary, location, description, requirements: requirements.split('\n').filter(s => s.trim()), tags: requirements.split(/[,\n]/).map(s => s.trim()).filter(Boolean), mustHaveSkills:mustHave.split(',').map(s=>s.trim()).filter(Boolean),niceToHaveSkills:niceToHave.split(',').map(s=>s.trim()).filter(Boolean),minimumExperienceYears: experience.startsWith('2')?2:experience.startsWith('Trên')?4:0, astThreshold, projectSubstituteNote: projectSubNote }) });
      showToast('Đã đăng tin tuyển dụng', `Vị trí ${title} đã lưu trên máy chủ.`, 'success');
      router.push('/recruiter/candidates');
    } catch (err) { setError(err instanceof Error ? err.message : 'Không đăng được tin.'); }
    finally { setBusy(false); }
  };
  const categoryLabels: Record<string, string> = { backend: 'Backend Engineering', ai: 'Data & BI Platform', frontend: 'Frontend / Fullstack', devops: 'Cloud / SRE / DevOps' };

  return <div className="job-composer">
    <Link href="/recruiter/candidates" className="job-composer-back"><ArrowLeft size={15} /> Quay lại danh sách ứng viên</Link>
    <header className="job-composer-heading"><div><div className="recruiter-eyebrow"><BriefcaseBusiness size={14} /> Tạo tin mới</div><h1>Tạo tin tuyển dụng</h1><p>Mô tả rõ vị trí để ứng viên phù hợp dễ dàng tìm thấy bạn.</p></div><span className="job-composer-step"><span>01</span> Thông tin vị trí <i /><span>02</span> Tiêu chí ứng viên</span></header>
    <div className="job-composer-layout">
      <form className="job-composer-form" onSubmit={handleSubmit}>
        <section className="job-form-section"><div className="job-section-heading"><span className="job-section-number">01</span><div><h2>Thông tin vị trí</h2><p>Những thông tin ứng viên nhìn thấy đầu tiên.</p></div></div>
          <div className="job-form-grid">
            <label className="job-field job-field-wide"><span>Tên vị trí <b>*</b></span><input type="text" value={title} onChange={event => setTitle(event.target.value)} placeholder="Ví dụ: Junior Backend Engineer" required /><small>Viết ngắn gọn, nêu rõ cấp bậc hoặc chuyên môn.</small></label>
            <label className="job-field"><span>Nhóm ngành <b>*</b></span><span className="job-select-wrap"><select value={category} onChange={event => setCategory(event.target.value)}><option value="backend">Backend Engineering</option><option value="ai">Data & BI Platform</option><option value="frontend">Frontend / Fullstack</option><option value="devops">Cloud / SRE / DevOps</option></select><ChevronDown size={15} /></span></label>
            <label className="job-field"><span>Hình thức làm việc <b>*</b></span><span className="job-select-wrap"><select value={workType} onChange={event => setWorkType(event.target.value)}><option>Full-time</option><option>Internship</option><option>Part-time</option></select><ChevronDown size={15} /></span></label>
            <label className="job-field"><span>Mức kinh nghiệm</span><span className="job-select-wrap"><select value={experience} onChange={event => setExperience(event.target.value)}><option>Sinh viên / 0–2 năm</option><option>2–4 năm</option><option>Trên 4 năm</option></select><ChevronDown size={15} /></span></label>
            <label className="job-field"><span>Địa điểm làm việc <b>*</b></span><span className="job-input-icon"><MapPin size={15} /><input type="text" value={location} onChange={event => setLocation(event.target.value)} placeholder="Thành phố hoặc khu vực" required /></span></label>
            <label className="job-field"><span>Mức lương</span><span className="job-input-icon"><Banknote size={15} /><input type="text" value={salary} onChange={event => setSalary(event.target.value)} placeholder="Ví dụ: 15–20 triệu VNĐ" /></span></label>
            <label className="job-field job-field-wide"><span>Mô tả công việc <b>*</b></span><textarea rows={4} value={description} onChange={event => setDescription(event.target.value)} placeholder="Bạn sẽ làm gì trong vai trò này?" required /><small>Nêu nhiệm vụ chính, đội ngũ và điều ứng viên sẽ học được.</small></label>
          </div>
        </section>
        <section className="job-form-section"><div className="job-section-heading"><span className="job-section-number">02</span><div><h2>Tiêu chí ứng viên</h2><p>Cho biết năng lực nào quan trọng nhất với vị trí này.</p></div></div>
          <div className="job-form-grid"><label className="job-field"><span>Kỹ năng bắt buộc</span><input value={mustHave} onChange={e=>setMustHave(e.target.value)} placeholder="Python, SQL" maxLength={1000}/><small>Phân tách bằng dấu phẩy; để trống nếu chưa phân loại.</small></label><label className="job-field"><span>Kỹ năng ưu tiên</span><input value={niceToHave} onChange={e=>setNiceToHave(e.target.value)} placeholder="Docker, Kubernetes" maxLength={1000}/></label></div>
          <label className="job-field"><span>Kỹ năng và yêu cầu <b>*</b></span><textarea rows={5} value={requirements} onChange={event => setRequirements(event.target.value)} placeholder={'Mỗi yêu cầu một dòng\nVí dụ: Thành thạo SQL'} required /><small>Mỗi dòng sẽ được hiển thị như một tiêu chí riêng.</small></label>
          <div className="job-ast-section"><div className="job-ast-heading"><div className="job-ast-icon"><ShieldCheck size={17} /></div><div><h3>Đánh giá mã nguồn AST</h3><p>Thêm một tiêu chí minh bạch cho hồ sơ có dự án cá nhân.</p></div><span className="job-optional-tag">Tùy chọn</span></div>
            <div className="job-form-grid job-ast-grid">
              <label className="job-field"><span>Điểm Clean Code tối thiểu <small>(0–100)</small></span><span className="job-score-input"><input type="number" min={50} max={100} value={astThreshold} onChange={event => setAstThreshold(Number(event.target.value))} /><b>/ 100</b></span><small>Gợi ý: đặt từ 80 điểm để cân bằng chất lượng và số lượng hồ sơ.</small></label>
              <label className="job-field"><span>Đồ án có thể thay thế kinh nghiệm</span><input type="text" value={projectSubNote} onChange={event => setProjectSubNote(event.target.value)} placeholder="Mô tả đồ án được chấp nhận" /><small>Giúp sinh viên hiểu rõ cách chứng minh năng lực.</small></label>
            </div>
            <div className="job-ast-rule"><Check size={14} /><span>Ngưỡng {astThreshold} được lưu để tham khảo. Chưa có dịch vụ thẩm định AST.</span></div>
          </div>
        </section>
        {error && <p role="alert" className="form-error">{error}</p>}<footer className="job-form-actions"><Link href="/recruiter/candidates">Hủy</Link><button type="submit" disabled={busy}>{busy ? 'Đang đăng…' : 'Đăng tin tuyển dụng'} <ArrowRight size={16} /></button></footer>
      </form>
      <aside className="job-preview-column"><div className="job-preview-label"><Eye size={15} /> Xem trước tin</div>
        <article className="job-live-preview"><div className="job-preview-company"><span>V</span><div><strong>{user?.name}</strong><small>Tài khoản doanh nghiệp</small></div><Check size={14} /></div>
          <div className="job-preview-status">Đang soạn tin</div><h2>{title || 'Tên vị trí tuyển dụng'}</h2><p className="job-preview-category">{categoryLabels[category]} <span>·</span> {workType}</p>
          <div className="job-preview-meta"><span><MapPin size={14} /> {location || 'Địa điểm làm việc'}</span><span><Banknote size={14} /> {salary || 'Thỏa thuận'}</span><span><Clock3 size={14} /> {experience}</span></div>
          <div className="job-preview-description"><strong>Về vị trí này</strong><p>{description || 'Mô tả công việc sẽ hiển thị tại đây.'}</p></div>
          <div className="job-preview-requirements"><strong>Kỹ năng cần có</strong>{requirements.split('\n').filter(item => item.trim()).slice(0, 4).map(item => <span key={item}><Check size={13} />{item}</span>)}</div>
          <div className="job-preview-ast"><ShieldCheck size={15} /><span>Ngưỡng AST tham khảo: {astThreshold}</span></div><div className="job-preview-footer"><FileText size={14} /> Ứng viên có thể nộp CV kèm hồ sơ năng lực</div>
        </article>
        <div className="job-preview-tip"><Plus size={15} /><p><strong>Mẹo viết tin hiệu quả</strong><br />Mô tả kỳ vọng cụ thể và nêu rõ cách bạn đánh giá hồ sơ.</p></div><p className="job-preview-demo"><ShieldCheck size={13} /> Tin sẽ được lưu và hiển thị cho ứng viên sau khi đăng.</p>
      </aside>
    </div>
  </div>;
}
