/**
 * kpi/ui/KpiCards.tsx
 * KPIサマリカード表示UI
 */

import React from 'react';
import { Card, Row, Col, Statistic, Typography, Tooltip } from 'antd';
import { fmtCurrency, fmtNumber, fmtUnitPrice } from '../../shared/model/metrics';

interface KpiCardsProps {
  totalAmount: number;
  totalQty: number;
  totalCount: number;
  avgUnitPrice: number | null;
  selectedRepLabel: string;
  hasSelection: boolean;
}

/**
 * KPIカードコンポーネント
 */
export const KpiCards: React.FC<KpiCardsProps> = ({
  totalAmount,
  totalQty,
  totalCount,
  avgUnitPrice,
  selectedRepLabel,
  hasSelection,
}) => {
  if (!hasSelection) {
    return (
      <Card className="accent-card accent-gold">
        <div style={{ padding: 12 }}>
          <Typography.Text type="secondary">
            営業が未選択のため、KPIは表示されません。左上の「営業」から選択してください。
          </Typography.Text>
        </div>

        <style>{`
          .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
          .accent-gold { border-left-color: #faad14; }
        `}</style>
      </Card>
    );
  }

  return (
    <Card
      className="accent-card accent-gold"
      title={
        <div className="card-section-header">
          KPI（営業：
          <Tooltip title={selectedRepLabel}>
            <span>{selectedRepLabel}</span>
          </Tooltip>
          ）
        </div>
      }
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Statistic
            title="（表示対象）合計 売上"
            value={totalAmount}
            formatter={(v) => fmtCurrency(Number(v))}
          />
        </Col>
        <Col xs={24} md={6}>
          <Statistic
            title="（表示対象）合計 数量"
            value={totalQty}
            formatter={(v) => `${fmtNumber(Number(v))} kg`}
          />
        </Col>
        <Col xs={24} md={6}>
          <Statistic
            title="（表示対象）合計 台数"
            value={totalCount}
            formatter={(v) => `${fmtNumber(Number(v))} 台`}
          />
        </Col>
        <Col xs={24} md={6}>
          <Statistic
            title="（表示対象）加重平均 単価"
            valueRender={() => <span>{fmtUnitPrice(avgUnitPrice)}</span>}
          />
        </Col>
      </Row>

      <style>{`
        .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
        .accent-gold { border-left-color: #faad14; }
        .card-section-header { 
          font-weight: 600; 
          padding: 6px 10px; 
          margin-bottom: 12px; 
          border-radius: 6px; 
          background: #f3fff4; 
          border: 1px solid #e6f7e6; 
        }
      `}</style>
    </Card>
  );
};
