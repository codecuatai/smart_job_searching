'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, BriefcaseBusiness, GraduationCap, LockKeyhole, Mail } from 'lucide-react';
import { RoleType } from '@/types';
import { useToast } from '@/context/ToastContext';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const { login } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [role, setRole] = useState<RoleType>('student');
  const [email, setEmail] = useState('nam.nguyen@hcmut.edu.vn');
  const [password, setPassword] = useState('demo12345');
  const selectRole = (next: RoleType) => { setRole(next); setEmail(next === 'student' ? 'nam.nguyen@hcmut.edu.vn' : 'recruitment@vng.com.vn'); };
  const enter = async (next: RoleType, demo = false) => {
    setBusy(true); setError('');
    try {
      const user = await login(demo ? (next === 'student' ? 'nam.nguyen@hcmut.edu.vn' : 'recruitment@vng.com.vn') : email, demo ? 'demo12345' : password);
      showToast('Đăng nhập thành công', `Chào mừng ${user.name}!`, 'success');
      router.push(user.role === 'student' ? '/student/jobs' : '/recruiter/candidates');
    } catch (err) { setError(err instanceof Error ? err.message : 'Không thể đăng nhập.'); }
    finally { setBusy(false); }
  };

  return <main className="auth-page">
    <section className="auth-story">
      <Link href="/login" className="auth-brand"><span className="auth-mark" />UniTalent<span>AI</span></Link>
      <div className="auth-story-content">
        <span className="auth-eyebrow">NỀN TẢNG SỰ NGHIỆP CHO THẾ HỆ MỚI</span>
        <h1>Năng lực của bạn xứng đáng được nhìn thấy.</h1>
        <p>Từ dự án đã làm đến công việc phù hợp. Một không gian để ứng viên chứng minh năng lực và doanh nghiệp tìm đúng người.</p>
        <div className="auth-preview" aria-hidden="true">
          <div className="auth-preview-top"><span>GỢI Ý DÀNH CHO BẠN</span><span>01 / 04</span></div>
          <div className="auth-preview-row"><span className="auth-company-mark">V</span><span><strong>Junior Backend Engineer</strong><small>VNG Corporation · TP. Hồ Chí Minh</small></span><b>94%</b></div>
          <div className="auth-preview-progress"><span /></div>
          <p>Đồ án Microservices của bạn phù hợp với vị trí này.</p>
        </div>
      </div>
      <div className="auth-story-foot">© 2026 UniTalent AI <span>Định hướng bằng dữ liệu. Phát triển bằng năng lực.</span></div>
    </section>
    <section className="auth-panel">
      <div className="auth-panel-inner">
        <div className="auth-mobile-brand">UniTalent<span>AI</span></div>
        <div className="auth-switch"><strong>Đăng nhập</strong><Link href="/register">Tạo tài khoản <ArrowRight size={14} /></Link></div>
        <div className="auth-intro"><span>RẤT VUI ĐƯỢC GẶP LẠI BẠN</span><h2>Tiếp tục hành trình<br />của bạn.</h2><p>Chọn không gian làm việc để bắt đầu.</p></div>
        <div className="auth-role-grid">
          <button type="button" className={role === 'student' ? 'selected' : ''} onClick={() => selectRole('student')} aria-pressed={role === 'student'}><GraduationCap size={23} /><strong>Ứng viên</strong><small>Tìm cơ hội phù hợp</small></button>
          <button type="button" className={role === 'recruiter' ? 'selected' : ''} onClick={() => selectRole('recruiter')} aria-pressed={role === 'recruiter'}><BriefcaseBusiness size={23} /><strong>Nhà tuyển dụng</strong><small>Khám phá ứng viên</small></button>
        </div>
        <form onSubmit={e => { e.preventDefault(); enter(role); }} className="auth-form">
          <label htmlFor="email">Email</label><div className="auth-field"><Mail size={17} /><input id="email" type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <label htmlFor="password">Mật khẩu</label><div className="auth-field"><LockKeyhole size={17} /><input id="password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required /></div>
          {error && <p role="alert" className="form-error">{error}</p>}
          <button className="auth-submit" type="submit" disabled={busy}>{busy ? 'Đang đăng nhập…' : 'Vào không gian làm việc'} <ArrowRight size={18} /></button>
        </form>
        <div className="auth-demo"><span>TÀI KHOẢN DEMO · demo12345</span><div><button disabled={busy} onClick={() => enter('student', true)}>Đăng nhập ứng viên ↗</button><button disabled={busy} onClick={() => enter('recruiter', true)}>Đăng nhập tuyển dụng ↗</button></div></div>
      </div>
    </section>
  </main>;
}
