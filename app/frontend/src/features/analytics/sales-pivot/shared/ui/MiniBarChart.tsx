/**
 * shared/ui/MiniBarChart.tsx
 * ミニバーグラフコンポーネント
 */

import React from 'react';

export interface MiniBarChartProps {
  value: number;
  maxValue: number;
  color: 'blue' | 'green' | 'gold';
  label: string | number;
  width?: number;
}

/**
 * テーブル内のミニバーグラフ
 */
export const MiniBarChart: React.FC<MiniBarChartProps> = ({
  value,
  maxValue,
  color,
  label,
  width = 80,
}) => {
  const percentage = Math.round((value / maxValue) * 100);
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
      <span style={{ minWidth: width, textAlign: 'right' }}>{label}</span>
      <div className="mini-bar-bg">
        <div
          className={`mini-bar mini-bar-${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
