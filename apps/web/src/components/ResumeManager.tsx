'use client';

import { ChangeEvent, useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, Upload } from 'lucide-react';
import { useResume } from '@/context/ResumeContext';
import { useToast } from '@/context/ToastContext';

function formatSize(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export default function ResumeManager() {
  const { resume, isLoaded, uploadResume, error, refresh } = useResume();
  const { showToast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!resume) {
      setPreviewUrl('');
      return;
    }
    const url = URL.createObjectURL(resume);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [resume]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setUploading(true);
    try {
      await uploadResume(file);
      showToast('CV đã được lưu', `${file.name} sẽ được đính kèm khi bạn ứng tuyển.`, 'success');
    } catch (error) {
      showToast('Không thể tải CV', error instanceof Error ? error.message : 'Vui lòng thử lại.', 'warning');
    } finally {
      setUploading(false);
    }
  };

  return (
    <section className="resume-card" aria-labelledby="resume-heading">
      <div className="resume-card-heading">
        <div className="resume-card-icon"><FileText size={19} /></div>
        <div>
          <h2 id="resume-heading">CV ứng tuyển</h2>
          <p>Tải CV PDF lên để đính kèm khi nộp hồ sơ.</p>
        </div>
      </div>

      {error && <div role="alert" className="form-error">{error} <button type="button" onClick={() => void refresh()}>Thử lại</button></div>}
      {!isLoaded ? (
        <p className="resume-empty">Đang kiểm tra CV đã lưu…</p>
      ) : resume ? (
        <div className="resume-file-row">
          <div className="resume-file-icon"><FileText size={18} /></div>
          <div className="resume-file-info">
            <strong title={resume.name}>{resume.name}</strong>
            <span>{formatSize(resume.size)} · PDF</span>
          </div>
          <span className="resume-ready"><CheckCircle2 size={15} /> Sẵn sàng</span>
          {previewUrl && <a href={previewUrl} target="_blank" rel="noreferrer" className="resume-view-link">Xem</a>}
        </div>
      ) : (
        <div className="resume-empty"><AlertCircle size={17} /><span>Chưa có CV. Chọn một tệp PDF tối đa 5 MB.</span></div>
      )}

      <div className="resume-card-footer">
        <input ref={inputRef} type="file" accept="application/pdf,.pdf" onChange={handleFileChange} className="sr-only" aria-label="Chọn CV dạng PDF" />
        <button type="button" className="resume-upload-button" disabled={!isLoaded || uploading} onClick={() => inputRef.current?.click()}>
          <Upload size={15} /> {uploading ? 'Đang lưu CV…' : resume ? 'Thay CV' : 'Tải CV lên'}
        </button>
        <span>Lưu theo tài khoản trên máy chủ</span>
      </div>
    </section>
  );
}
