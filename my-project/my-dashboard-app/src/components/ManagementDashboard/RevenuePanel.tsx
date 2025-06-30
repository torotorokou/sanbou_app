// src/components/ManagementDashboard/RevenueChartPanel.tsx
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

const revenueData = [
    { name: '売上', value: 5490175 },
    { name: '仕入', value: 1649815 },
    { name: '粗利', value: 3840360 },
];

const unitPriceData = [
    { name: '売上単価', value: 53.5 },
    { name: '仕入単価', value: 16.91 },
    { name: '粗利単価', value: 32.86 },
    { name: '粗利単価（当日）', value: 36.6 },
    { name: 'ブロック単価', value: 33.52 },
];

const RevenueChartPanel: React.FC = () => {
    return (
        <Card title="📊 収益グラフ" style={{ marginTop: 24 }}>
            <Row gutter={24}>
                {/* 左：売上・仕入・粗利 */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>💰 売上・仕入・粗利</h4>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={revenueData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="value" fill="#1890ff">
                                <LabelList
                                    dataKey="value"
                                    position="top"
                                    formatter={(v) =>
                                        `${v.toLocaleString()} 円`
                                    }
                                />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </Col>

                {/* 右：単価 */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>📈 単価</h4>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={unitPriceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="value" fill="#faad14">
                                <LabelList
                                    dataKey="value"
                                    position="top"
                                    formatter={(v) =>
                                        `${v.toLocaleString()} 円`
                                    }
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
