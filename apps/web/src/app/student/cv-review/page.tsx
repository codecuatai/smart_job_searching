import CVReviewStart from '@/components/CVReviewStart';
import './review.css';

export default async function CVReviewPage({ searchParams }: { searchParams: Promise<{ jobId?: string | string[]; cvId?: string | string[] }> }) {
  const search = await searchParams;
  const jobId = typeof search.jobId === 'string' ? search.jobId : '';
  const cvId = typeof search.cvId === 'string' ? search.cvId : '';
  return <CVReviewStart key={`${jobId}:${cvId}`} initialJobId={jobId} initialResumeId={cvId} />;
}
