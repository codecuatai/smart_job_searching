'use client';

import { ChangeEvent, useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, Upload } from 'lucide-react';
import { useResume } from '@/context/ResumeContext';
import { useToast } from '@/context/ToastContext';
import { api } from '@/lib/api';

function formatSize(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export default function ResumeManager() {
  const { resume, resumeId, analysis, isLoaded, uploadResume, updateAnalysis, error, refresh } = useResume();
  const { showToast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [skillsDraft, setSkillsDraft] = useState('');
  const [yearsDraft, setYearsDraft] = useState('');
  useEffect(() => {
    setSkillsDraft(analysis?.skills.map(s => s.name).join(', ') || '');
    setYearsDraft(analysis?.experienceYears == null ? '' : String(analysis.experienceYears));
    setAnalysisError('');
  }, [analysis]);
  const analyze = async () => {
    setAnalyzing(true); setAnalysisError('');
    try { await api(`/resumes/${resumeId}/analyze`, { method: 'POST' }); await refresh(); }
    catch (err) { setAnalysisError(err instanceof Error ? err.message : 'Không phân tích được CV.'); }
    finally { setAnalyzing(false); }
  };
  const confirm = async () => {
    setConfirming(true); setAnalysisError('');
    try {
      const result = await api<{ analysis: NonNullable<typeof analysis> }>(`/resumes/${resumeId}/analysis`, { method: 'PATCH', body: JSON.stringify({ skills: skillsDraft.split(',').map(s => s.trim()).filter(Boolean), experienceYears: yearsDraft === '' ? null : Number(yearsDraft) }) });
      if (result.analysis) updateAnalysis(result.analysis);
      showToast('Đã xác nhận phân tích CV', 'Kết quả matching sẽ ưu tiên nội dung CV và các kỹ năng bạn vừa xác nhận.', 'success');
    } catch (err) { setAnalysisError(err instanceof Error ? err.message : 'Không lưu được phân tích.'); }
    finally { setConfirming(false); }
  };

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
        <button type="button" className="resume-upload-button" disabled={!isLoaded || uploading || analyzing} onClick={() => inputRef.current?.click()}>
          <Upload size={15} /> {uploading ? 'Đang lưu CV…' : resume ? 'Thay CV' : 'Tải CV lên'}
        </button>
        <span>Lưu theo tài khoản trên máy chủ</span>
      </div>
      {resume && analysis && <div className="cv-analysis-panel" aria-labelledby="cv-analysis-title">
        <h3 id="cv-analysis-title">Phân tích CV</h3>
        <p>{analysis.method.startsWith('gemini:') ? `Phân tích bởi ${analysis.method.replace('gemini:', '')}` : 'Kỹ năng nhận diện sơ bộ từ văn bản. Chọn phân tích AI để xem thông tin có bằng chứng.'} · {analysis.confirmed ? 'Đã xác nhận bởi bạn' : 'Chờ bạn kiểm tra/xác nhận'}</p>
        {analysis.status === 'needs-ocr' && <p>CV chưa có lớp chữ. Phân tích AI sẽ thử OCR tối đa 3 trang đầu.</p>}
        {analysis.ocrUsed && <p>Đã nhận diện chữ bằng OCR{analysis.ocrPartial ? ' ở 3 trang đầu; các trang sau chưa được phân tích' : ''}.</p>}
        <button type="button" className="resume-upload-button" disabled={analyzing || uploading} onClick={analyze}>{analyzing ? 'Đang xử lý phân tích…' : 'Phân tích CV bằng AI'}</button>
        {analysisError && <p className="form-error" role="alert">{analysisError}</p>}
        <div className="cv-skill-evidence">{analysis.skills.length ? analysis.skills.map(skill => <details key={skill.name}><summary>{skill.name}</summary><p>{skill.evidence || 'Kỹ năng do bạn bổ sung; chưa có trích dẫn tự động trong CV.'}</p></details>) : <p>Chưa nhận diện được kỹ năng. Bạn có thể bổ sung bên dưới.</p>}</div>
        <label className="live-field">Kỹ năng xác nhận từ CV<input value={skillsDraft} onChange={e => setSkillsDraft(e.target.value)} placeholder="Python, SQL, Docker" disabled={analyzing} /></label>
        <label className="live-field">Số năm kinh nghiệm (để trống nếu chưa rõ)<input type="number" min="0" max="60" step="0.5" value={yearsDraft} onChange={e => setYearsDraft(e.target.value)} disabled={analyzing} /></label>
        {!!analysis.education?.length && <p>Học vấn: {analysis.education.join(' · ')}</p>}
        {!!analysis.projects?.length && <p>Dự án: {analysis.projects.join(' · ')}</p>}
        {!!analysis.unknown?.length && <p>Cần làm rõ: {analysis.unknown.join(' · ')}</p>}
        <button type="button" className="resume-upload-button" onClick={() => void confirm()} disabled={analyzing || confirming || uploading}>{confirming ? 'Đang lưu xác nhận…' : 'Xác nhận phân tích CV'}</button>
      </div>}
    </section>
  );
}
