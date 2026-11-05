'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Stethoscope,
  Mic,
  Layers,
  Building2
} from 'lucide-react';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import { Job } from '@/types';
import { ScoreSummary } from '@/components/WorkspaceUI';
import { jobDate, jobSalary } from '@/lib/jobPresentation';
import ApplyWithResumeButton from '@/components/ApplyWithResumeButton';

export default function JobDetailPage() {
  const params = useParams();

  const jobId = params?.id as string;
  const { data: job, error, reload } = useResource<Job>(`/jobs/${jobId}`);
  if (!job || error) return <DataState error={error} retry={reload} />;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/student/jobs"
          className="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Quay lại danh sách việc làm</span>
        </Link>
      </div>

      {/* Header Card */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 text-white font-bold flex items-center justify-center text-lg flex-shrink-0 shadow-sm">
              {job.logoText}
            </div>
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                  {job.title}
                </h1>
                <span className="text-xs bg-slate-100 text-slate-700 font-medium px-2.5 py-0.5 rounded-full border border-slate-200">
                  {job.workType}
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-700 flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-slate-500" />
                <span>{job.company}</span>
              </p>
              <div className="flex flex-wrap items-center text-xs text-slate-500 gap-x-3 gap-y-1 pt-1">
                <span className="flex items-center">
                  <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" /> {job.location}
                </span>
                <span>•</span>
                <span className="font-semibold text-emerald-700">{jobSalary(job.salary)}</span>
                <span>•</span>
                <span className="flex items-center text-slate-400">
                  <Clock className="w-3.5 h-3.5 mr-1" /> Đăng {jobDate(job.postedAt)}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Apply / Match Column */}
          <div className="flex flex-col sm:flex-row md:flex-col items-stretch sm:items-center md:items-end gap-3 min-w-[220px]">
            <div className="bg-blue-50/70 border border-blue-200 p-3 rounded-xl text-center md:text-right w-full">
              <span className="text-xs text-blue-700 font-semibold block">Độ phù hợp kỹ năng & văn bản</span>
              <ScoreSummary score={job.matchScore} provisional={job.scoreStatus==='insufficient-cv'}/>
              <span className="text-[11px] text-slate-500 block mt-0.5">{job.explanation || 'Chưa xác minh năng lực hoặc mã nguồn.'}</span>
            </div>

            <ApplyWithResumeButton
              job={job}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition-colors cursor-pointer shadow-xs"
            >
              Nộp hồ sơ ngay
            </ApplyWithResumeButton>
          </div>
        </div>

        {/* Project Substitution Guarantee Banner */}
        <div className="bg-blue-50/60 border border-blue-200 p-4 rounded-xl flex items-start space-x-3 text-xs sm:text-sm text-blue-950">
          <Layers className="w-5 h-5 text-blue-700 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-blue-900">Cam kết quy đổi đồ án thay kinh nghiệm thực tế</h4>
            <p className="mt-0.5 leading-relaxed text-blue-800">
              {job.projectSubstituteNote}. Đây là ghi chú của tin tuyển dụng. Hệ thống chưa thẩm định mã nguồn hoặc quy đổi số năm kinh nghiệm.
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Description & AI Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): JD Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
            <h3 className="font-bold text-base text-slate-900 border-b border-slate-100 pb-3">
              Mô tả công việc
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {job.description}
            </p>
          </div>

          {/* Requirements */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
            <h3 className="font-bold text-base text-slate-900 border-b border-slate-100 pb-3">
              Yêu cầu chuyên môn & Năng lực
            </h3>
            <ul className="space-y-2.5">
              {job.requirements.map((req, i) => (
                <li key={i} className="flex items-start space-x-2.5 text-xs sm:text-sm text-slate-700">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Benefits */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
            <h3 className="font-bold text-base text-slate-900 border-b border-slate-100 pb-3">
              Chế độ đãi ngộ & Môi trường
            </h3>
            <ul className="space-y-2.5">
              {job.benefits.map((b, i) => (
                <li key={i} className="flex items-start space-x-2.5 text-xs sm:text-sm text-slate-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column (1 Col): AI Diagnosis & Actions */}
        <div className="space-y-6">
          <section className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3" aria-label="Giải thích matching">
            <h2 className="font-bold">Cách tính độ phù hợp</h2>
            <p className="text-sm text-slate-600">{job.scoreMeaning} Model: {job.modelVersion}.</p>
            <p>{job.explanation}</p>
            <div className="score-calculation"><span>Điểm mô hình ban đầu: {job.rawScore ?? job.matchScore}/100</span>{job.adjustments?.map(a => <p key={a.code}>{a.reason} <strong>{a.before} → {a.after}</strong></p>)}<strong>Điểm cuối: {job.finalScore ?? job.matchScore}/100</strong></div>
            {!!job.unknownRequirements?.length && <p className="data-notice">Yêu cầu chưa đối chiếu được: {job.unknownRequirements.join(', ')}</p>}
            {job.sourceUrl && <a href={job.sourceUrl} target="_blank" rel="noreferrer">Xem tin gốc tại {job.source || 'nguồn tuyển dụng'} ↗</a>}
            <p className="text-sm">Kỹ năng khớp: {job.matchedSkills?.join(', ') || 'Chưa nhận diện được'}</p>
            {!!job.missingMustHaveSkills?.length && <p className="text-sm">Thiếu bắt buộc: {job.missingMustHaveSkills.join(', ')}</p>}
            <details><summary className="cursor-pointer text-sm font-semibold">Xem hệ số và bằng chứng</summary>
              <p className="text-xs text-slate-500 my-2">Hệ số đóng góp vào logit trước sigmoid. Hệ số 0 nghĩa là model hiện tại chưa sử dụng yếu tố đó. Kinh nghiệm thiếu thông tin được để unknown.</p>
              {job.scoreFactors?.map(f => <p className="text-xs py-1" key={f.feature}>{({coverage:'Độ phủ kỹ năng',cosineSimilarity:'Tương đồng văn bản',requiredSkillRatio:'Số kỹ năng yêu cầu',mustHaveCoverage:'Kỹ năng bắt buộc',experienceFit:'Kinh nghiệm'} as Record<string,string>)[f.feature] || f.feature}: {Math.round(f.value*100)}% · hệ số {f.weight.toFixed(3)}</p>)}
              {job.evidence?.map(e => <blockquote className="text-sm border-l-2 pl-2 my-2 break-words" key={e.skill}><strong>{e.skill}</strong>: {e.quote}</blockquote>)}
            </details>
          </section>
          {/* Missing Skills Warning */}
          {job.missingSkills && job.missingSkills.length > 0 && (
            <div className="bg-amber-50/50 border border-amber-200 p-5 rounded-2xl space-y-3">
              <div className="flex items-center space-x-2 text-xs font-bold text-amber-900">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Kỹ năng bạn còn thiếu so với JD này</span>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                Các kỹ năng trong yêu cầu chưa có bằng chứng trong hồ sơ của bạn:
              </p>
              <div className="space-y-1.5">
                {job.missingSkills.map((skill, idx) => (
                  <div key={idx} className="bg-white px-2.5 py-1.5 rounded-lg border border-amber-200 text-xs text-slate-700 font-medium">
                    • {skill}
                  </div>
                ))}
              </div>
              <Link
                href="/student/skill-gap"
                className="w-full mt-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 transition-colors cursor-pointer"
              >
                <Stethoscope className="w-3.5 h-3.5" />
                <span>Xem lộ trình bù hổng 2 tuần</span>
              </Link>
            </div>
          )}

          {/* Quick Mock Interview Callout */}
          <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-blue-400">
              <Mic className="w-4 h-4" />
              <span>Luyện phỏng vấn bằng AI</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Trả lời câu hỏi bằng văn bản và nhận phản hồi Gemini theo vị trí mục tiêu.
            </p>
            <Link
              href="/student/mock-interview"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 transition-colors"
            >
              <span>Vào buồng phỏng vấn</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
