// src/pages/FactoryDashboard.tsx
import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const FactoryDashboard: React.FC = () => {
    return (
        <Card title="🏭 工場管理ダッシュボード">
            <Title level={5}>管理対象：処理ブロック・日報・収支表 等</Title>
            <Paragraph>
                このページでは工場の処理状況を集計・表示・帳票出力できます。
            </Paragraph>
        </Card>
    );
};

export default FactoryDashboard;
