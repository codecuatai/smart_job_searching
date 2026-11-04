'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Calendar,
  BookOpen,
  ArrowRight,
  AlertTriangle,
  Building2,
  Target
} from 'lucide-react';
import { useResource } from '@/lib/useResource';
import DataState from '@/components/DataState';
import { SkillGapDiagnosis, Job } from '@/types';
import { useToast } from '@/context/ToastContext';

export default function SkillGapPage() {
  const { showToast } = useToast();
  const [target, setTarget] = useState('');
  const jobs = useResource<Job[]>('/jobs');
  const { data: gapData, error, reload } = useResource<SkillGapDiagnosis>(`/skill-gap${target ? `?jobId=${target}` : ''}`);

  const [completedTasks, setCompletedTasks] = useState<{ [key: string]: boolean }>({

  });

  const toggleTask = (key: string, taskTitle: string) => {
    const isNowDone = !completedTasks[key];
    setCompletedTasks((prev) => ({ ...prev, [key]: isNowDone }));
    if (isNowDone) {
      showToast('Tiến độ cập nhật', `Hoàn thành cột mốc: ${taskTitle}`, 'success');
    }
  };

  if (!gapData || error) return <DataState error={error} retry={reload} />;
  return (
    <div className="space-y-6">
      <label className="live-field">Vị trí mục tiêu<select value={target} onChange={e => { setTarget(e.target.value); setCompletedTasks({}); }}><option value="">Vị trí phù hợp nhất</option>{jobs.data?.map(job => <option value={job.id} key={job.id}>{job.title}</option>)}</select></label>
      <p className="data-notice">Lộ trình dựa trên kỹ năng nhận diện trong hồ sơ. Mức 100% là mục tiêu bao phủ kỹ năng, không phải dự đoán điểm sau khi học. Tiến độ đánh dấu chỉ lưu trong phiên trang hiện tại.</p>
      {/* Header */}
      <div>
        <Link
          href="/student/jobs"
          className="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 mb-2 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Về danh sách việc làm</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                Khoảng trống kỹ năng & lộ trình học
              </h1>
              <span className="text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                AI Gap Engine
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Phân tích độ lệch giữa đồ án hiện tại và yêu cầu kỹ thuật mục tiêu tại {gapData.company}.
            </p>
          </div>

          <div className="bg-white border border-slate-200 px-4 py-2 rounded-xl flex items-center space-x-4">
            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Match Hiện tại</span>
              <span className="text-lg font-bold text-amber-700">{gapData.currentScore}%</span>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-300" />
            <div>
              <span className="text-[11px] text-slate-400 block font-medium">Match Sau 2 tuần</span>
              <span className="text-lg font-bold text-emerald-700">{gapData.projectedScore}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Target Role Card */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 text-white font-bold flex items-center justify-center text-sm">
            SHO
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900">{gapData.targetJobTitle}</h3>
            <p className="text-xs text-slate-500 flex items-center space-x-1.5">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span>{gapData.company}</span>
            </p>
          </div>
        </div>

        <span className="text-xs font-semibold bg-blue-50 text-blue-800 px-3 py-1 rounded-lg border border-blue-200">
          Mục tiêu: Bổ sung minh chứng cho kỹ năng còn thiếu
        </span>
      </div>

      {/* 3 Diagnosed Gaps */}
      <div className="space-y-3">
        <h3 className="font-bold text-sm text-slate-900 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          <span>{gapData.gaps.length} kỹ năng cần bổ sung</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {gapData.gaps.map((gap, i) => (
            <div
              key={i}
              className="bg-white p-5 rounded-xl border border-slate-200 space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                      gap.importance === 'critical'
                        ? 'bg-rose-50 text-rose-800 border border-rose-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {gap.importance === 'critical' ? 'Bắt buộc bổ sung' : 'Khuyến nghị'}
                  </span>
                  <span className="text-xs text-slate-400">#0{i + 1}</span>
                </div>
                <h4 className="font-bold text-sm text-slate-900">{gap.skill}</h4>
                <p className="text-xs text-slate-600 leading-relaxed">{gap.gapDescription}</p>
              </div>

              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-[11px] space-y-1">
                <div>
                  <span className="font-semibold text-slate-500">Hiện tại: </span>
                  <span className="text-slate-700">{gap.currentLevel}</span>
                </div>
                <div>
                  <span className="font-semibold text-blue-700">Mục tiêu: </span>
                  <span className="text-blue-900 font-medium">{gap.requiredLevel}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2-Week Micro-Learning Action Plan */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <div className="inline-flex items-center space-x-1.5 bg-blue-50 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-md mb-1 border border-blue-200">
            <Target className="w-3.5 h-3.5 text-blue-600" />
            <span>Kế hoạch hành động chi tiết</span>
          </div>
          <h2 className="text-lg font-bold text-slate-900">
            Lộ trình bù đắp kỹ năng theo từng chặng
          </h2>
          <p className="text-xs text-slate-500">
            Đánh dấu vào từng cột mốc sau khi hoàn thành code thực chiến trên GitHub của bạn.
          </p>
        </div>

        <div className="space-y-6">

          {gapData.roadmap.map((weekData, wIdx) => (
            <div
              key={wIdx}
              className="bg-slate-50 p-5 sm:p-6 rounded-xl border border-slate-200 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-full bg-blue-700 text-white font-bold text-xs flex items-center justify-center">
                    {weekData.week}
                  </span>
                  <h4 className="font-bold text-sm text-slate-900">{weekData.focusTitle}</h4>
                </div>
                <span className="text-xs font-semibold text-slate-500 flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{weekData.timeRange}</span>
                </span>
              </div>

              {/* Tasks Checklist */}
              <div className="space-y-2.5">
                {weekData.milestones.map((task, tIdx) => {
                  const key = `w${weekData.week}-${tIdx}`;
                  const isChecked = !!completedTasks[key];
                  return (
                    <div
                      key={tIdx}
                      onClick={() => toggleTask(key, task)}
                      className={`p-3 rounded-lg border transition-all flex items-start space-x-3 cursor-pointer ${
                        isChecked
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}}
                        className="mt-1 h-4 w-4 rounded text-blue-600 focus:ring-blue-500 border-slate-300"
                      />
                      <span className={`text-xs sm:text-sm ${isChecked ? 'line-through text-slate-500' : 'font-medium'}`}>
                        {task}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Curated Resource */}
              <div className="bg-white p-3 rounded-lg border border-blue-200 flex items-center space-x-2.5 text-xs text-blue-900 font-medium">
                <BookOpen className="w-4 h-4 text-blue-700 flex-shrink-0" />
                <span>Gợi ý tài liệu: </span>
                <span className="font-bold">{weekData.curatedResource}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
