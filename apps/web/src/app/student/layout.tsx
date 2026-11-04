import React from 'react';
import Navbar from '@/components/Navbar';
import { RoleGuard } from '@/context/AuthContext';

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return <RoleGuard role="student"><div className="workspace-shell"><Navbar currentRole="student" /><main className="workspace-sheet">{children}</main></div></RoleGuard>;
}
