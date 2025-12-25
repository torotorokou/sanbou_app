import React from 'react';
import { Card, Row, Col } from 'antd';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
  ResponsiveContainer,
} from 'recharts';
import { customTokens } from '@/shared';

const revenueData = [
  { name: '売上', value: 5490175 },
  { name: '仕入', value: 1649815 },
  { name: '粗利', value: 3840360 },
];

const unitPriceData = [
  { name: '売上', value: 53.5 },
  { name: '仕入', value: 16.91 },
  { name: '粗利', value: 32.86 },
  { name: '粗利（当日）', value: 36.6 },
  { name: 'ブロック', value: 33.52 },
];

const gradientMap: Record<string, string> = {
  売上: customTokens.colorInfo, // ブルー
  仕入: customTokens.chartRed, // レッド
  粗利: customTokens.colorSuccess, // グリーン
  '粗利（当日）': customTokens.colorSuccess, // グリーン（統一）
  ブロック: customTokens.colorWarning, // オレンジ
};

interface BarDatum {
  name: string;
  value: number;
}
const generateGradients = (data: BarDatum[], prefix: string) =>
  data.map((item: BarDatum) => {
    const gradId = `${prefix}${item.name}`;
    const topColor = gradientMap[item.name] || '#999';
    return (
      <linearGradient key={gradId} id={gradId} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={topColor} stopOpacity={1} />
        <stop offset="60%" stopColor={topColor} stopOpacity={0.9} />
        <stop offset="100%" stopColor="#ffffff" stopOpacity={0.8} />
      </linearGradient>
    );
  });

const getGradientId = (prefix: string, name: string) => `url(#${prefix}${name})`;

const RevenueChartPanel: React.FC = () => {
  return (
    <Card title="収益グラフ" className="dashboard-card" variant="outlined">
      <Row gutter={24}>
        {/* 売上・仕入・粗利 */}
        <Col span={12}>
          <h4 style={{ marginBottom: 12 }}>売上・仕入・粗利</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueData}>
              <defs>{generateGradients(revenueData, 'gradRev')}</defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis
                tick={{ fontSize: 14 }}
                tickFormatter={(value: number) => {
                  const num = typeof value === 'number' ? value : Number(value) || 0;
                  return (num / 1_000_000).toFixed(2);
                }}
                label={{
                  value: '単位：百万円',
                  angle: -90,
                  position: 'insideLeft',
                  offset: -10,
                  style: { fontSize: 12 },
                }}
              />
              <Tooltip />
              <Bar
                dataKey="value"
                shape={(props: unknown) => {
                  const p = props as {
                    x?: number;
                    y?: number;
                    width?: number;
                    height?: number;
                    payload?: BarDatum;
                  };
                  const { x = 0, y = 0, width = 0, height = 0, payload } = p;
                  return (
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill={getGradientId('gradRev', payload?.name ?? '')}
                      rx={4}
                      ry={4}
                    />
                  );
                }}
              >
                <LabelList
                  dataKey="value"
                  position="top"
                  style={{ fontSize: 16, fontWeight: 600, fill: '#111' }}
                  formatter={(label: unknown) => {
                    const num = typeof label === 'number' ? label : Number(label) || 0;
                    // 表示を百万単位（百万円）にして小数点2桁
                    return `${(num / 1_000_000).toFixed(2)} 百万円`;
                  }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Col>

        {/* 単価 */}
        <Col span={12}>
          <h4 style={{ marginBottom: 12 }}>単価</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={unitPriceData}>
              <defs>{generateGradients(unitPriceData, 'gradUnit')}</defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                interval={0}
                tick={(tickProps: {
                  x?: number;
                  y?: number;
                  payload?: { value?: string; payload?: { name?: string } };
                }) => {
                  const { x, y, payload } = tickProps || {};
                  const label = payload?.value ?? payload?.payload?.name ?? '';
                  // '粗利（当日）' を '粗利' と '（当日）' に分割して2行表示
                  const xx = x ?? 0;
                  const yy = y ?? 0;
                  if (typeof label === 'string' && label.includes('（')) {
                    const parts = label.split(/(?=（)/);
                    return (
                      <g>
                        <text x={xx} y={yy + 6} textAnchor="middle" fill="#000" fontSize={12}>
                          <tspan x={xx} dy={0}>
                            {parts[0]}
                          </tspan>
                          <tspan x={xx} dy={14}>
                            {parts[1]}
                          </tspan>
                        </text>
                      </g>
                    );
                  }

                  return (
                    <text x={xx} y={yy + 6} textAnchor="middle" fill="#000" fontSize={12}>
                      {label}
                    </text>
                  );
                }}
              />
              <YAxis tick={{ fontSize: 13 }} />
              <Tooltip />
              <Bar
                dataKey="value"
                shape={(props: unknown) => {
                  const p = props as {
                    x?: number;
                    y?: number;
                    width?: number;
                    height?: number;
                    payload?: BarDatum;
                  };
                  const { x = 0, y = 0, width = 0, height = 0, payload } = p;
                  return (
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill={getGradientId('gradUnit', payload?.name ?? '')}
                      rx={4}
                      ry={4}
                    />
                  );
                }}
              >
                <LabelList
                  dataKey="value"
                  position="top"
                  style={{ fontSize: 14, fontWeight: 600, fill: '#111' }}
                  formatter={(label: unknown) => {
                    const num = typeof label === 'number' ? label : Number(label) || 0;
                    return `${num.toLocaleString()} 円`;
                  }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Col>
      </Row>
    </Card>
  );
};

export default RevenueChartPanel;
