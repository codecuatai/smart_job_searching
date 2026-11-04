'use client';

import React from 'react';
import Link from 'next/link';
import {
  GitPullRequest,
  Clock,
  Calendar,
  Video,
  Building2,
  ArrowRight,
  Download,
  FileText
} from 'lucide-react';

import { ApplicationStage } from '@/types';
import { useToast } from '@/context/ToastContext';
import { useResume } from '@/context/ResumeContext';

export default function StudentApplicationsPage() {
  const { showToast } = useToast();
  const { submissions, isLoaded, downloadSubmittedResume, error, refresh } = useResume();

  const stages: { key: ApplicationStage; title: string; count: number; colorClass: string; borderClass: string }[] = [
    {
      key: 'submitted',
      title: 'HỒ SƠ ĐÃ GỬI',
      count: submissions.filter((a) => a.stage === 'submitted').length,
      colorClass: 'text-slate-700 bg-slate-100',
      borderClass: 'border-slate-200',
    },
    {
      key: 'reviewing',
      title: 'ĐANG XÉT DUYỆT',
      count: submissions.filter((a) => a.stage === 'reviewing').length,
      colorClass: 'text-blue-800 bg-blue-100',
      borderClass: 'border-blue-200',
    },
    {
      key: 'interview',
      title: 'MỜI PHỎNG VẤN TRỰC TIẾP',
      count: submissions.filter((a) => a.stage === 'interview').length,
      colorClass: 'text-amber-800 bg-amber-100',
      borderClass: 'border-amber-200',
    },
    {
      key: 'offered',
      title: 'NHẬN OFFER CHÍNH THỨC',
      count: submissions.filter((a) => a.stage === 'offered').length,
      colorClass: 'text-emerald-800 bg-emerald-100',
      borderClass: 'border-emerald-200',
    },
  ];

  const handleJoinMeeting = () => {
    showToast('Lịch phỏng vấn', 'Vui lòng liên hệ người phỏng vấn theo thông tin trong lịch.', 'info');
  };

  return (
    <div className="space-y-6">
      {error && <p role="alert" className="form-error">{error} <button onClick={() => void refresh()}>Thử lại</button></p>}
      <button className="analytics-refresh" onClick={() => void refresh()}>Làm mới trạng thái</button>
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 bg-blue-50 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-md mb-2 border border-blue-200">
            <GitPullRequest className="w-3.5 h-3.5 text-blue-600" />
            <span>Tiến độ trên máy chủ</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Tiến Độ Ứng Tuyển & Lịch Phỏng Vấn
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Theo dõi trạng thái phản hồi từ doanh nghiệp sau khi làm mới (Kanban 4 giai đoạn).
          </p>
        </div>

        <Link
          href="/student/jobs"
          className="bg-blue-700 hover:bg-blue-800 text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors flex items-center space-x-1.5 self-start sm:self-auto shadow-xs"
        >
          <span>Khám phá thêm việc làm</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {isLoaded && submissions.length > 0 && <section className="submitted-resumes" aria-labelledby="submitted-resumes-heading">
        <div className="submitted-resumes-heading">
          <div><h2 id="submitted-resumes-heading">CV đã gửi</h2><p>Các hồ sơ đã gửi từ tài khoản của bạn</p></div>
          <span>{submissions.length} đơn</span>
        </div>
        <div className="submitted-resumes-list">
          {submissions.map(application => <article key={application.id} className="submitted-resume-row">
            <div className="submitted-resume-icon"><FileText size={18} /></div>
            <div className="submitted-resume-main"><strong>{application.jobTitle}</strong><span>{application.company} · {application.applicantName}</span></div>
            <div className="submitted-resume-file"><FileText size={14} /><span>{application.resumeName}</span></div>
            <time dateTime={application.submittedAt}>{new Date(application.submittedAt).toLocaleDateString('vi-VN')}</time>
            <button type="button" onClick={() => downloadSubmittedResume(application.id).catch(error => showToast('Không thể tải CV', error instanceof Error ? error.message : 'Vui lòng thử lại.', 'warning'))}><Download size={15} /> Tải CV</button>
          </article>)}
        </div>
      </section>}

      {/* Kanban Board 4 Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-start">
        {stages.map((stage) => {
          const items = submissions.filter((a) => a.stage === stage.key);
          return (
            <div
              key={stage.key}
              className="bg-slate-50/80 p-4 rounded-xl border border-slate-200 space-y-3 min-h-[400px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 tracking-wide">
                  {stage.title}
                </span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${stage.colorClass}`}>
                  {stage.count}
                </span>
              </div>

              {/* Cards in this stage */}
              <div className="space-y-3">
                {items.length === 0 ? (
                  <div className="py-12 text-center text-slate-400 text-xs italic">
                    Chưa có hồ sơ ở giai đoạn này
                  </div>
                ) : (
                  items.map((app) => (
                    <div
                      key={app.id}
                      className="bg-white p-4 rounded-xl border border-slate-200 hover:border-slate-300 transition-all shadow-xs space-y-3"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                            {app.matchScore}% Match
                          </span>
                          <span className="text-[11px] text-slate-400 flex items-center">
                            <Clock className="w-3 h-3 mr-1" /> {new Date(app.updatedAt).toLocaleDateString('vi-VN')}
                          </span>
                        </div>
                        <h4 className="font-bold text-sm text-slate-900 leading-snug">
                          {app.jobTitle}
                        </h4>
                        <p className="text-xs text-slate-500 font-medium mt-0.5 flex items-center space-x-1">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          <span>{app.company}</span>
                        </p>
                      </div>

                      <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 leading-relaxed">
                        {app.note}
                      </p>

                      {/* If Interview Scheduled */}
                      {app.interviewSchedule && (
                        <div className="bg-amber-50/70 border border-amber-200 p-3 rounded-lg space-y-2 text-xs">
                          <div className="font-bold text-amber-900 flex items-center space-x-1.5">
                            <Calendar className="w-3.5 h-3.5 text-amber-700" />
                            <span>{app.interviewSchedule.date} ({app.interviewSchedule.time})</span>
                          </div>
                          <p className="text-amber-800 leading-tight">
                            {app.interviewSchedule.format}
                          </p>
                          <p className="text-[11px] text-slate-500 italic">
                            Người phỏng vấn: {app.interviewSchedule.interviewer}
                          </p>
                          <button
                            onClick={() => handleJoinMeeting()}
                            className="w-full mt-1 bg-amber-700 hover:bg-amber-800 text-white font-semibold py-1.5 px-3 rounded-md transition-colors flex items-center justify-center space-x-1.5 cursor-pointer text-xs"
                          >
                            <Video className="w-3.5 h-3.5" />
                            <span>Cách tham gia phỏng vấn</span>
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
