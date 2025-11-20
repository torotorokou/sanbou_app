/**
 * summary-table/ui/SummaryTable.tsx
 * サマリテーブルメインコンポーネント
 */

import React from 'react';
import { Card, Table, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { Tag, Space } from 'antd';
import type { SummaryRow, Mode, MetricEntry, SummaryQuery } from '../../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice, axisLabel } from '../../shared/model/metrics';
import { ExpandedRow } from './ExpandedRow';

interface SummaryTableProps {
  data: SummaryRow[];
  loading: boolean;
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  hasSelection: boolean;
  onRowClick: (entry: MetricEntry) => void;
  repSeriesCache: Record<string, unknown[]>;
  loadDailySeries: (repId: string) => Promise<void>;
  sortBy: string;
  order: 'asc' | 'desc';
  onSortChange: (sortBy: string, order: 'asc' | 'desc') => void;
  query: SummaryQuery;
}

/**
 * サマリテーブルコンポーネント
 */
export const SummaryTable: React.FC<SummaryTableProps> = ({
  data,
  loading,
  mode,
  topN,
  hasSelection,
  onRowClick,
  repSeriesCache,
  loadDailySeries,
  sortBy,
  order,
  onSortChange,
  query,
}) => {
  if (!hasSelection) {
    return (
      <Card className="sales-tree-accent-card sales-tree-accent-primary">
        <div style={{ padding: 12 }}>
          <Typography.Text type="secondary">
            営業が未選択のため、一覧は表示されません。左上の「営業」から選択してください。
          </Typography.Text>
        </div>
      </Card>
    );
  }

  const parentCols: TableColumnsType<SummaryRow> = [
    { title: '営業', dataIndex: 'repName', key: 'repName', width: 160, fixed: 'left' },
    {
      title: `${axisLabel(mode)} Top${topN === 'all' ? 'All' : topN}`,
      key: 'summary',
      render: (_: unknown, row: SummaryRow) => {
        const totalAmount = row.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
        const totalQty = row.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
        const totalCount = row.topN.reduce((s: number, x: MetricEntry) => s + x.count, 0);
        const unit = totalQty > 0 ? Math.round((totalAmount / totalQty) * 100) / 100 : null;
        return (
          <Space wrap size="small" className="sales-tree-summary-tags">
            <Tag color="#237804">合計 売上 {fmtCurrency(totalAmount)}</Tag>
            <Tag color="green">数量 {fmtNumber(totalQty)} kg</Tag>
            <Tag color="blue">台数 {fmtNumber(totalCount)} 台</Tag>
            <Tag color="gold">単価 {fmtUnitPrice(unit)}</Tag>
          </Space>
        );
      },
    },
  ];

  return (
    <Card
      className="sales-tree-accent-card sales-tree-accent-primary"
      title={<div className="sales-tree-card-section-header">一覧</div>}
    >
      <Table<SummaryRow>
        rowKey={(r) => r.repId}
        columns={parentCols}
        dataSource={data}
        loading={loading}
        pagination={false}
        expandable={{
          expandedRowRender: (record) => (
            <ExpandedRow
              row={record}
              mode={mode}
              topN={topN}
              sortBy={sortBy}
              order={order}
              onSortChange={onSortChange}
              onRowClick={onRowClick}
              repSeriesCache={repSeriesCache}
              loadDailySeries={loadDailySeries}
              query={query}
            />
          ),
          rowExpandable: () => true,
        }}
        scroll={{ x: 1220 }}
        rowClassName={(_: unknown, idx: number) => (idx % 2 === 0 ? 'sales-tree-zebra-even' : 'sales-tree-zebra-odd')}
      />
    </Card>
  );
};
