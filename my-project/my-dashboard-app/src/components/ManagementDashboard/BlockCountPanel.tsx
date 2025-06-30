import React from 'react';
import { Card, Row, Col } from 'antd';
import AnimatedStatistic from '../Utils/AnimatedStatistic';
import {
    AppstoreOutlined,
    RiseOutlined,
    FallOutlined,
} from '@ant-design/icons';
import DiffIndicator from '../Utils/DiffIndicator'; // ←追加

const BlockCountPanel: React.FC = () => {
    const blockData = [
        { title: '廃プラ', value: 48, diff: 5 },
        { title: '焼却', value: 32, diff: -3 },
        { title: '破砕', value: 27, diff: 0 },
        { title: '安定', value: 19, diff: 2 },
        { title: 'B', value: 12, diff: -1 },
    ];

    return (
        <Card title="🧱 ブロック数" style={{ marginTop: 24 }}>
            <Row gutter={16} justify="space-between">
                {blockData.map((item, index) => (
                    <Col key={index} span={Math.floor(24 / blockData.length)}>
                        <AnimatedStatistic
                            title={item.title}
                            value={item.value}
                            suffix="個"
                            prefix={<AppstoreOutlined />}
                        />
                        <div style={{ marginTop: 4, textAlign: 'center' }}>
                            <DiffIndicator diff={item.diff} unit="個" />
                        </div>
                    </Col>
                ))}
            </Row>
        </Card>
    );
};

export default BlockCountPanel;
