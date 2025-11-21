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
      <Card className="sales-tree-accent-card sales-tree-accent-gold">
        <div style={{ padding: 12 }}>
          <Typography.Text type="secondary">
            営業が未選択のため、KPIは表示されません。左上の「営業」から選択してください。
          </Typography.Text>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="sales-tree-accent-card sales-tree-accent-gold"
      title={
        <div className="sales-tree-card-section-header">
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
            title="（表示対象）合計 件数"
            value={totalCount}
            formatter={(v) => `${fmtNumber(Number(v))} 件`}
          />
        </Col>
        <Col xs={24} md={6}>
          <Statistic
            title="（表示対象）加重平均 単価"
            valueRender={() => <span>{fmtUnitPrice(avgUnitPrice)}</span>}
          />
        </Col>
      </Row>
    </Card>
  );
};
