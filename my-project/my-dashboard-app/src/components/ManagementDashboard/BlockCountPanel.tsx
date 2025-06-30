import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const BlockCountPanel: React.FC = () => {
    return (
        <Card title="📦 ブロック数状況">
            <Title level={5}>稼働中ブロック</Title>
            <Paragraph>ブロック単位の処理数などを表示します。</Paragraph>
        </Card>
    );
};

export default BlockCountPanel;
