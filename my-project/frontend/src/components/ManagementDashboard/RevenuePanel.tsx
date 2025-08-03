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
import { customTokens } from '@/theme/tokens';

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
    売上: customTokens.colorInfo,      // ブルー
    仕入: customTokens.chartRed,       // レッド
    粗利: customTokens.colorSuccess,   // グリーン
    '粗利（当日）': customTokens.colorSuccess, // グリーン（統一）
    ブロック: customTokens.colorWarning, // オレンジ
};

const generateGradients = (data: any[], prefix: string) =>
    data.map((item: any) => {
        const gradId = `${prefix}${item.name}`;
        const topColor = gradientMap[item.name] || '#999';
        return (
            <linearGradient
                key={gradId}
                id={gradId}
                x1='0'
                y1='0'
                x2='0'
                y2='1'
            >
                <stop offset='0%' stopColor={topColor} stopOpacity={1} />
                <stop offset='60%' stopColor={topColor} stopOpacity={0.9} />
                <stop offset='100%' stopColor='#ffffff' stopOpacity={0.8} />
            </linearGradient>
        );
    });

const getGradientId = (prefix: string, name: string) =>
    `url(#${prefix}${name})`;

const RevenueChartPanel: React.FC = () => {
    return (
        <Card title='収益グラフ' style={{ marginTop: 24 }} variant='outlined'>
            <Row gutter={24}>
                {/* 売上・仕入・粗利 */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>売上・仕入・粗利</h4>
                    <ResponsiveContainer width='100%' height={300}>
                        <BarChart data={revenueData}>
                            <defs>
                                {generateGradients(revenueData, 'gradRev')}
                            </defs>
                            <CartesianGrid strokeDasharray='3 3' />
                            <XAxis dataKey='name' />
                            <YAxis />
                            <Tooltip />
                            <Bar
                                dataKey='value'
                                shape={({ x, y, width, height, payload }) => (
                                    <rect
                                        x={x}
                                        y={y}
                                        width={width}
                                        height={height}
                                        fill={getGradientId(
                                            'gradRev',
                                            payload.name
                                        )}
                                        rx={4}
                                        ry={4}
                                    />
                                )}
                            >
                                <LabelList
                                    dataKey='value'
                                    position='top'
                                    formatter={(v) =>
                                        `${v.toLocaleString()} 円`
                                    }
                                />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </Col>

                {/* 単価 */}
                <Col span={12}>
                    <h4 style={{ marginBottom: 12 }}>単価</h4>
                    <ResponsiveContainer width='100%' height={300}>
                        <BarChart data={unitPriceData}>
                            <defs>
                                {generateGradients(unitPriceData, 'gradUnit')}
                            </defs>
                            <CartesianGrid strokeDasharray='3 3' />
                            <XAxis
                                dataKey='name'
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
                                dataKey='value'
                                shape={({ x, y, width, height, payload }) => (
                                    <rect
                                        x={x}
                                        y={y}
                                        width={width}
                                        height={height}
                                        fill={getGradientId(
                                            'gradUnit',
                                            payload.name
                                        )}
                                        rx={4}
                                        ry={4}
                                    />
                                )}
                            >
                                <LabelList
                                    dataKey='value'
                                    position='top'
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
