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
    { name: '売上\n単価', value: 53.5 },
    { name: '仕入\n単価', value: 16.91 },
    { name: '粗利\n単価', value: 32.86 },
    { name: '粗利\n（当日）', value: 36.6 },
    { name: 'ブロック\n単価', value: 33.52 },
];

const RevenueChartPanel: React.FC = () => {
    return (
        <Card title="📊 収益グラフ" style={{ marginTop: 24 }}>
            <Row gutter={24}>
                {/* ✅ 左：売上・仕入・粗利（グラデーション付き） */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>💰 売上・仕入・粗利</h4>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={revenueData}>
                            <defs>
                                {revenueData.map((_, index) => (
                                    <linearGradient
                                        key={index}
                                        id={`gradRevenue${index}`}
                                        x1="0"
                                        y1="0"
                                        x2="0"
                                        y2="1"
                                    >
                                        <stop
                                            offset="0%"
                                            stopColor="#1890ff"
                                            stopOpacity={1 - index * 0.1}
                                        />
                                        <stop
                                            offset="100%"
                                            stopColor="#91d5ff"
                                            stopOpacity={0.6 + index * 0.1}
                                        />
                                    </linearGradient>
                                ))}
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Bar
                                dataKey="value"
                                shape={(props) => {
                                    const { x, y, width, height, index } =
                                        props;
                                    return (
                                        <rect
                                            x={x}
                                            y={y}
                                            width={width}
                                            height={height}
                                            fill={`url(#gradRevenue${index})`}
                                            rx={4}
                                            ry={4}
                                        />
                                    );
                                }}
                            >
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

                {/* ✅ 右：単価（グラデーション付き） */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>📈 単価</h4>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={unitPriceData}>
                            <defs>
                                {unitPriceData.map((_, index) => (
                                    <linearGradient
                                        key={index}
                                        id={`gradUnit${index}`}
                                        x1="0"
                                        y1="0"
                                        x2="0"
                                        y2="1"
                                    >
                                        <stop
                                            offset="0%"
                                            stopColor="#faad14"
                                            stopOpacity={1 - index * 0.1}
                                        />
                                        <stop
                                            offset="100%"
                                            stopColor="#fadb14"
                                            stopOpacity={0.5 + index * 0.1}
                                        />
                                    </linearGradient>
                                ))}
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="name"
                                interval={0}
                                tick={{
                                    fontSize: 12,
                                    whiteSpace: 'pre-line',
                                    lineHeight: 1.2,
                                }}
                            />
                            <YAxis />
                            <Tooltip />
                            <Bar
                                dataKey="value"
                                shape={(props) => {
                                    const { x, y, width, height, index } =
                                        props;
                                    return (
                                        <rect
                                            x={x}
                                            y={y}
                                            width={width}
                                            height={height}
                                            fill={`url(#gradUnit${index})`}
                                            rx={4}
                                            ry={4}
                                        />
                                    );
                                }}
                            >
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
