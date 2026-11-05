'use client';
import { useId, useState } from 'react';

export default function JobSelector({label, jobs, value, onChange, disabled}: {label: string; jobs: {id: string; title: string}[]; value: string; onChange: (value: string) => void; disabled?: boolean}) {
  const [search, setSearch] = useState('');
  const id = useId();
  const filtered = jobs.filter(job => job.id === value || job.title.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')));
  return <div className="job-selector"><label className="live-field" htmlFor={`${id}-search`}>Tìm vị trí theo tên<input id={`${id}-search`} type="search" value={search} onChange={e => setSearch(e.target.value)} disabled={disabled} placeholder="Ví dụ: Python, Backend…" /></label><label className="live-field" htmlFor={id}>{label}<select id={id} value={value} onChange={e => onChange(e.target.value)} disabled={disabled}><option value="">Vị trí phù hợp nhất</option>{filtered.map(job => <option key={job.id} value={job.id}>{job.title}</option>)}</select></label><span className="field-hint" role="status">{filtered.length} vị trí trong danh sách</span></div>;
}
