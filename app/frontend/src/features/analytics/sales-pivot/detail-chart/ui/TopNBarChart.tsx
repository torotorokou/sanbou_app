/**
 * detail-chart/ui/TopNBarChart.tsx
 * TopNデータの棒グラフコンポーネント
 */

import React from 'react';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip as RTooltip } from 'recharts';
import type { MetricEntry } from '../../shared/model/types';

export interface TopNBarChartProps {
  data: MetricEntry[];
}

/**
 * TopN棒グラフ
 */
export const TopNBarChart: React.FC<TopNBarChartProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    name: d.name,
    売上: d.amount,
    数量: d.qty,
    台数: d.count,
    売単価: d.unit_price ?? 0,
  }));

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" hide={chartData.length > 12} />
          <YAxis />
          <RTooltip />
          <Bar dataKey="売上" />
          <Bar dataKey="数量" />
          <Bar dataKey="台数" />
          <Bar dataKey="売単価" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
