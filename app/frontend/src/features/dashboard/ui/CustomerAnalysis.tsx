// src/components/ManagementDashboard/CustomerAnalysisPanel.tsx
import React from 'react';
import { Card, Row, Col } from 'antd';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { customTokens } from '@/shared';

const COLORS = [
  customTokens.chartGreen,
  customTokens.chartBlue,
  customTokens.chartPurple,
  customTokens.chartOrange,
  customTokens.chartRed,
  customTokens.colorNeutral,
];

const CATEGORIES = [
  'A客（事業系）',
  'B客（移転・残置）',
  'C客（解体）',
  'D客（建設）',
  'E客（中間・積保）',
  'F客（その他）',
];

const weightData = [
  { name: CATEGORIES[0], value: 18260 },
  { name: CATEGORIES[1], value: 28830 },
  { name: CATEGORIES[2], value: 6290 },
  { name: CATEGORIES[3], value: 0 },
  { name: CATEGORIES[4], value: 44920 },
  { name: CATEGORIES[5], value: 4300 },
];

const countData = [
  { name: CATEGORIES[0], value: 24 },
  { name: CATEGORIES[1], value: 43 },
  { name: CATEGORIES[2], value: 14 },
  { name: CATEGORIES[3], value: 0 },
  { name: CATEGORIES[4], value: 48 },
  { name: CATEGORIES[5], value: 6 },
];

const renderLegend = () => (
  <div style={{ paddingTop: 12 }}>
    {CATEGORIES.map((name, index) => (
      <div
        key={index}
        style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <div
          style={{
            width: 12,
            height: 12,
            backgroundColor: COLORS[index % COLORS.length],
            marginRight: 8,
            borderRadius: '50%',
          }}
        />
        <span style={{ fontSize: 12 }}>{name}</span>
      </div>
    ))}
  </div>
);
const PIE_HEIGHT = 200; // グラフエリアを大きく

interface PieDatum {
  name: string;
  value: number;
}
const renderPieChart = (data: PieDatum[]) => (
  <ResponsiveContainer width="100%" height={PIE_HEIGHT}>
    <PieChart>
      <Pie
        data={data}
        cx="50%"
        cy="50%"
        outerRadius={80}
        innerRadius={50}
        dataKey="value"
        startAngle={90}
        endAngle={-270}
        label={(rawProps: {
          value?: number | string;
          cx?: number | string;
          cy?: number | string;
          midAngle?: number;
          innerRadius?: number | string;
          outerRadius?: number | string;
        }) => {
          // Recharts の型が厳密でないため安全に取り出して数値化
          const value = Number(rawProps?.value ?? 0);
          const cxNum = Number(rawProps?.cx ?? 0);
          const cyNum = Number(rawProps?.cy ?? 0);
          const midAngle = Number(rawProps?.midAngle ?? 0);
          const innerRadius = Number(rawProps?.innerRadius ?? 0);
          const outerRadius = Number(rawProps?.outerRadius ?? 0);

          const RADIAN = Math.PI / 180;
          const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
          const x = cxNum + radius * Math.cos(-midAngle * RADIAN);
          const y = cyNum + radius * Math.sin(-midAngle * RADIAN);

          const display = value.toLocaleString();
          const paddingX = 8;
          const paddingY = 4;
          const fontSize = 14;

          return (
            <g>
              <rect
                x={x - display.length * fontSize * 0.32 - paddingX / 2}
                y={y - fontSize / 2 - paddingY / 2}
                width={display.length * fontSize * 0.64 + paddingX}
                height={fontSize + paddingY}
                rx={6}
                fill="rgba(255, 255, 255, 0.8)"
              />
              <text x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize={fontSize}>
                {display}
              </text>
            </g>
          );
        }}
        labelLine={false}
      >
        {data.map((entry, idx) => (
          <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
        ))}
      </Pie>

      <Tooltip />
    </PieChart>
  </ResponsiveContainer>
);

const CustomerAnalysisPanel: React.FC = () => {
  return (
    <Card title="👥 顧客分析" className="dashboard-card">
      <Row gutter={24}>
        {/* 凡例 */}
        <Col span={8}>
          <h4 style={{ marginBottom: 12 }}>凡例</h4>
          {renderLegend()}
        </Col>

        {/* 搬入量（円グラフ） */}
        <Col span={8}>
          <h4 style={{ marginBottom: 12 }}>搬入量（kg）</h4>
          {renderPieChart(weightData)}
        </Col>

        {/* 搬入台数（円グラフ） */}
        <Col span={8}>
          <h4 style={{ marginBottom: 12 }}>搬入台数（台）</h4>
          {renderPieChart(countData)}
        </Col>
      </Row>
    </Card>
  );
};

export default CustomerAnalysisPanel;
