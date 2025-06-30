import React from 'react';
import { Card, Row, Col } from 'antd';
import { CarOutlined, InboxOutlined } from '@ant-design/icons';
import AnimatedStatistic from '../ui/AnimatedStatistic';
import DiffIndicator from '../ui/DiffIndicator';
import Sparkline from '../ui/Sparkline';

const SummaryPanel: React.FC = () => {
    const driveData = [
        {
            title: '月間搬入台数',
            value: 1381,
            suffix: '台',
            prefix: <CarOutlined />,
            diff: +52,
            trend: [1200, 1240, 1260, 1290, 1300, 1340, 1381],
        },
        {
            title: '終了台数（当日）',
            value: 120,
            suffix: '台',
            prefix: <CarOutlined />,
            diff: -7,
            trend: [122, 128, 125, 130, 124, 127, 120],
        },
    ];

    const weightData = [
        {
            title: '月間搬入量',
            value: 860330,
            suffix: 'kg',
            prefix: <InboxOutlined />,
            diff: +24500,
            trend: [790000, 805000, 820000, 830000, 845000, 860000, 860330],
        },
        {
            title: '当日搬入量',
            value: 102600,
            suffix: 'kg',
            prefix: <InboxOutlined />,
            diff: +3200,
            trend: [98000, 99000, 99500, 100500, 101000, 102000, 102600],
        },
        {
            title: '当日搬出量',
            value: 127570,
            suffix: 'kg',
            prefix: <InboxOutlined />,
            diff: -8100,
            trend: [130000, 129000, 128000, 128500, 127800, 127000, 127570],
        },
    ];

    return (
        <Card title="🚛 月間搬入サマリー" headStyle={{ fontWeight: 'bold' }}>
            <Row gutter={24}>
                <Col span={12}>
                    <h4>🚚 搬入台数</h4>
                    {driveData.map((item, index) => (
                        <div
                            key={index}
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                marginBottom: 16,
                            }}
                        >
                            {/* 数値・差分 */}
                            <div style={{ flex: 1 }}>
                                <AnimatedStatistic
                                    title={item.title}
                                    value={item.value}
                                    suffix={item.suffix}
                                    prefix={item.prefix}
                                />
                                <div style={{ marginTop: 4 }}>
                                    <DiffIndicator
                                        diff={item.diff}
                                        unit={item.suffix}
                                    />
                                </div>
                            </div>

                            {/* グラフ */}
                            <div style={{ width: 100 }}>
                                <Sparkline data={item.trend} />
                            </div>
                        </div>
                    ))}
                </Col>

                <Col span={12}>
                    <h4>⚖️ 搬入・搬出量</h4>
                    {weightData.map((item, index) => (
                        <div
                            key={index}
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                marginBottom: 16,
                            }}
                        >
                            {/* 数値・差分 */}
                            <div style={{ flex: 1 }}>
                                <AnimatedStatistic
                                    title={item.title}
                                    value={item.value}
                                    suffix={item.suffix}
                                    prefix={item.prefix}
                                />
                                <div style={{ marginTop: 4 }}>
                                    <DiffIndicator
                                        diff={item.diff}
                                        unit={item.suffix}
                                    />
                                </div>
                            </div>

                            {/* グラフ */}
                            <div style={{ width: 100 }}>
                                <Sparkline data={item.trend} />
                            </div>
                        </div>
                    ))}
                </Col>
            </Row>
        </Card>
    );
};

export default SummaryPanel;
