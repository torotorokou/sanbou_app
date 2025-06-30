import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const ProcessVolumePanel: React.FC = () => {
    return (
        <Card title="⚙️ 工程別処理量">
            <Title level={5}>各工程の処理量状況</Title>
            <Paragraph>工程ごとの棒グラフなどをここに表示します。</Paragraph>
        </Card>
    );
};

export default ProcessVolumePanel;
