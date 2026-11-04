'use client';

import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

interface RadarChartProps {
  skills: {
    skill: string;
    candidateScore: number;
    marketBenchmark: number;
  }[];
}

export default function RadarChart({ skills }: RadarChartProps) {
  const data = {
    labels: skills.map((s) => s.skill),
    datasets: [
      {
        label: 'Năng lực ứng viên (Nam Nguyễn)',
        data: skills.map((s) => s.candidateScore),
        backgroundColor: 'rgba(39, 133, 91, 0.12)',
        borderColor: '#27855b',
        borderWidth: 2,
        pointBackgroundColor: '#27855b',
        pointBorderColor: '#ffffff',
        pointHoverBackgroundColor: '#ffffff',
        pointHoverBorderColor: '#27855b',
      },
      {
        label: 'Ngưỡng trung bình thị trường',
        data: skills.map((s) => s.marketBenchmark),
        backgroundColor: 'rgba(166, 189, 171, 0.07)',
        borderColor: '#9bbba4',
        borderWidth: 1.5,
        borderDash: [4, 4],
        pointBackgroundColor: '#9bbba4',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          color: '#e2e8f0',
        },
        grid: {
          color: '#f1f5f9',
        },
        pointLabels: {
          font: {
            family: "'DM Sans', sans-serif",
            size: 11,
            weight: 600 as const,
          },
          color: '#334155',
        },
        ticks: {
          backdropColor: 'transparent',
          color: '#94a3b8',
          font: {
            size: 9,
          },
          stepSize: 20,
        },
        suggestedMin: 30,
        suggestedMax: 100,
      },
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          boxWidth: 12,
          padding: 16,
          font: {
            family: "'DM Sans', sans-serif",
            size: 12,
          },
          color: '#475569',
        },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { family: "'DM Sans', sans-serif", size: 12 },
        bodyFont: { family: "'DM Sans', sans-serif", size: 11 },
        padding: 10,
        cornerRadius: 8,
      },
    },
  };

  return (
    <div className="w-full h-72 sm:h-80">
      <Radar data={data} options={options} />
    </div>
  );
}
