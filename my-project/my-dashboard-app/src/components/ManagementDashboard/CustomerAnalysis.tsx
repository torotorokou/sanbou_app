import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const CustomerAnalysis: React.FC = () => {
    return (
        <Card title="👥 顧客分析">
            <Title level={5}>主要顧客の動向</Title>
            <Paragraph>グラフや分析結果などをここに表示します。</Paragraph>
        </Card>
    );
};

export default CustomerAnalysis;
