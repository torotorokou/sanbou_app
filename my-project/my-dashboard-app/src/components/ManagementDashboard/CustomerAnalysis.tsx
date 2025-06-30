// src/components/ManagementDashboard/CustomerAnalysisPanel.tsx
import React from 'react';
import { Card, Row, Col } from 'antd';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = [
    '#1890ff',
    '#13c2c2',
    '#52c41a',
    '#faad14',
    '#f5222d',
    '#722ed1',
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
    { name: CATEGORIES[3], value: 48 },
    { name: CATEGORIES[4], value: 0 },
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
                <span style={{ fontSize: 14 }}>{name}</span>
            </div>
        ))}
    </div>
);

const renderPieChart = (data: any[]) => (
    <ResponsiveContainer width="100%" height={250}>
        <PieChart>
            <Pie
                startAngle={90}
                endAngle={-270}
                data={data}
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
                dataKey="value"
            >
                {data.map((entry, index) => (
                    <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                    />
                ))}
            </Pie>
            <Tooltip />
        </PieChart>
    </ResponsiveContainer>
);

const CustomerAnalysisPanel: React.FC = () => {
    return (
        <Card title="👥 顧客分析" style={{ height: '100%' }}>
            <Row gutter={24}>
                {/* 凡例 */}
                <Col span={6}>
                    <h4 style={{ marginBottom: 12 }}>凡例</h4>
                    {renderLegend()}
                </Col>

                {/* 搬入量（円グラフ） */}
                <Col span={9}>
                    <h4 style={{ marginBottom: 12 }}>搬入量（kg）</h4>
                    {renderPieChart(weightData)}
                </Col>

                {/* 搬入台数（円グラフ） */}
                <Col span={9}>
                    <h4 style={{ marginBottom: 12 }}>搬入台数（台）</h4>
                    {renderPieChart(countData)}
                </Col>
            </Row>
        </Card>
    );
};

export default CustomerAnalysisPanel;
