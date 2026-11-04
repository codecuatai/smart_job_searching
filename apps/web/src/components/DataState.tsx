export default function DataState({ error, retry }: { error?: string; retry?: () => void }) {
  return <div className="data-state" role={error ? 'alert' : 'status'}><p>{error || 'Đang tải dữ liệu…'}</p>
    {error && retry && <button type="button" onClick={retry}>Thử lại</button>}</div>;
}
