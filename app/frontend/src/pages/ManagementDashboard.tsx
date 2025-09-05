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
const RIGHT_HEIGHT = '100%'; // 右側全体の高さを固定
const ManagementDashboard: React.FC = () => {
    return (
        <div style={{ padding: 16 }}>
            <Title level={3} style={{ marginBottom: 12 }}>
                2025年6月27日 実績ダッシュボード
            </Title>

            <Row gutter={[16, 16]}>
                {/* ✅ 左側 全体 */}
                <Col xs={24} lg={12}>
                    <Row gutter={[16, 16]}>
                        {/* ✅ 左上 */}
                        <Col span={24} style={{ height: '100%' }}>
                            <SummaryPanel />
                        </Col>

                        {/* ✅ 左下 */}
                        <Col span={24} style={{ height: '100%' }}>
                            <RevenuePanel />
                        </Col>
                    </Row>
                </Col>

                {/* ✅ 右側 全体 */}
                <Col xs={24} lg={12} style={{ height: RIGHT_HEIGHT }}>
                    <Row gutter={[16, 16]} style={{ height: '100%' }}>
                        {/* ✅ 右上（1/3） */}
                        <Col span={24} style={{ height: '33.33%' }}>
                            <CustomerAnalysis />
                        </Col>

                        {/* ✅ 右中（1/3） */}
                        <Col span={24} style={{ height: '33.33%' }}>
                            <ProcessVolumePanel />
                        </Col>

                        {/* ✅ 右下（1/3） */}
                        <Col span={24} style={{ height: '33.33%' }}>
                            <BlockCountPanel />
                        </Col>
                    </Row>
                </Col>
            </Row>
        </div>
    );
};

export default ManagementDashboard;
