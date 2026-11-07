export type GapStatus = 'evidenced' | 'self-declared' | 'not-evidenced' | 'learning-needed' | 'unknown';
export interface ReviewGap { id: string; skill: string; jdQuote: string; priority: string; status: GapStatus; sourceId: string | null; cvQuote: string; action: string }
export interface OutlineSection { title: string; reason: string; sourceIds: string[]; gapIds: string[]; advice: string }
export interface CVOutline { sections: OutlineSection[]; learningActions: { gapId: string; action: string }[] }
export interface ReviewChecklist { cvPermission?: boolean; outlineReviewed?: boolean; videoSeconds?: number | null; submitted?: boolean; deadline?: string | null }
export interface ReviewData {
  gaps: ReviewGap[]; sources: { id: string; quote: string }[]; currentOutline: string[];
  bi: { totalJobs: number; category: string; dataset: string; observedAt: string; sources: string[]; smallSample: boolean; postedFrom: string | null; postedTo: string | null; skills: { skill: string; jobCount: number; percentage: number | null }[] };
  matching: { matchScore: number; explanation: string; scorerVersion: string };
  selectedGapIds: string[]; gapAssessments: Record<string, Exclude<GapStatus, 'evidenced'>>;
  outline: CVOutline | null; outlineMethod: string | null; script: string; checklist: ReviewChecklist; userEditedOutline?: boolean;
}
export interface CVConsultation {
  id: string; revision: number; createdAt: string; updatedAt: string;
  snapshot: { resumeId: string; resumeName: string; resumeText: string; resumeHash: string; capturedAt: string; analysisConfirmed?: boolean; analysis: { partialOcr?: boolean }; job: { title: string; company: string; description: string; requirements: string[]; sourceUrl?: string } };
  data: ReviewData;
  readiness: { gapCount: number; enoughGaps: boolean; hasOutline: boolean; reviewed: boolean; videoValid: boolean; cvPermission: boolean; submitted: boolean };
}
export interface ReviewSummary { id: string; title: string; company: string; resumeId: string; jobId: string | null; resumeName: string; revision: number; createdAt: string }
export interface ResumeVersion { id: string; name: string; createdAt: string; size: number; confirmed: boolean; analysis: { skills: { name: string; evidence: string }[]; experienceYears: number | null; status?: string } | null }
export interface ResumeJobMatch { id: string; title: string; company: string; location?: string; workType?: string; salary?: string; tags?: string[]; matchScore: number; scoreStatus?: string; matchedSkills: string[]; missingSkills: string[]; unknownRequirements?: string[]; isDemo?: boolean }
export interface ResumeMatches { resumeId: string; resumeName: string; confirmed: boolean; evaluatedJobs: number; total: number; items: ResumeJobMatch[]; target: ResumeJobMatch | null }
export const gapLabels: Record<GapStatus, string> = { evidenced: 'Có minh chứng trong CV', 'self-declared': 'Chỉ tự khai báo', 'not-evidenced': 'Chưa thấy minh chứng', 'learning-needed': 'Tôi cần học thêm', unknown: 'Chưa đủ dữ liệu đánh giá' };
