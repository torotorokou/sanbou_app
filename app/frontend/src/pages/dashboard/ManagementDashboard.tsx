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
    // 全体をビューポート高さに合わせ、パディング分を差し引いて縦スクロールを抑える
    return (
        <div style={{ padding: 16, height: 'calc(100vh - 32px)' }}>
            <Title level={3} style={{ marginBottom: 12 }}>
                2025年6月27日 実績ダッシュボード
            </Title>

            <Row gutter={[16, 16]} style={{ height: 'calc(100% - 56px)' }}>
                {/* ✅ 左側 全体 */}
                <Col xs={24} lg={12} style={{ height: '100%' }}>
                    <Row gutter={[16, 16]} style={{ height: '100%' }}>
                        {/* ✅ 左上 */}
                        <Col span={24} style={{ height: '50%' }}>
                            <div style={{ height: '100%' }}>
                                <SummaryPanel />
                            </div>
                        </Col>

                        {/* ✅ 左下 */}
                        <Col span={24} style={{ height: '50%' }}>
                            <div style={{ height: '100%' }}>
                                <RevenuePanel />
                            </div>
                        </Col>
                    </Row>
                </Col>

                {/* ✅ 右側 全体 */}
                <Col xs={24} lg={12} style={{ height: RIGHT_HEIGHT }}>
                    <Row gutter={[16, 16]} style={{ height: '100%' }}>
                        {/* ✅ 右上（拡大） */}
                        <Col span={24} style={{ height: '40%' }}>
                            <div style={{ height: '100%' }}>
                                <CustomerAnalysis />
                            </div>
                        </Col>

                        {/* ✅ 右中（縮小: 約0.9倍） */}
                        <Col span={24} style={{ height: '30%' }}>
                            <div style={{ height: '100%' }}>
                                <ProcessVolumePanel />
                            </div>
                        </Col>

                        {/* ✅ 右下（縮小: 約0.9倍） */}
                        <Col span={24} style={{ height: '30%' }}>
                            <div style={{ height: '100%' }}>
                                <BlockCountPanel />
                            </div>
                        </Col>
                    </Row>
                </Col>
            </Row>
        </div>
    );
};

export default ManagementDashboard;
