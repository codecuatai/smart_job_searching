import { ReactNode } from 'react';

export function PageHeader({title, description, action}: {title: string; description?: string; action?: ReactNode}) {
  return <header className="page-header"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="page-header-actions">{action}</div>}</header>;
}

export function ScoreSummary({score, provisional}: {score: number; provisional?: boolean}) {
  return <div className={`job-score score-summary ${provisional ? 'is-provisional' : ''}`} aria-label={`Điểm xếp hạng ${score} trên 100${provisional ? ', chưa đủ dữ liệu CV' : ''}`}><div><strong>{score}</strong><small>/100</small></div><span>{provisional ? 'Sơ bộ' : 'Phù hợp'}</span></div>;
}
