/**
 * summary-table/ui/MetricChart.tsx
 * チャート表示コンポーネント（TopN棒グラフ + 日次推移折れ線）
 */

import React from 'react';
import { Row, Col, Space, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ResponsiveContainer,
} from 'recharts';
import { fmtCurrency, fmtNumber, fmtUnitPrice } from '../../shared/model/metrics';
import type { MetricEntry, SummaryQuery } from '../../shared/model/types';

interface MetricChartProps {
  data: MetricEntry[];
  series: unknown[] | undefined;
  repName: string;
  onLoadSeries: () => Promise<void>;
  query: SummaryQuery;
}

/**
 * メトリックチャートコンポーネント
 */
export const MetricChart: React.FC<MetricChartProps> = ({
  data,
  series,
  repName,
  onLoadSeries,
  query,
}) => {
  const chartBarData = data.map((d: MetricEntry) => ({
    name: d.name,
    売上: d.amount,
    数量: d.qty,
    件数: d.count,
    単価: d.unit_price ?? 0,
  }));

  return (
    <Row gutter={[16, 16]}>
      {/* TopN棒グラフ */}
      <Col xs={24} xl={14}>
        <div className="card-subtitle">TopN（売上・数量・件数・単価）</div>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={chartBarData} margin={{ top: 8, right: 8, left: 8, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide={chartBarData.length > 12} />
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
              <Bar dataKey="売上" fill="#237804" />
              <Bar dataKey="数量" fill="#52c41a" />
              <Bar dataKey="件数" fill="#1890ff" />
              <Bar dataKey="単価" fill="#faad14" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Col>

      {/* 日次推移折れ線グラフ */}
      <Col xs={24} xl={10}>
        <Space align="baseline" style={{ justifyContent: 'space-between', width: '100%' }}>
          <div className="card-subtitle">
            {query.month
              ? `${query.month} 日次推移`
              : `${query.monthRange!.from}〜${query.monthRange!.to} 日次推移`}
            （営業：{repName}）
          </div>
          {!series && (
            <Button size="small" onClick={onLoadSeries} icon={<ReloadOutlined />}>
              日次を取得
            </Button>
          )}
        </Space>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <LineChart data={series ?? []} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" hide />
              <YAxis />
              <RTooltip
                formatter={(v: number | string, name: string) => {
                  if (name === '売上') return fmtCurrency(Number(v));
                  if (name === '数量') return `${fmtNumber(Number(v))} kg`;
                  if (name === '件数') return `${fmtNumber(Number(v))} 件`;
                  if (name === '単価') return fmtUnitPrice(Number(v));
                  return v;
                }}
                labelFormatter={(l) => l}
              />
              <Line type="monotone" dataKey="amount" name="売上" stroke="#237804" />
              <Line type="monotone" dataKey="qty" name="数量" stroke="#52c41a" />
              <Line type="monotone" dataKey="count" name="件数" stroke="#1890ff" />
              <Line type="monotone" dataKey="unit_price" name="単価" stroke="#faad14" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Col>

      <style>{`
        .card-subtitle { color: rgba(0,0,0,0.55); margin-bottom: 6px; font-size: 12px; }
      `}</style>
    </Row>
  );
};
