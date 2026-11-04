'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { ArrowUpRight, BarChart3, BriefcaseBusiness, ChevronDown, Code2, FileText, GraduationCap, LogOut, Menu, Mic2, Plus, SearchCheck, Users, X } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { RoleType } from '@/types';

const studentLinks = [
  { href: '/student/jobs', label: 'Khám phá việc làm', icon: BriefcaseBusiness },
  { href: '/student/profile', label: 'Hồ sơ năng lực', icon: Code2 },
  { href: '/student/applications', label: 'Đơn ứng tuyển', icon: FileText },
  { href: '/student/mock-interview', label: 'Luyện phỏng vấn', icon: Mic2 },
  { href: '/student/skill-gap', label: 'Lộ trình kỹ năng', icon: SearchCheck },
];
const recruiterLinks = [
  { href: '/recruiter/candidates', label: 'Ứng viên', icon: Users },
  { href: '/recruiter/post-job', label: 'Đăng tin tuyển dụng', icon: Plus },
  { href: '/recruiter/analytics', label: 'Phân tích thị trường', icon: BarChart3 },
];

export default function Navbar({ currentRole }: { currentRole: RoleType }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const [roleOpen, setRoleOpen] = useState(false);
  const links = currentRole === 'student' ? studentLinks : recruiterLinks;
  const active = links.find(link => pathname === link.href || pathname.startsWith(`${link.href}/`));
  const name = user?.name || '';

  const switchRole = (role: RoleType) => {
    setRoleOpen(false);
    setMenuOpen(false);
    if (role !== user?.role) { router.push('/login'); return; }
    router.push(role === 'student' ? '/student/jobs' : '/recruiter/candidates');
  };

  return (
    <>
      <header className="workspace-topbar">
        <button className="workspace-menu-button" type="button" aria-label={menuOpen ? 'Đóng menu' : 'Mở menu'} onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="workspace-topbar-title">{active?.label ?? 'Chi tiết'}</span>
        <div className="workspace-topbar-right"><span className="workspace-live-dot" /> Không gian {currentRole === 'student' ? 'ứng viên' : 'doanh nghiệp'}</div>
      </header>
      {menuOpen && <button className="workspace-scrim" aria-label="Đóng menu" onClick={() => setMenuOpen(false)} />}
      <aside className={`workspace-sidebar ${menuOpen ? 'is-open' : ''}`}>
        <Link className="workspace-brand" href={currentRole === 'student' ? '/student/jobs' : '/recruiter/candidates'} onClick={() => setMenuOpen(false)}>
          <span className="workspace-mark" aria-hidden="true"><span /><span /><span /></span>
          <span><strong>UniTalent<span className="workspace-brand-ai">AI</span></strong><small>Career workspace</small></span>
        </Link>
        <div className="workspace-side-label">Không gian làm việc</div>
        <nav className="workspace-nav" aria-label="Điều hướng chính">
          {links.map(link => {
            const Icon = link.icon;
            const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return <Link key={link.href} href={link.href} className={`workspace-nav-link ${isActive ? 'is-active' : ''}`} onClick={() => setMenuOpen(false)} aria-current={isActive ? 'page' : undefined}>
              <Icon size={18} strokeWidth={1.8} /><span>{link.label}</span>{isActive && <ArrowUpRight size={14} className="workspace-nav-arrow" />}
            </Link>;
          })}
        </nav>
        <div className="workspace-sidebar-bottom">
          <div className="workspace-role-wrap">
            <button type="button" className="workspace-role-button" onClick={() => setRoleOpen(!roleOpen)} aria-expanded={roleOpen}>
              {currentRole === 'student' ? <GraduationCap size={17} /> : <BriefcaseBusiness size={17} />}
              <span>{currentRole === 'student' ? 'Chế độ ứng viên' : 'Chế độ tuyển dụng'}</span><ChevronDown size={15} />
            </button>
            {roleOpen && <div className="workspace-role-menu">
              <button onClick={() => switchRole('student')}>Ứng viên</button>
              <button onClick={() => switchRole('recruiter')}>Nhà tuyển dụng</button>
            </div>}
          </div>
          <div className="workspace-account"><span className="workspace-avatar"><Image src={user?.avatarUrl || (currentRole === 'student' ? '/avatars/default-student.svg' : '/avatars/default-recruiter.svg')} alt={`Ảnh đại diện của ${name || 'tài khoản'}`} width={30} height={30} /></span><span><strong>{name}</strong><small>{currentRole === 'student' ? 'Ứng viên' : 'Doanh nghiệp'}</small></span><button title="Đăng xuất" aria-label="Đăng xuất" onClick={() => logout().then(() => router.push('/login')).catch(error => showToast('Không thể đăng xuất', error.message, 'warning'))}><LogOut size={17} /></button></div>
        </div>
      </aside>
    </>
  );
}
