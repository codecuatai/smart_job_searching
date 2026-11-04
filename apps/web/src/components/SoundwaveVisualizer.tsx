'use client';

import React from 'react';

interface SoundwaveVisualizerProps {
  isActive: boolean;
}

export default function SoundwaveVisualizer({ isActive }: SoundwaveVisualizerProps) {
  // Height profiles for sound bars
  const heights = [35, 60, 85, 45, 95, 70, 40, 90, 65, 30, 80, 50, 95, 75, 40];

  return (
    <div className="flex items-center justify-center space-x-1.5 h-16 px-4 bg-slate-900 rounded-xl border border-slate-800">
      {heights.map((h, i) => (
        <span
          key={i}
          className={`w-1 rounded-full transition-all duration-300 ${
            isActive ? 'bg-blue-400' : 'bg-slate-700'
          }`}
          style={{
            height: isActive ? `${Math.max(15, (h * (0.6 + Math.sin(i * 1.5) * 0.4)))}%` : '20%',
            opacity: isActive ? 1 : 0.4,
          }}
        />
      ))}
    </div>
  );
}
