import React from 'react';
import { Card, Row, Col } from 'antd';
import { CarOutlined, InboxOutlined } from '@ant-design/icons';
import AnimatedStatistic from '../Utils/AnimatedStatistic';

const SummaryPanel: React.FC = () => {
    return (
        <Card title="🚛 月間搬入サマリー" headStyle={{ fontWeight: 'bold' }}>
            <Row gutter={24}>
                {/* 🚚 搬入台数グループ */}
                <Col span={12}>
                    <h4>🚚 搬入台数</h4>
                    <AnimatedStatistic
                        title="月間搬入台数"
                        value={1381}
                        suffix="台"
                        prefix={<CarOutlined />}
                        // color="#1890ff"
                    />
                    <AnimatedStatistic
                        title="終了台数（当日）"
                        value={120}
                        suffix="台"
                        prefix={<CarOutlined />}
                        // color="#3f8600"
                    />
                </Col>

                {/* ⚖️ 搬入・搬出量グループ */}
                <Col span={12}>
                    <h4>⚖️ 搬入・搬出量</h4>
                    <AnimatedStatistic
                        title="月間搬入量"
                        value={860330}
                        suffix="kg"
                        prefix={<InboxOutlined />}
                        // color="#faad14"
                    />
                    <AnimatedStatistic
                        title="当日搬入量"
                        value={102600}
                        suffix="kg"
                        prefix={<InboxOutlined />}
                        // color="#faad14"
                    />
                    <AnimatedStatistic
                        title="当日搬出量"
                        value={127570}
                        suffix="kg"
                        prefix={<InboxOutlined />}
                        // color="#cf1322"
                    />
                </Col>
            </Row>
        </Card>
    );
};

export default SummaryPanel;
