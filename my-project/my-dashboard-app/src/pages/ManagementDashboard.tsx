import React from 'react';
import { Row, Col, Typography } from 'antd';
import {
    SummaryPanel,
    CustomerAnalysis,
    RevenuePanel,
    BlockCountPanel,
    ProcessVolumePanel,
} from '@/components/ManagementDashboard';

const { Title } = Typography;

const PANEL_HEIGHT = 420; // 統一高さ：今後変更しやすい
const ManagementDashboard: React.FC = () => {
    return (
        <div style={{ padding: 16 }}>
            <Title level={3} style={{ marginBottom: 12 }}>
                2025年6月27日 実績ダッシュボード
            </Title>

            <Row gutter={[16, 16]}>
                <Col xs={24} lg={12} style={{ height: PANEL_HEIGHT }}>
                    <SummaryPanel />
                </Col>
                <Col xs={24} lg={12} style={{ height: PANEL_HEIGHT }}>
                    <CustomerAnalysis />
                </Col>
                <Col xs={24} lg={12} style={{ height: PANEL_HEIGHT }}>
                    <RevenuePanel />
                </Col>
                <Col xs={24} lg={12} style={{ height: PANEL_HEIGHT }}>
                    <Row gutter={[16, 16]} style={{ height: '100%' }}>
                        <Col span={24} style={{ height: '50%' }}>
                            <ProcessVolumePanel />
                        </Col>
                        <Col span={24} style={{ height: '50%' }}>
                            <BlockCountPanel />
                        </Col>
                    </Row>
                </Col>
            </Row>
        </div>
    );
};

export default ManagementDashboard;
