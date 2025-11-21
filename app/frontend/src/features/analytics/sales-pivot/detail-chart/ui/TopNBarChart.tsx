/**
 * detail-chart/ui/TopNBarChart.tsx
 * TopNデータの棒グラフコンポーネント
 */

import React from 'react';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip as RTooltip } from 'recharts';
import type { MetricEntry } from '../../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice } from '../../shared/model/metrics';

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
    件数: d.count,
    単価: d.unit_price ?? 0,
  }));

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" hide={chartData.length > 12} />
          <YAxis />
          <RTooltip
            formatter={(value: number, name: string) => {
              if (name === '売上') return fmtCurrency(value);
              if (name === '数量') return `${fmtNumber(value)} kg`;
              if (name === '件数') return `${fmtNumber(value)} 件`;
              if (name === '単価') return fmtUnitPrice(value);
              return value;
            }}
          />
          <Bar dataKey="売上" />
          <Bar dataKey="数量" />
          <Bar dataKey="件数" />
          <Bar dataKey="単価" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
