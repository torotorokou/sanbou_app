import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const RevenuePanel: React.FC = () => {
    return (
        <Card title="💰 収益パネル">
            <Title level={5}>売上・利益推移</Title>
            <Paragraph>収益に関するチャートを表示します。</Paragraph>
        </Card>
    );
};

export default RevenuePanel;
