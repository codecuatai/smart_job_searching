import React from 'react';
import Navbar from '@/components/Navbar';
import { RoleGuard } from '@/context/AuthContext';

export default function RecruiterLayout({ children }: { children: React.ReactNode }) {
  return <RoleGuard role="recruiter"><div className="workspace-shell"><Navbar currentRole="recruiter" /><main className="workspace-sheet">{children}</main></div></RoleGuard>;
}
