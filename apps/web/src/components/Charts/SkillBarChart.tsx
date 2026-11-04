'use client';

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { MarketStatItem } from '@/types';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface SkillBarChartProps {
  stats: MarketStatItem[];
}

export default function SkillBarChart({ stats }: SkillBarChartProps) {
  const data = {
    labels: stats.map((s) => s.skill),
    datasets: [
      {
        label: 'Tỷ lệ Doanh nghiệp yêu cầu (%)',
        data: stats.map((s) => s.demandPercentage),
        backgroundColor: '#1d4ed8',
        borderRadius: 6,
      },
      {
        label: 'Tỷ lệ Sinh viên đáp ứng (%)',
        data: stats.map((s) => s.supplyPercentage),
        backgroundColor: '#94a3b8',
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: '#475569',
          font: { family: "'DM Sans', sans-serif", size: 11 },
          maxRotation: 25,
          minRotation: 15,
        },
      },
      y: {
        grid: { color: '#f1f5f9' },
        ticks: {
          color: '#94a3b8',
          font: { family: "'DM Sans', sans-serif", size: 11 },
          stepSize: 20,
        },
        max: 100,
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          boxWidth: 12,
          font: { family: "'DM Sans', sans-serif", size: 12 },
          color: '#334155',
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
      <Bar data={data} options={options} />
    </div>
  );
}
