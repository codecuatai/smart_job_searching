export type RoleType = 'student' | 'recruiter';

export type JobCategory = 'all' | 'backend' | 'frontend' | 'ai' | 'devops' | 'mobile';

export type ApplicationStage = 'submitted' | 'reviewing' | 'interview' | 'offered';

export interface Job {
  id: string;
  isDemo?: boolean;
  explanation?: string;
  matchedSkills?: string[];
  title: string;
  company: string;
  logoText: string;
  location: string;
  workType: 'Full-time' | 'Internship' | 'Part-time';
  salary: string;
  postedAt: string;
  category: JobCategory;
  tags: string[];
  matchScore: number;
  projectSubstituteNote: string;
  astCleanCodeScore: number;
  description: string;
  requirements: string[];
  benefits: string[];
  missingSkills?: string[];
  modelVersion?: string;
  scoreMeaning?: string;
  scoreFactors?: { feature: string; value: number; weight: number; contribution: number }[];
  missingMustHaveSkills?: string[];
  evidence?: { skill: string; quote: string }[];
}

export interface Candidate {
  id: string;
  name: string;
  university: string;
  major: string;
  year: string;
  gpa: number;
  email: string;
  avatarText: string;
  avatarUrl?: string;
  targetRole: string;
  matchScore: number;
  status: ApplicationStage;
  appliedDate: string;
  astAudit: {
    cleanCodeScore: number;
    solidCompliance: number;
    plagiarismPercentage: number;
    cyclomaticComplexity: string;
    securityVulnerabilities: number;
    verifiedCommitCount: number;
  };
  featuredProject: {
    title: string;
    repo: string;
    techStack: string[];
    summary: string;
    score: number;
  };
  voiceAiAssessment: {
    overallScore: number;
    technicalDepth: number;
    problemSolving: number;
    communication: number;
    feedbackSummary: string;
    completedAt: string;
  };
  skillsRadar: {
    skill: string;
    candidateScore: number;
    marketBenchmark: number;
  }[];
}

export interface ApplicationTrackingItem {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  stage: ApplicationStage;
  updatedAt: string;
  matchScore: number;
  note: string;
  interviewSchedule?: {
    date: string;
    time: string;
    format: string;
    interviewer: string;
  };
}

export interface SkillGapItem {
  skill: string;
  currentLevel: string;
  requiredLevel: string;
  importance: 'critical' | 'recommended' | 'optional';
  gapDescription: string;
}

export interface RoadmapStep {
  week: number;
  timeRange: string;
  focusTitle: string;
  milestones: string[];
  curatedResource: string;
}

export interface SkillGapDiagnosis {
  targetJobTitle: string;
  company: string;
  currentScore: number;
  projectedScore?: number;
  planId?: string | null;
  method?: string;
  summary?: string;
  completedTasks?: Record<string, boolean>;
  hoursPerWeek?: number;
  gaps: SkillGapItem[];
  roadmap: RoadmapStep[];
}

export interface MarketStatItem {
  skill: string;
  demandPercentage: number;
  supplyPercentage: number;
  shortagePercentage: number;
  candidateCount?: number;
  jobCount?: number;
}

export interface CategoryDistribution {
  category: string;
  percentage: number;
  jobCount: number;
}

export interface SalaryStatItem {
  category: string;
  sampleSize: number;
  averageMinimumVnd: number;
  averageMaximumVnd: number;
  medianMinimumVnd?: number;
  medianMaximumVnd?: number;
}

export interface HiringFunnelItem {
  stage: ApplicationStage;
  label: string;
  count: number;
  reachedPercentage: number;
  conversionFromPreviousPercentage: number;
}
