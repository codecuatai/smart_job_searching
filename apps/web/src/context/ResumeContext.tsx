'use client';
import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Job, ApplicationTrackingItem } from '@/types';
import { api, download } from '@/lib/api';
import { useAuth } from './AuthContext';
export interface ResumeApplication extends ApplicationTrackingItem {
  applicantName: string; resumeName: string; size: number; submittedAt: string;
}
interface ResumeValue {
  resume: File | null; isLoaded: boolean; submissions: ResumeApplication[]; error: string;
  refresh: () => Promise<void>; uploadResume: (file: File) => Promise<void>;
  submitApplication: (job: Job, applicantName: string) => Promise<void>;
  downloadSubmittedResume: (id: string) => Promise<void>;
}
const Context = createContext<ResumeValue | null>(null);
export function ResumeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [resume, setResume] = useState<File | null>(null);
  const [submissions, setSubmissions] = useState<ResumeApplication[]>([]);
  const [isLoaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const accountGeneration = useRef(0);
  const refresh = useCallback(async () => {
    if (!user) return;
    const generation = accountGeneration.current;
    setError('');
    try {
      const applications = await api<ResumeApplication[]>('/applications');
      if (generation !== accountGeneration.current) return;
      setSubmissions(applications);
      if (user.role === 'student') {
        const info = await api<{ id: string; name: string } | null>('/resumes/current');
        if (generation !== accountGeneration.current) return;
        if (info) {
          const response = await fetch(`/api/resumes/${info.id}/download`);
          if (!response.ok) throw new Error('Không tải được CV đã lưu.');
          const content = await response.blob();
          if (generation !== accountGeneration.current) return;
          setResume(new File([content], info.name, { type: 'application/pdf' }));
        } else setResume(null);
      }
    } catch (err) { if (generation === accountGeneration.current) setError(err instanceof Error ? err.message : 'Không tải được dữ liệu CV.'); }
    finally { if (generation === accountGeneration.current) setLoaded(true); }
  }, [user]);
  useEffect(() => {
    setResume(null); setSubmissions([]); setLoaded(false); setError('');
    if (user) void refresh(); else setLoaded(true);
    return () => { accountGeneration.current += 1; };
  }, [user, refresh]);
  const uploadResume = async (file: File) => {
    // Invalidate an in-flight refresh so it cannot overwrite the newly uploaded CV
    // with the previous server snapshot after navigation.
    accountGeneration.current += 1;
    const form = new FormData(); form.append('file', file);
    const result = await api<{ textExtracted: boolean }>('/resumes', { method: 'POST', body: form });
    setResume(file);
    setLoaded(true);
    if (!result.textExtracted) setError('PDF không có lớp văn bản. Hãy bổ sung kỹ năng trong hồ sơ để ghép việc.');
  };
  const submitApplication = async (job: Job) => {
    await api('/applications', { method: 'POST', body: JSON.stringify({ jobId: job.id }) });
    await refresh();
  };
  const downloadSubmittedResume = async (id: string) => {
    await download(`/applications/${id}/resume`, submissions.find(s => s.id === id)?.resumeName || 'cv.pdf');
  };
  return <Context.Provider value={{ resume, isLoaded, submissions, error, refresh, uploadResume, submitApplication, downloadSubmittedResume }}>{children}</Context.Provider>;
}
export function useResume() {
  const value = useContext(Context);
  if (!value) throw new Error('ResumeProvider missing');
  return value;
}
