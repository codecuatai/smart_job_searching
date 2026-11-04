'use client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '@/lib/api';
interface AuthValue {
  user: User | null; ready: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string, role: User['role']) => Promise<User>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => { api<User>('/auth/me').then(setUser).catch(() => setUser(null)).finally(() => setReady(true)); }, []);
  const login = async (email: string, password: string) => {
    const result = await api<User>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    setUser(result); return result;
  };
  const register = async (name: string, email: string, password: string, role: User['role']) => {
    const result = await api<User>('/auth/register', { method: 'POST', body: JSON.stringify({ name, email, password, role }) });
    setUser(result); return result;
  };
  const logout = async () => { await api('/auth/logout', { method: 'POST' }); setUser(null); };
  return <AuthContext.Provider value={{ user, ready, login, register, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('AuthProvider missing');
  return context;
}
export function RoleGuard({ role, children }: { role: User['role']; children: ReactNode }) {
  const { user, ready } = useAuth(); const router = useRouter();
  useEffect(() => {
    if (!ready) return;
    if (!user) router.replace('/login');
    else if (user.role !== role) router.replace(user.role === 'student' ? '/student/jobs' : '/recruiter/candidates');
  }, [user, ready, role, router]);
  if (!ready || !user || user.role !== role) return <p className="data-state" role="status">Đang kiểm tra phiên đăng nhập…</p>;
  return <>{children}</>;
}
