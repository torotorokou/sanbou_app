/**
 * ReservationMonthlyStats - 月次予約統計グラフ
 * 
 * UI Component (状態レス)
 * カレンダーの下に表示する月次統計
 */

import React from 'react';
import { Row, Col, Statistic, Typography } from 'antd';
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
    <>
      <style>{`
        .monthly-stats .ant-statistic-title {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        
        /* xl付近 (1280-1399px) - 小さめフォント */
        @media (min-width: 1280px) and (max-width: 1399px) {
          .monthly-stats .ant-statistic-title {
            font-size: 10px !important;
          }
          .monthly-stats .ant-statistic-content-value {
            font-size: 14px !important;
          }
        }
        
        /* 中サイズ (1400-1599px) */
        @media (min-width: 1400px) and (max-width: 1599px) {
          .monthly-stats .ant-statistic-title {
            font-size: 11px !important;
          }
          .monthly-stats .ant-statistic-content-value {
            font-size: 16px !important;
          }
        }
        
        /* 大サイズ (1600px以上) */
        @media (min-width: 1600px) {
          .monthly-stats .ant-statistic-title {
            font-size: 13px !important;
          }
          .monthly-stats .ant-statistic-content-value {
            font-size: 18px !important;
          }
        }
      `}</style>
      
      <div style={{ marginBottom: 6 }}>
        <Text strong style={{ fontSize: 13 }}>📊 月次統計</Text>
      </div>

      <Row gutter={12} className="monthly-stats">
        <Col span={6}>
          <Statistic
            title="合計予約台数"
            value={totalTrucks}
            prefix={<TruckOutlined style={{ fontSize: 14 }} />}
            suffix="台"
            valueStyle={{ fontSize: 16 }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="合計固定客台数"
            value={totalFixed}
            prefix={<TeamOutlined style={{ fontSize: 14 }} />}
            suffix="台"
            valueStyle={{ fontSize: 16, color: '#52c41a' }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="1日平均予約"
            value={avgTrucks}
            suffix="台"
            valueStyle={{ fontSize: 16 }}
            loading={isLoading}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="固定客比率"
            value={fixedRatio}
            suffix="%"
            precision={1}
            valueStyle={{ fontSize: 16, color: '#1890ff' }}
            loading={isLoading}
          />
        </Col>
      </Row>
      <div style={{ 
        marginTop: 20, 
        borderBottom: '1px solid #e8e8e8' 
      }} />
    </>
  );
};
