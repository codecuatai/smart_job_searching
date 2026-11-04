'use client';
import { FormEvent, useState } from 'react';
import { api } from '@/lib/api';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';

interface Question { id: string; question: string }
interface Result { score: number; feedback: string; matchedConcepts: string[]; suggestedConcepts: string[] }
interface History { id: string; questionId: string; answer: string; result: Result; createdAt: string }
export default function InterviewPage() {
  const questions = useResource<Question[]>('/interview/questions');
  const history = useResource<History[]>('/interview/history');
  const [selected, setSelected] = useState(''); const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const question = questions.data?.find(q => q.id === selected) || questions.data?.[0];
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (!question) return;
    setBusy(true); setError(''); setResult(null);
    try {
      setResult(await api<Result>('/interview/evaluate', { method: 'POST', body: JSON.stringify({ questionId: question.id, answer }) }));
      history.reload();
    } catch (err) { setError(err instanceof Error ? err.message : 'Không chấm được câu trả lời.'); }
    finally { setBusy(false); }
  };
  if (questions.loading || questions.error) return <DataState error={questions.error} retry={questions.reload} />;
  return <div className="live-page">
    <header><h1>Luyện phỏng vấn kỹ thuật</h1><p>Trả lời bằng văn bản, nhận phản hồi theo rubric và xem lại lịch sử.</p></header>
    <p className="data-notice">Bản cục bộ dùng bộ câu hỏi và chấm từ khóa. Điểm không xác nhận câu trả lời đúng hay năng lực thực tế; chưa có nhận diện giọng nói hoặc mô hình hội thoại.</p>
    <form className="live-panel live-form" onSubmit={submit}>
      <label className="live-field">Chủ đề<select value={question?.id || ''} onChange={e => { setSelected(e.target.value); setAnswer(''); setResult(null); }}>{questions.data?.map(q => <option key={q.id} value={q.id}>{q.id === 'api' ? 'Thiết kế API' : q.id === 'database' ? 'Tối ưu cơ sở dữ liệu' : 'Kinh nghiệm dự án'}</option>)}</select></label>
      <h2>{question?.question}</h2>
      <label className="live-field">Câu trả lời của bạn<textarea required rows={9} maxLength={10000} value={answer} onChange={e => setAnswer(e.target.value)} placeholder="Mô tả giải pháp, ví dụ và cách kiểm chứng…" /></label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="live-primary" disabled={busy || !question}>{busy ? 'Đang phân tích…' : 'Phân tích câu trả lời'}</button>
    </form>
    {result && <section className="live-panel" aria-live="polite"><h2>Kết quả rubric: {result.score}/100</h2><p>{result.feedback}</p><p>Khái niệm đã đề cập: {result.matchedConcepts.join(', ') || 'Chưa nhận diện'}</p><p>Gợi ý bổ sung: {result.suggestedConcepts.join(', ') || 'Thêm ví dụ và kiểm chứng'}</p></section>}
    <section className="live-panel"><h2>Lịch sử luyện tập</h2>
      {history.error ? <DataState error={history.error} retry={history.reload} /> : history.loading ? <p>Đang tải lịch sử…</p> : history.data?.length ? history.data.map(item => <details key={item.id}><summary>{new Date(item.createdAt).toLocaleString('vi-VN')} · {item.questionId} · {item.result.score}/100</summary><p className="whitespace-pre-wrap">{item.answer}</p><p>{item.result.feedback}</p></details>) : <p>Chưa có câu trả lời nào được lưu.</p>}
    </section>
  </div>;
}
