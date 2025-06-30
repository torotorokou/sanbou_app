// src/pages/ManagementDashboard.tsx
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

const ManagementDashboard: React.FC = () => {
    return (
        <div style={{ padding: 16 }}>
            <Title level={3} style={{ marginBottom: 24 }}>
                2025年6月27日 実績ダッシュボード
            </Title>
            <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                    <SummaryPanel />
                </Col>
                <Col xs={24} lg={12}>
                    <CustomerAnalysis />
                </Col>
                <Col xs={24} lg={12}>
                    <RevenuePanel />
                </Col>
                <Col xs={24} lg={12}>
                    <div
                        style={{
                            height: 400,
                            display: 'flex',
                            flexDirection: 'column',
                        }}
                    >
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                            <ProcessVolumePanel />
                        </div>
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                            <BlockCountPanel />
                        </div>
                    </div>
                </Col>
            </Row>
        </div>
    );
};

export default ManagementDashboard;
