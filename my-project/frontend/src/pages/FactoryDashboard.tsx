import React from 'react';
import { Card, Typography, Row, Col } from 'antd';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    Legend,
    ResponsiveContainer,
    AreaChart, // ✅ 追加
    Area, // ✅ 追加
} from 'recharts';
import { factoryChartColors } from '../theme';

const { Title, Paragraph } = Typography;

// ✅ 時間帯別 搬入量
const hourlyInData = [
    { time: '7:00', amount: 2.1 },
    { time: '8:00', amount: 3.2 },
    { time: '9:00', amount: 5.8 },
    { time: '10:00', amount: 4.1 },
    { time: '11:00', amount: 6.5 },
    { time: '12:00', amount: 2.4 },
    { time: '13:00', amount: 5.2 },
    { time: '14:00', amount: 4.8 },
    { time: '15:00', amount: 3.9 },
    { time: '16:00', amount: 2.6 },
    { time: '17:00', amount: 2.0 },
    { time: '18:00', amount: 1.5 },
];

// ✅ 車種別 搬入割合（時間帯別）
const vehicleByHourData = [
    { time: '7:00', 軽トラ: 2, '2t車': 3, '4t車': 1, 大型車: 0 },
    { time: '8:00', 軽トラ: 1, '2t車': 4, '4t車': 2, 大型車: 1 },
    { time: '9:00', 軽トラ: 3, '2t車': 2, '4t車': 2, 大型車: 0 },
    { time: '10:00', 軽トラ: 2, '2t車': 3, '4t車': 3, 大型車: 1 },
    { time: '11:00', 軽トラ: 2, '2t車': 2, '4t車': 1, 大型車: 2 },
    { time: '12:00', 軽トラ: 1, '2t車': 2, '4t車': 0, 大型車: 1 },
    { time: '13:00', 軽トラ: 2, '2t車': 3, '4t車': 2, 大型車: 1 },
    { time: '14:00', 軽トラ: 2, '2t車': 2, '4t車': 2, 大型車: 2 },
    { time: '15:00', 軽トラ: 3, '2t車': 1, '4t車': 2, 大型車: 0 },
    { time: '16:00', 軽トラ: 2, '2t車': 2, '4t車': 1, 大型車: 1 },
    { time: '17:00', 軽トラ: 1, '2t車': 2, '4t車': 1, 大型車: 1 },
    { time: '18:00', 軽トラ: 1, '2t車': 1, '4t車': 0, 大型車: 0 },
];

// ✅ 品目別 搬入量（積み上げ棒）
const itemBreakdownData = [
    { time: '7:00', 可燃ごみ: 0.8, 木くず: 0.5, 金属: 0.7 },
    { time: '8:00', 可燃ごみ: 1.2, 木くず: 0.8, 金属: 1.2 },
    { time: '9:00', 可燃ごみ: 2.0, 木くず: 1.5, 金属: 2.3 },
    { time: '10:00', 可燃ごみ: 1.8, 木くず: 1.0, 金属: 1.3 },
    { time: '11:00', 可燃ごみ: 2.5, 木くず: 1.2, 金属: 2.8 },
    { time: '12:00', 可燃ごみ: 1.0, 木くず: 0.6, 金属: 0.8 },
    { time: '13:00', 可燃ごみ: 2.2, 木くず: 1.3, 金属: 1.7 },
    { time: '14:00', 可燃ごみ: 1.7, 木くず: 1.1, 金属: 1.0 },
    { time: '15:00', 可燃ごみ: 1.9, 木くず: 1.0, 金属: 1.4 },
    { time: '16:00', 可燃ごみ: 1.5, 木くず: 0.9, 金属: 0.6 },
    { time: '17:00', 可燃ごみ: 1.2, 木くず: 0.6, 金属: 0.9 },
    { time: '18:00', 可燃ごみ: 0.9, 木くず: 0.4, 金属: 0.5 },
];

const FactoryDashboard: React.FC = () => {
    return (
        <div style={{ padding: '24px' }}>
            <Card
                title='🏭 工場管理ダッシュボード'
                bordered={false}
                style={{ marginBottom: 24 }}
            >
                <Title level={5}>搬入分析ダッシュボード</Title>
                <Paragraph>
                    時間帯別の搬入量、車種割合、品目内訳を視覚的に表示します。
                </Paragraph>
            </Card>

            <Row gutter={[24, 24]}>
                {/* 時間帯別搬入量 */}
                <Col span={24}>
                    <Card title='⏰ 時間帯ごとの搬入量'>
                        <ResponsiveContainer width='30%' height={250}>
                            <BarChart data={hourlyInData}>
                                <XAxis dataKey='time' />
                                <YAxis unit='t' />
                                <Tooltip />
                                <Bar dataKey='amount' fill={factoryChartColors.revenue} />
                            </BarChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>

                {/* 時間帯別 車種割合（100% stacked） */}
                <Col span={24}>
                    <Card title='🚛 時間帯ごとの車種割合（100%積み上げ・面グラフ）'>
                        <ResponsiveContainer width='30%' height={300}>
                            <AreaChart
                                data={vehicleByHourData}
                                stackOffset='expand'
                                margin={{
                                    top: 20,
                                    right: 30,
                                    left: 0,
                                    bottom: 0,
                                }}
                            >
                                <XAxis dataKey='time' />
                                <YAxis
                                    tickFormatter={(v: any) =>
                                        `${(Number(v) * 100).toFixed(0)}%`
                                    }
                                />
                                <Tooltip
                                    formatter={(v: any) =>
                                        `${(Number(v) * 100).toFixed(1)}%`
                                    }
                                />
                                <Legend />
                                <Area
                                    type='monotone'
                                    dataKey='軽トラ'
                                    stackId='1'
                                    stroke={factoryChartColors.revenue}
                                    fill={factoryChartColors.revenue}
                                />
                                <Area
                                    type='monotone'
                                    dataKey='2t車'
                                    stackId='1'
                                    stroke={factoryChartColors.info}
                                    fill={factoryChartColors.info}
                                />
                                <Area
                                    type='monotone'
                                    dataKey='4t車'
                                    stackId='1'
                                    stroke={factoryChartColors.warning}
                                    fill={factoryChartColors.warning}
                                />
                                <Area
                                    type='monotone'
                                    dataKey='大型車'
                                    stackId='1'
                                    stroke={factoryChartColors.error}
                                    fill={factoryChartColors.error}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>

                {/* 品目別 搬入量 */}
                <Col span={24}>
                    <Card title='📦 品目別の搬入量（時間帯内訳）'>
                        <ResponsiveContainer width='30%' height={280}>
                            <BarChart data={itemBreakdownData}>
                                <XAxis dataKey='time' />
                                <YAxis unit='t' />
                                <Tooltip />
                                <Legend />
                                <Bar
                                    dataKey='可燃ごみ'
                                    stackId='a'
                                    fill={factoryChartColors.error}
                                />
                                <Bar
                                    dataKey='木くず'
                                    stackId='a'
                                    fill={factoryChartColors.info}
                                />
                                <Bar
                                    dataKey='金属'
                                    stackId='a'
                                    fill={factoryChartColors.profit}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default FactoryDashboard;
