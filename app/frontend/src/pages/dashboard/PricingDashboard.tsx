import React from 'react';
import { Row, Col, Card, Typography } from 'antd';
import {
    DollarCircleOutlined,
    UserOutlined,
    ShoppingCartOutlined,
    TeamOutlined,
    BarChartOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

const PricingDashboard: React.FC = () => {
    return (
        <div style={{ padding: 24 }}>
            <Title level={3}>単価分析ダッシュボード</Title>
            <Row gutter={[16, 16]}>
                {/* ✅ 全体平均単価 */}
                <Col xs={24} md={12} lg={8}>
                    <Card
                        title='全体平均単価'
                        extra={<DollarCircleOutlined />}
                        hoverable
                    >
                        <Text>直近月：¥10.5 / kg</Text>
                        <br />
                        <Text type='secondary'>
                            利益率変化や値下がり傾向の確認
                        </Text>
                    </Card>
                </Col>

                {/* ✅ 商品別単価 */}
                <Col xs={24} md={12} lg={8}>
                    <Card
                        title='商品別単価'
                        extra={<ShoppingCartOutlined />}
                        hoverable
                    >
                        <Text>高単価商品を重点分析・販売強化</Text>
                        <br />
                        <Text type='secondary'>
                            例：A商品 ¥12/kg、B商品 ¥8/kg
                        </Text>
                    </Card>
                </Col>

                {/* ✅ 営業者別単価 */}
                <Col xs={24} md={12} lg={8}>
                    <Card
                        title='営業者別単価'
                        extra={<TeamOutlined />}
                        hoverable
                    >
                        <Text>営業ごとの値引傾向・交渉力の評価</Text>
                        <br />
                        <Text type='secondary'>
                            例：営業A ¥11/kg、営業B ¥9/kg
                        </Text>
                    </Card>
                </Col>

                {/* ✅ 顧客別単価 */}
                <Col xs={24} md={12} lg={8}>
                    <Card title='顧客別単価' extra={<UserOutlined />} hoverable>
                        <Text>値引きが過剰な顧客を把握し戦略調整</Text>
                        <br />
                        <Text type='secondary'>例：顧客X ¥13/kg、Y ¥7/kg</Text>
                    </Card>
                </Col>

                {/* ✅ 商品 × 営業別単価 */}
                <Col xs={24} md={12} lg={8}>
                    <Card
                        title='商品×営業別単価'
                        extra={<BarChartOutlined />}
                        hoverable
                    >
                        <Text>戦略・スキルの違いによる単価差を分析</Text>
                        <br />
                        <Text type='secondary'>
                            営業A × 商品B：¥10 / 営業B × 商品B：¥8.5
                        </Text>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default PricingDashboard;
