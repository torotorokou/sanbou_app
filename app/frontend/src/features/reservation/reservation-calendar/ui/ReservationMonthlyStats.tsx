/**
 * ReservationMonthlyStats - 月次予約統計グラフ
 * 
 * UI Component (状態レス)
 * カレンダーの下に表示する月次統計
 */

import React from 'react';
import { Card, Row, Col, Statistic, Typography } from 'antd';
import { TruckOutlined, TeamOutlined } from '@ant-design/icons';
import type { ReservationForecastDaily } from '../../shared';

const { Text } = Typography;

interface ReservationMonthlyStatsProps {
  data: ReservationForecastDaily[];
  isLoading?: boolean;
}

export const ReservationMonthlyStats: React.FC<ReservationMonthlyStatsProps> = ({
  data,
  isLoading = false,
}) => {
  // 月次合計を計算
  const totalTrucks = data.reduce((sum, d) => sum + d.reserve_trucks, 0);
  const totalFixed = data.reduce((sum, d) => sum + d.reserve_fixed_trucks, 0);
  const avgTrucks = data.length > 0 ? Math.round(totalTrucks / data.length) : 0;
  const fixedRatio = totalTrucks > 0 ? ((totalFixed / totalTrucks) * 100).toFixed(1) : '0.0';

  return (
    <Card
      size="small"
      style={{ marginTop: 16 }}
      styles={{ body: { padding: '16px' } }}
    >
      <div style={{ marginBottom: 12 }}>
        <Text strong style={{ fontSize: 14 }}>📊 月次統計</Text>
      </div>

      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="合計予約台数"
            value={totalTrucks}
            prefix={<TruckOutlined />}
            suffix="台"
            valueStyle={{ fontSize: 20 }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="合計固定客台数"
            value={totalFixed}
            prefix={<TeamOutlined />}
            suffix="台"
            valueStyle={{ fontSize: 20, color: '#52c41a' }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="1日平均予約"
            value={avgTrucks}
            suffix="台"
            valueStyle={{ fontSize: 20 }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="固定客比率"
            value={fixedRatio}
            suffix="%"
            precision={1}
            valueStyle={{ fontSize: 20, color: '#1890ff' }}
            loading={isLoading}
          />
        </Col>
      </Row>
    </Card>
  );
};
