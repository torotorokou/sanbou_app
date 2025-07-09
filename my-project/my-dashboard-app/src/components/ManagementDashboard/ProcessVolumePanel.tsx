import React from 'react';
import { Card, Row, Col } from 'antd';
import StatisticCard from '../ui/StatisticCard';

const ProcessVolumePanel: React.FC = () => {
    const items = [
        { title: '有価物', value: 13800, diff: 800 },
        { title: 'スクラップ\n（当日）', value: 4260, diff: -220 },
        { title: 'スクラップ\n（月間）', value: 22800, diff: 1120 },
        { title: 'シュレッダー', value: 17320, diff: 0 },
        { title: '選別\n（搬入重量）', value: 20450, diff: -500 },
    ];

    return (
        <Card title='⚙️ 工程別処理量' style={{ height: '100%', marginTop: 24 }}>
            <Row gutter={0} justify='space-between'>
                {items.map((item, index) => (
                    <Col key={index} span={Math.floor(24 / items.length)}>
                        <StatisticCard
                            title={item.title}
                            value={item.value}
                            diff={item.diff}
                            suffix='kg'
                            // prefix={<InboxOutlined />}
                        />
                    </Col>
                ))}
            </Row>
        </Card>
    );
};

export default ProcessVolumePanel;
