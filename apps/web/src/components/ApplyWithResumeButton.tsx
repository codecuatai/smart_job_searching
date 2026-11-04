'use client';

import { ChangeEvent, ReactNode, useRef, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, FileText, Upload, X } from 'lucide-react';
import { Job } from '@/types';
import { useAuth } from '@/context/AuthContext';
import { useResume } from '@/context/ResumeContext';
import { useToast } from '@/context/ToastContext';

interface ApplyWithResumeButtonProps {
  job: Job;
  className: string;
  children: ReactNode;
}

function formatSize(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export default function ApplyWithResumeButton({ job, className, children }: ApplyWithResumeButtonProps) {
  const { resume, isLoaded, uploadResume, submitApplication } = useResume();
  const { showToast } = useToast();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setIsBusy(true);
    try {
      await uploadResume(file);
      showToast('CV đã sẵn sàng', `${file.name} sẽ được gửi kèm hồ sơ.`, 'success');
    } catch (error) {
      showToast('Không thể tải CV', error instanceof Error ? error.message : 'Vui lòng thử lại.', 'warning');
    } finally {
      setIsBusy(false);
    }
  };

  const handleSubmit = async () => {
    if (!resume) return;
    setIsBusy(true);
    try {
      await submitApplication(job, user?.name || '');
      showToast('Đã gửi hồ sơ ứng tuyển', `CV ${resume.name} đã được đính kèm cho ${job.company}.`, 'success');
      setIsOpen(false);
    } catch (error) {
      showToast('Không thể gửi hồ sơ', error instanceof Error ? error.message : 'Vui lòng thử lại.', 'warning');
    } finally {
      setIsBusy(false);
    }
  };

  return <>
    <button type="button" className={className} onClick={() => setIsOpen(true)}>{children}</button>
    {isOpen && <div className="apply-dialog-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) setIsOpen(false); }}>
      <section className="apply-dialog" role="dialog" aria-modal="true" aria-labelledby="apply-dialog-title">
        <button type="button" className="apply-dialog-close" aria-label="Đóng" onClick={() => setIsOpen(false)}><X size={19} /></button>
        <span className="apply-dialog-kicker">ỨNG TUYỂN · {job.company}</span>
        <h2 id="apply-dialog-title">Gửi CV cho vị trí này</h2>
        <p className="apply-dialog-job">{job.title}</p>

        {!isLoaded ? <p className="apply-resume-empty">Đang tải thông tin CV đã lưu…</p> : resume ? (
          <div className="apply-resume-file">
            <span className="apply-resume-file-icon"><FileText size={18} /></span>
            <span className="apply-resume-file-info"><strong>{resume.name}</strong><small>{formatSize(resume.size)} · PDF</small></span>
            <CheckCircle2 size={18} className="apply-resume-check" />
          </div>
        ) : <div className="apply-resume-empty">Bạn cần có CV PDF trước khi gửi hồ sơ. Tệp tối đa 5 MB.</div>}

        <input ref={fileInput} type="file" accept="application/pdf,.pdf" onChange={handleUpload} className="sr-only" aria-label="Chọn CV PDF" />
        <div className="apply-dialog-actions">
          <button type="button" className="apply-upload-button" disabled={!isLoaded || isBusy} onClick={() => fileInput.current?.click()}>
            <Upload size={15} /> {resume ? 'Chọn CV khác' : 'Tải CV PDF lên'}
          </button>
          {resume && <button type="button" className="apply-submit-button" disabled={!isLoaded || isBusy} onClick={handleSubmit}>
            {isBusy ? 'Đang gửi…' : <>Gửi CV ứng tuyển <ArrowRight size={16} /></>}
          </button>}
        </div>
        <p className="apply-dialog-note">CV được lưu trên máy chủ. Đơn ứng tuyển giữ nguyên bản CV tại thời điểm gửi.</p>
        {resume && <Link href="/student/applications" onClick={() => setIsOpen(false)} className="apply-history-link">Xem lịch sử ứng tuyển</Link>}
      </section>
    </div>}
  </>;
}
