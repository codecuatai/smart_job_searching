'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, download } from '@/lib/api';
import { CVConsultation, ReviewData, CVOutline, gapLabels, GapStatus } from '@/lib/cvReview';
import { PageHeader, ScoreSummary } from '@/components/WorkspaceUI';

export default function ConsultationEditor({ id }: { id: string }) {
  const [record, setRecord] = useState<CVConsultation | null>(null);
  const [draft, setDraft] = useState<ReviewData | null>(null);
  const [activeTab, setActiveTab] = useState<'gaps' | 'outline' | 'bi'>('gaps');
  const [dirty, setDirty] = useState(false); const [busy, setBusy] = useState(false);
  const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const [hideContacts, setHideContacts] = useState(true);
  const [remote, setRemote] = useState<CVConsultation | null>(null);
  const path = `/cv-consultations/${id}`;
  useEffect(() => {
    let active = true;
    api<CVConsultation>(`/cv-consultations/${id}`).then(r => { if (active) { setRecord(r); setDraft(r.data); } }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [id]);
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } };
    window.addEventListener('beforeunload', guard);
    return () => window.removeEventListener('beforeunload', guard);
  }, [dirty]);
  function update(patch: Partial<ReviewData>) { setDraft(d => d && { ...d, ...patch }); setDirty(true); setNotice(''); }
  function outline(value: CVOutline) {
    update({ outline: value, userEditedOutline: true });
  }
  function receive(r: CVConsultation) { setRecord(r); setDraft(r.data); setDirty(false); setRemote(null); }
  async function compareRemote() {
    setBusy(true);
    try { setRemote(await api<CVConsultation>(path)); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function persist(): Promise<CVConsultation> {
    if (!record || !draft) throw new Error('Chưa tải được ca tư vấn.');
    if (!dirty) return record;
    const body = { revision: record.revision, selectedGapIds: draft.selectedGapIds, gapAssessments: draft.gapAssessments,
      currentOutline: draft.currentOutline,
      ...(draft.outline ? { outline: draft.outline } : {}) };
    const saved = await api<CVConsultation>(path, { method: 'PATCH', body: JSON.stringify(body) });
    receive(saved); return saved;
  }
  async function action(kind: 'save' | 'analyze' | 'export') {
    setBusy(true); setError(''); setNotice('');
    try {
      const current = await persist();
      if (kind === 'analyze') {
        const updated = await api<CVConsultation>(`${path}/analyze`, { method: 'POST', body: JSON.stringify({ revision: current.revision }) });
        receive(updated);
        setNotice('Đã tạo Outline. Hãy kiểm tra, sửa và lưu bản đề xuất.');
      } else if (kind === 'export') {
        await download(`${path}/export?hideContacts=${hideContacts}`, `tu-van-cv-${id}.md`);
        setNotice('Đã xuất báo cáo theo bản vừa lưu.');
      } else setNotice('Đã lưu thay đổi.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  if (!record || !draft) return <div className="cv-review"><h1>So sánh CV với job</h1>{error ? <p role="alert">{error}</p> : <p role="status">Đang tải bản phân tích…</p>}<Link href="/student/cv-review">Về danh sách CV</Link></div>;
  const chosen = draft.gaps.filter(g => draft.selectedGapIds.includes(g.id) && !['evidenced', 'unknown'].includes(draft.gapAssessments[g.id] || g.status));
  const snapshot = record.snapshot;
  const changeSection = (i: number, patch: Partial<CVOutline['sections'][number]>) => {
    if (draft.outline) outline({ ...draft.outline, sections: draft.outline.sections.map((s, n) => n === i ? { ...s, ...patch } : s) });
  };
  const move = (i: number, delta: number) => {
    if (!draft.outline) return;
    const sections = [...draft.outline.sections];
    [sections[i], sections[i + delta]] = [sections[i + delta], sections[i]];
    outline({ ...draft.outline, sections });
  };
  return <div className="live-page cv-review">
    <Link href={`/student/cv-review?cvId=${encodeURIComponent(snapshot.resumeId)}`}>← Job phù hợp với CV này</Link>
    <PageHeader title={snapshot.job.title} description={`${snapshot.job.company} · ${snapshot.resumeName}`} action={<ScoreSummary score={draft.matching.matchScore} caption="Điểm tham khảo" />} />
    <div className="review-status"><span>CV: {snapshot.resumeName}{snapshot.analysisConfirmed === false ? ' · trích xuất sơ bộ' : ''}</span><span>Đầu vào lưu ngày {new Date(record.createdAt).toLocaleString('vi-VN')}</span><span>Bản {record.revision}</span><span role="status">{busy ? 'Đang xử lý…' : dirty ? 'Có thay đổi chưa lưu' : 'Đã lưu'}</span></div>
    <nav className="review-tabs" aria-label="Nội dung tư vấn" role="tablist">
      <button type="button" role="tab" aria-selected={activeTab === 'gaps'} className={activeTab === 'gaps' ? 'review-tab is-active' : 'review-tab'} onClick={() => setActiveTab('gaps')}>Đối chiếu kỹ năng</button>
      <button type="button" role="tab" aria-selected={activeTab === 'outline'} className={activeTab === 'outline' ? 'review-tab is-active' : 'review-tab'} onClick={() => setActiveTab('outline')}>Outline CV</button>
      <button type="button" role="tab" aria-selected={activeTab === 'bi'} className={activeTab === 'bi' ? 'review-tab is-active' : 'review-tab'} onClick={() => setActiveTab('bi')}>BI tham khảo</button>
    </nav>
    {error && <p className="form-error" role="alert">{error}</p>}
    {error && dirty && <div className="review-panel"><p>Bản đang sửa vẫn được giữ. Nếu có xung đột phiên bản, bạn có thể xem bản mới trên máy chủ trước khi quyết định.</p><button type="button" disabled={busy} onClick={compareRemote}>So sánh bản mới trên máy chủ</button>{remote && <><p>Bản máy chủ: {remote.revision} · {new Date(remote.updatedAt).toLocaleString('vi-VN')}</p><details><summary>Nội dung đã lưu trên máy chủ</summary><pre className="review-raw">{JSON.stringify({ outline: remote.data.outline, selectedGapIds: remote.data.selectedGapIds }, null, 2)}</pre></details><div className="review-actions"><button type="button" onClick={() => { receive(remote); setError(''); }}>Bỏ bản đang sửa và dùng bản máy chủ</button><button type="button" onClick={() => { setRecord(remote); setRemote(null); setError(''); setNotice('Đã giữ bản đang sửa. Bấm Lưu thay đổi để thay thế nội dung bản máy chủ bằng bản này.'); }}>Giữ bản đang sửa để lưu thay bản máy chủ</button></div></>}</div>}
    {notice && <p className="review-notice" role="status">{notice}</p>}
    <fieldset disabled={busy}>
      <div className="review-actions"><button type="button" className="live-primary" onClick={() => action('save')} disabled={!dirty}>Lưu thay đổi</button><button type="button" onClick={() => action('export')}>Xuất báo cáo Markdown</button><label className="review-check"><input type="checkbox" checked={hideContacts} onChange={e => setHideContacts(e.target.checked)} />Ẩn email, URL và số điện thoại trong bản xuất</label></div>
      <details className="review-panel"><summary>CV và JD gốc đã lưu</summary><p className="review-muted">Thay hồ sơ hoặc tải CV mới không làm đổi đầu vào của ca này. Để phân tích lại đầu vào khác, tạo một ca tư vấn mới.</p><h3>JD</h3><pre className="review-raw">{snapshot.job.description}{'\n'}{snapshot.job.requirements.join('\n')}</pre>{snapshot.job.sourceUrl && <a href={snapshot.job.sourceUrl} target="_blank" rel="noreferrer">Mở nguồn JD</a>}<h3>Văn bản CV</h3><pre className="review-raw">{snapshot.resumeText}</pre></details>
      {activeTab === 'gaps' && <section id="review-gaps" role="tabpanel" className="review-panel review-section">
        <h2>Đối chiếu yêu cầu và bằng chứng</h2><p>{chosen.length} kỹ năng được ưu tiên cải thiện. Hãy kiểm tra từng yêu cầu so với bằng chứng trong CV.</p>
        <p className="review-muted">Không có từ khóa trong CV chưa chứng minh bạn thiếu năng lực. Yêu cầu ngoài khả năng nhận diện cần được kiểm tra thủ công.</p>
        {!draft.gaps.length && <p>Chưa nhận diện được yêu cầu có thể đối chiếu từ JD này. Không sinh thêm khoảng trống giả.</p>}
        {draft.gaps.map(g => <article className="review-gap" key={g.id}><div>
          <h3>{g.skill}</h3><p className="review-priority">{g.priority === 'must-have' ? 'Bắt buộc theo JD' : g.priority === 'nice-to-have' ? 'Ưu tiên theo JD' : 'Chưa phân loại mức bắt buộc'}</p>
          {g.status !== 'evidenced' ? <><label className="review-check"><input type="checkbox" checked={draft.selectedGapIds.includes(g.id)} onChange={e => update({ selectedGapIds: e.target.checked ? [...draft.selectedGapIds, g.id] : draft.selectedGapIds.filter(x => x !== g.id) })} />Ưu tiên cải thiện</label><label className="live-field">Đánh giá của bạn<select value={draft.gapAssessments[g.id] || g.status} onChange={e => update({ gapAssessments: { ...draft.gapAssessments, [g.id]: e.target.value as Exclude<GapStatus, 'evidenced'> } })}>{(['not-evidenced', 'self-declared', 'learning-needed', 'unknown'] as const).map(s => <option key={s} value={s}>{gapLabels[s]}</option>)}</select></label></> : <p>{gapLabels[g.status]}</p>}
        </div><div><span className="review-muted">Yêu cầu trong JD</span><blockquote>{g.jdQuote}</blockquote><span className="review-muted">Minh chứng trong CV</span>{g.cvQuote ? <blockquote>{g.cvQuote}</blockquote> : <p>Chưa có câu trích được kiểm chứng.</p>}<p>{g.action}</p></div></article>)}
      </section>}
      {activeTab === 'outline' && <section id="review-outline" role="tabpanel" className="review-panel review-section">
        <div className="review-actions"><h2>Outline CV trước và sau</h2>{!draft.outline && <button type="button" className="live-primary" onClick={() => action('analyze')}>Tạo Outline bằng AI</button>}</div>
        <p className="review-muted">Bullet minh chứng giữ nguyên câu trích từ CV. Gợi ý chỉnh sửa và việc cần học không được xem là thành tích đã đạt.</p>
        <div className="review-two"><div><label className="live-field">Bố cục hiện tại (kiểm tra và sửa, mỗi mục một dòng)<textarea rows={7} value={draft.currentOutline.join('\n')} onChange={e => update({ currentOutline: e.target.value.split('\n') })} onBlur={() => update({ currentOutline: draft.currentOutline.map(s => s.trim()).filter(Boolean) })} /></label>{!draft.currentOutline.length && <p className="review-muted">Chưa nhận diện được tiêu đề section. Hãy nhập thứ tự thực tế từ CV.</p>}</div><div>
          {!draft.outline ? <p>Chưa có Outline đề xuất. Tạo bằng AI sau khi kiểm tra phần đối chiếu.</p> : <><p className="review-muted">Nguồn: {draft.outlineMethod?.replace('gemini:', '')}{draft.userEditedOutline ? ' · Có chỉnh sửa của người dùng' : ''}</p>
          {draft.outline.sections.map((s, i) => <div className="review-outline-section" key={i}>
            <div className="review-actions"><strong>Mục {i + 1}</strong><button type="button" aria-label={`Đưa mục ${i + 1} lên`} disabled={i === 0} onClick={() => move(i, -1)}>Lên</button><button type="button" aria-label={`Đưa mục ${i + 1} xuống`} disabled={i === draft.outline!.sections.length - 1} onClick={() => move(i, 1)}>Xuống</button><button type="button" disabled={draft.outline!.sections.length <= 1} onClick={() => outline({ ...draft.outline!, sections: draft.outline!.sections.filter((_, n) => i !== n) })}>Bỏ mục</button></div>
            <label className="live-field">Tiêu đề mục {i + 1}<input maxLength={120} value={s.title} onChange={e => changeSection(i, { title: e.target.value })} /></label>
            <label className="live-field">Lý do sắp xếp mục {i + 1}<textarea maxLength={900} rows={2} value={s.reason} onChange={e => changeSection(i, { reason: e.target.value })} /></label>
            <ul>{s.sourceIds.map(ref => <li key={ref}>{draft.sources.find(x => x.id === ref)?.quote}</li>)}</ul>
            <details><summary>Chọn minh chứng sẵn có</summary>{draft.sources.map(source => <label className="review-check" key={source.id}><input type="checkbox" checked={s.sourceIds.includes(source.id)} onChange={e => changeSection(i, { sourceIds: e.target.checked ? [...s.sourceIds, source.id] : s.sourceIds.filter(x => x !== source.id) })} />{source.quote}</label>)}</details>
            <label className="live-field">Gợi ý chỉnh mục {i + 1}<textarea rows={3} maxLength={1500} value={s.advice} onChange={e => changeSection(i, { advice: e.target.value })} /></label>
          </div>)}<button type="button" disabled={draft.outline.sections.length >= 10} onClick={() => outline({ ...draft.outline!, sections: [...draft.outline!.sections, { title: 'Mục bổ sung', reason: 'Bổ sung nội dung có thật phù hợp vị trí mục tiêu.', sourceIds: [], gapIds: [], advice: '' }] })}>Thêm mục CV</button></>}
        </div></div>
        {!!draft.outline?.learningActions.length && <div className="review-extraction"><h3>Cần học/thực hành trước khi thêm vào CV</h3>{draft.outline.learningActions.map((a, i) => <label className="live-field" key={i}>{draft.gaps.find(g => g.id === a.gapId)?.skill}<textarea rows={2} maxLength={1000} value={a.action} onChange={e => outline({ ...draft.outline!, learningActions: draft.outline!.learningActions.map((x, n) => n === i ? { ...x, action: e.target.value } : x) })} /></label>)}</div>}
      </section>}
      {activeTab === 'bi' && <section id="review-bi" role="tabpanel" className="review-panel review-section"><h2>Nhu cầu kỹ năng trong dữ liệu hệ thống</h2><p>{draft.bi.totalJobs} tin thuộc dataset real · nhóm {draft.bi.category}.</p><p className="review-muted">Chụp lúc {new Date(draft.bi.observedAt).toLocaleString('vi-VN')}. Nguồn: {draft.bi.sources.join(', ') || 'Chưa có nguồn'}. {draft.bi.postedFrom && `Ngày đăng ${draft.bi.postedFrom} đến ${draft.bi.postedTo}.`}</p>
        {(draft.bi.smallSample || !draft.bi.totalJobs) && <p className="review-notice">{draft.bi.totalJobs ? 'Cỡ mẫu dưới 30 tin; diễn giải thận trọng.' : 'Chưa có tin thật phù hợp để tính BI. Không tạo số liệu thay thế.'}</p>}
        <table className="review-table"><thead><tr><th>Kỹ năng</th><th>Số tin / tổng</th><th>Tỷ lệ</th></tr></thead><tbody>{draft.bi.skills.map(s => <tr key={s.skill}><td>{s.skill}</td><td>{s.jobCount} / {draft.bi.totalJobs}</td><td>{s.percentage === null ? '—' : `${s.percentage.toFixed(1)}%`}</td></tr>)}</tbody></table><p className="review-muted">Mẫu nội bộ không đại diện toàn thị trường. Số liệu BI và điểm matching không dự đoán khả năng được tuyển.</p>
      </section>}
      <div className="review-footer"><button type="button" className="live-primary" disabled={!dirty} onClick={() => action('save')}>Lưu thay đổi</button><button type="button" onClick={() => action('export')}>Xuất báo cáo Markdown</button><span role="status">{dirty ? 'Nội dung chưa lưu được giữ trên màn hình nếu có lỗi.' : 'Đã lưu bản tư vấn.'}</span></div>
    </fieldset>
  </div>;
}
