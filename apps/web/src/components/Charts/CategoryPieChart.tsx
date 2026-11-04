'use client';

import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { CategoryDistribution } from '@/types';

ChartJS.register(ArcElement, Tooltip, Legend);

interface CategoryPieChartProps {
  distribution: CategoryDistribution[];
}

export default function CategoryPieChart({ distribution }: CategoryPieChartProps) {
  const data = {
    labels: distribution.map((d) => d.category),
    datasets: [
      {
        data: distribution.map((d) => d.percentage),
        backgroundColor: ['#1d4ed8', '#0284c7', '#0d9488', '#64748b'],
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          boxWidth: 12,
          padding: 12,
          font: { family: "'DM Sans', sans-serif", size: 11 },
          color: '#334155',
        },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { family: "'DM Sans', sans-serif", size: 12 },
        bodyFont: { family: "'DM Sans', sans-serif", size: 11 },
        callbacks: {
          label: (context: { label: string; parsed: number }) => ` ${context.label}: ${context.parsed}%`,
        },
      },
    },
    cutout: '65%',
  };

  return (
    <div className="w-full h-64 sm:h-72">
      <Doughnut data={data} options={options} />
    </div>
  );
}
