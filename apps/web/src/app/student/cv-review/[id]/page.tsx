import ConsultationEditor from '@/components/ConsultationEditor';
import '../review.css';

export default async function CVReviewDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ConsultationEditor id={id} />;
}
