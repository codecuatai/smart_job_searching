'use client';
import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { Job, ApplicationTrackingItem } from '@/types';
import { api, download } from '@/lib/api';
import { useAuth } from './AuthContext';
export interface ResumeApplication extends ApplicationTrackingItem {
  applicantName: string; applicantAvatarUrl?: string; resumeName: string; size: number; submittedAt: string;
}
export interface ResumeAnalysis {
  method: string; status: string; confirmed: boolean; skills: {name: string; evidence: string}[];
  experienceYears?: number | null; education?: string[]; projects?: string[]; unknown?: string[];
  ocrUsed?: boolean; ocrPartial?: boolean;
}
interface ResumeValue {
  resume: File | null; isLoaded: boolean; submissions: ResumeApplication[]; error: string;
  refresh: () => Promise<void>; uploadResume: (file: File) => Promise<void>;
  updateAnalysis: (analysis: ResumeAnalysis) => void;
  submitApplication: (job: Job, applicantName: string) => Promise<void>;
  downloadSubmittedResume: (id: string) => Promise<void>;
  resumeId: string; analysis: ResumeAnalysis | null;
}
const Context = createContext<ResumeValue | null>(null);
export function ResumeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [resume, setResume] = useState<File | null>(null);
  const [submissions, setSubmissions] = useState<ResumeApplication[]>([]);
  const [isLoaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [resumeId, setResumeId] = useState('');
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
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
        const info = await api<{ id: string; name: string; analysis: ResumeAnalysis | null } | null>('/resumes/current');
        if (generation !== accountGeneration.current) return;
        if (info) {
          const response = await fetch(`/api/resumes/${info.id}/download`);
          if (!response.ok) throw new Error('Không tải được CV đã lưu.');
          const content = await response.blob();
          if (generation !== accountGeneration.current) return;
          setResume(new File([content], info.name, { type: 'application/pdf' }));
          setResumeId(info.id); setAnalysis(info.analysis);
        } else { setResume(null); setResumeId(''); setAnalysis(null); }
      }
    } catch (err) { if (generation === accountGeneration.current) setError(err instanceof Error ? err.message : 'Không tải được dữ liệu CV.'); }
    finally { if (generation === accountGeneration.current) setLoaded(true); }
  }, [user]);
  useEffect(() => {
    setResume(null); setResumeId(''); setAnalysis(null); setSubmissions([]); setLoaded(false); setError('');
    if (user) void refresh(); else setLoaded(true);
    return () => { accountGeneration.current += 1; };
  }, [user, refresh]);
  const uploadResume = async (file: File) => {
    // Invalidate an in-flight refresh so it cannot overwrite the newly uploaded CV
    // with the previous server snapshot after navigation.
    accountGeneration.current += 1;
    const generation = accountGeneration.current;
    setError('');
    const form = new FormData(); form.append('file', file);
    try {
      const result = await api<{ id: string; analysis: ResumeAnalysis; textExtracted: boolean; warning?: string }>('/resumes', { method: 'POST', body: form });
      if (generation !== accountGeneration.current) return;
      setResume(file);
      setResumeId(result.id); setAnalysis(result.analysis);
      setLoaded(true);
      setError(result.warning || (!result.textExtracted ? 'CV đã lưu nhưng PDF không có lớp văn bản. Hãy bổ sung kỹ năng trong hồ sơ để ghép việc.' : ''));
    } catch (err) {
      if (generation === accountGeneration.current) {
        setError(err instanceof Error ? err.message : 'Không thể tải CV. Vui lòng thử lại.');
        setLoaded(true);
      }
      throw err;
    }
  };
  const submitApplication = async (job: Job) => {
    await api('/applications', { method: 'POST', body: JSON.stringify({ jobId: job.id }) });
    await refresh();
  };
  const downloadSubmittedResume = async (id: string) => {
    await download(`/applications/${id}/resume`, submissions.find(s => s.id === id)?.resumeName || 'cv.pdf');
  };
  const updateAnalysis = useCallback((next: ResumeAnalysis) => setAnalysis(next), []);
  return <Context.Provider value={{ resume, resumeId, analysis, isLoaded, submissions, error, refresh, uploadResume, updateAnalysis, submitApplication, downloadSubmittedResume }}>{children}</Context.Provider>;
}
export function useResume() {
  const value = useContext(Context);
  if (!value) throw new Error('ResumeProvider missing');
  return value;
}
