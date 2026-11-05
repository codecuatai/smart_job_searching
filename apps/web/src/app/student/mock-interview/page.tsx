'use client';
import { FormEvent, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import JobSelector from '@/components/JobSelector';

interface Question { id: string; question: string; topic?: string; method?: string }
interface Result { score: number; feedback: string; matchedConcepts: string[]; suggestedConcepts: string[]; method?: string; question?: string }
interface History { id: string; questionId: string; answer: string; result: Result; createdAt: string }
export default function InterviewPage() {
  const questions = useResource<Question[]>('/interview/questions');
  const history = useResource<History[]>('/interview/history');
  const jobs = useResource<{ id: string; title: string }[]>('/jobs');
  const [target, setTarget] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generatedQuestions, setGeneratedQuestions] = useState<Question[] | null>(null);
  const [generationError, setGenerationError] = useState('');
  const [selected, setSelected] = useState(''); const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [evaluationError, setEvaluationError] = useState('');
  const [answerError, setAnswerError] = useState('');
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const questionList = generatedQuestions ?? questions.data ?? [];
  const question = questionList.find(q => q.id === selected) || questionList[0];
  const generate = async () => {
    setGenerating(true); setGenerationError('');
    try {
      const fresh = await api<Question[]>('/interview/questions', { method: 'POST', body: JSON.stringify({ jobId: target || null }) });
      setGeneratedQuestions(fresh);
      setSelected(fresh[0]?.id || ''); setAnswer(''); setResult(null);
      setEvaluationError(''); setAnswerError('');
    } catch (err) { setGenerationError(err instanceof Error ? err.message : 'Không tạo được câu hỏi.'); }
    finally { setGenerating(false); }
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (!question) return;
    if (!answer.trim()) {
      setAnswerError('Vui lòng nhập câu trả lời trước khi phân tích.');
      answerRef.current?.focus();
      return;
    }
    setBusy(true); setEvaluationError(''); setAnswerError(''); setResult(null);
    try {
      setResult(await api<Result>('/interview/evaluate', { method: 'POST', body: JSON.stringify({ questionId: question.id, answer }) }));
      history.reload();
    } catch (err) { setEvaluationError(err instanceof Error ? err.message : 'Không chấm được câu trả lời.'); }
    finally { setBusy(false); }
  };
  if (questions.loading || questions.error) return <DataState error={questions.error} retry={questions.reload} />;
  return <div className="live-page">
    <header><h1>Luyện phỏng vấn kỹ thuật</h1><p>Trả lời bằng văn bản, nhận phản hồi theo rubric và xem lại lịch sử.</p></header>
    <p className="data-notice">Gemini tạo câu hỏi theo kỹ năng, dự án và vị trí mục tiêu, đồng thời phân tích câu trả lời. Điểm dùng cho luyện tập. {question?.method?.startsWith('gemini:') ? `Đang hiển thị bộ câu hỏi đã lưu từ ${question.method.replace('gemini:', '')}.` : question?.method?.startsWith('test-fixture:') ? 'Bộ câu hỏi kiểm thử offline, không phải kết quả Gemini thật.' : 'Đang hiển thị bộ câu hỏi tham khảo; bấm nút bên dưới để tạo câu hỏi AI cá nhân hóa.'}</p>
    <section className="live-panel" aria-labelledby="interview-generator-title">
      <h2 id="interview-generator-title">1. Chuẩn bị bộ câu hỏi</h2>
      <JobSelector label="Vị trí phỏng vấn" jobs={jobs.data || []} value={target} onChange={value => { setTarget(value); setGenerationError(''); }} disabled={generating || busy} />
      <p>Chọn vị trí rồi bấm tạo. Bộ câu hỏi bên dưới chỉ được thay khi tạo mới thành công.</p>
      <button type="button" className="live-primary" onClick={generate} disabled={generating || busy}>{generating ? 'Gemini đang tạo câu hỏi…' : 'Tạo bộ câu hỏi AI'}</button>
      {generationError && <div className="form-error" role="alert"><p>Không tạo được bộ câu hỏi mới. Bộ câu hỏi và câu trả lời hiện tại vẫn được giữ.</p><p>{generationError}</p><p>Bạn có thể bấm “Tạo bộ câu hỏi AI” để thử lại.</p></div>}
    </section>
    <form className="live-panel live-form" onSubmit={submit} noValidate aria-label="Trả lời phỏng vấn">
      <h2>2. Trả lời và nhận phản hồi</h2>
      <label className="live-field">Chủ đề<select disabled={busy || generating} value={question?.id || ''} onChange={e => { setSelected(e.target.value); setAnswer(''); setResult(null); setEvaluationError(''); setAnswerError(''); }}>{questionList.map(q => <option key={q.id} value={q.id}>{(q.topic || q.id) === 'api' ? 'Thiết kế API' : (q.topic || q.id) === 'database' ? 'Tối ưu cơ sở dữ liệu' : 'Kinh nghiệm dự án'}</option>)}</select></label>
      <h2>{question?.question}</h2>
      <div className="live-field"><label htmlFor="interview-answer">Câu trả lời của bạn</label><textarea id="interview-answer" ref={answerRef} required rows={9} maxLength={10000} value={answer} disabled={busy || generating} aria-invalid={!!answerError} aria-describedby={answerError ? 'interview-answer-error' : undefined} onChange={e => { setAnswer(e.target.value); setAnswerError(''); setEvaluationError(''); setResult(null); }} placeholder="Mô tả giải pháp, ví dụ và cách kiểm chứng…" /></div>
      {answerError && <p id="interview-answer-error" className="form-error" role="alert">{answerError}</p>}
      {evaluationError && <div className="form-error" role="alert"><p>Chưa phân tích được câu trả lời. Nội dung bạn nhập vẫn được giữ; hãy thử lại.</p><p>{evaluationError}</p></div>}
      <button className="live-primary" disabled={busy || generating || !question}>{busy ? 'Đang phân tích…' : 'Phân tích câu trả lời'}</button>
    </form>
    {result && <section className="live-panel" aria-live="polite"><h2>Kết quả rubric: {result.score}/100</h2><p>{result.feedback}</p><small>{result.method?.startsWith('gemini:') ? `Phân tích bởi ${result.method.replace('gemini:', '')}` : 'Đánh giá dự phòng bằng rubric từ khóa; Gemini chưa khả dụng.'}</small><p>Khái niệm đã đề cập: {result.matchedConcepts.join(', ') || 'Chưa nhận diện'}</p><p>Gợi ý bổ sung: {result.suggestedConcepts.join(', ') || 'Thêm ví dụ và kiểm chứng'}</p></section>}
    <section className="live-panel"><h2>Lịch sử luyện tập</h2>
      {history.error ? <DataState error={history.error} retry={history.reload} /> : history.loading ? <p>Đang tải lịch sử…</p> : history.data?.length ? history.data.map(item => <details key={item.id}><summary>{new Date(item.createdAt).toLocaleString('vi-VN')} · {item.questionId} · {item.result.score}/100</summary><p className="whitespace-pre-wrap">{item.answer}</p><p>{item.result.feedback}</p></details>) : <p>Chưa có câu trả lời nào được lưu.</p>}
    </section>
  </div>;
}
