'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, BriefcaseBusiness, GraduationCap } from 'lucide-react';
import { RoleType } from '@/types';
import { useToast } from '@/context/ToastContext';
import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const { register } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [role, setRole] = useState<RoleType>('student');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await register(name, email, password, role);
      showToast('Tạo tài khoản thành công', `Chào mừng ${name}!`, 'success');
      router.push(role === 'student' ? '/student/profile' : '/recruiter/post-job');
    } catch (err) { setError(err instanceof Error ? err.message : 'Không tạo được tài khoản.'); }
    finally { setBusy(false); }
  };
  return <main className="register-page"><div className="register-shell">
    <Link href="/login" className="register-back"><ArrowLeft size={16} /> Về đăng nhập</Link>
    <div className="register-heading"><span>UniTalent<span>AI</span></span><p>BẮT ĐẦU MỘT HÀNH TRÌNH MỚI</p><h1>Tạo tài khoản<br />của bạn.</h1><p>Tham gia không gian kết nối năng lực với cơ hội.</p></div>
    <form onSubmit={submit} className="register-form">
      <label>Bạn tham gia với vai trò nào?</label><div className="auth-role-grid"><button type="button" className={role === 'student' ? 'selected' : ''} onClick={() => setRole('student')} aria-pressed={role === 'student'}><GraduationCap size={22} /><strong>Ứng viên</strong><small>Tìm việc làm</small></button><button type="button" className={role === 'recruiter' ? 'selected' : ''} onClick={() => setRole('recruiter')} aria-pressed={role === 'recruiter'}><BriefcaseBusiness size={22} /><strong>Nhà tuyển dụng</strong><small>Tìm ứng viên</small></button></div>
      <label htmlFor="name">{role === 'student' ? 'Họ và tên' : 'Tên doanh nghiệp'}</label><input id="name" value={name} onChange={e => setName(e.target.value)} placeholder={role === 'student' ? 'Nguyễn Văn A' : 'Công ty của bạn'} required />
      <label htmlFor="email">Email</label><input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="name@example.com" required />
      <label htmlFor="password">Mật khẩu</label><input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Tối thiểu 8 ký tự" minLength={8} required />
      {error && <p role="alert" className="form-error">{error}</p>}
      <button className="auth-submit" type="submit" disabled={busy}>{busy ? 'Đang tạo tài khoản…' : 'Tạo tài khoản'} <ArrowRight size={18} /></button>
    </form>
  </div></main>;
}
