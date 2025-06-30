import React from 'react';
import { Card, Row, Col } from 'antd';
import AnimatedStatistic from '../Utils/AnimatedStatistic';
import DiffIndicator from '../Utils/DiffIndicator';
import { InboxOutlined } from '@ant-design/icons';

const ProcessVolumePanel: React.FC = () => {
    const items = [
        { title: '有価物', value: 13800, diff: 800 },
        { title: 'スクラップ（当日）', value: 4260, diff: -220 },
        { title: 'スクラップ（月間）', value: 22800, diff: 1120 },
        { title: 'シュレッダー', value: 17320, diff: 0 },
        { title: '選別（搬入重量）', value: 20450, diff: -500 },
    ];

    return (
        <Card title="⚙️ 工程別処理量" style={{ marginTop: 24 }}>
            <Row gutter={16} justify="space-between">
                {items.map((item, index) => (
                    <Col key={index} span={Math.floor(24 / items.length)}>
                        <AnimatedStatistic
                            title={item.title}
                            value={item.value}
                            suffix="kg"
                            // prefix={<InboxOutlined />}
                            color={item.color}
                        />
                        <div style={{ marginTop: 4, textAlign: 'center' }}>
                            <DiffIndicator diff={item.diff} unit="kg" />
                        </div>
                    </Col>
                ))}
            </Row>
        </Card>
    );
};

export default ProcessVolumePanel;
