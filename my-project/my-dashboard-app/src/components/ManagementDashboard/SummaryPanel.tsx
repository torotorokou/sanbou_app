import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const SummaryPanel: React.FC = () => {
    return (
        <Card title="🚛 搬入サマリー">
            <Title level={5}>今月の搬入概要</Title>
            <Paragraph>ここに搬入に関する統計情報などを表示します。</Paragraph>
        </Card>
    );
};

export default SummaryPanel;
