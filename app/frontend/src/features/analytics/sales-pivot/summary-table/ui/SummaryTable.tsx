/**
 * summary-table/ui/SummaryTable.tsx
 * サマリテーブルメインコンポーネント
 */

import React from 'react';
import { Card, Table, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { Tag } from 'antd';
import type { SummaryRow, Mode, MetricEntry, SummaryQuery, CategoryKind, ID } from '../../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice, axisLabel } from '../../shared/model/metrics';
import { ExpandedRow } from './ExpandedRow';

interface SummaryTableProps {
  data: SummaryRow[];
  loading: boolean;
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  hasSelection: boolean;
  onRowClick: (entry: MetricEntry, repId: ID) => void;
  repSeriesCache: Record<string, unknown[]>;
  loadDailySeries: (repId: string) => Promise<void>;
  sortBy: string;
  order: 'asc' | 'desc';
  onSortChange: (sortBy: string, order: 'asc' | 'desc') => void;
  query: SummaryQuery;
  categoryKind: CategoryKind;
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
  categoryKind,
}) => {
  // 件数/台数ラベルの動的切り替え
  const countLabel = mode === 'item' ? '件数' : '台数';
  // 売上/仕入ラベルの動的切り替え
  const amountLabel = categoryKind === 'waste' ? '売上' : '仕入';
  
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
    { 
      title: '営業', 
      dataIndex: 'repName', 
      key: 'repName', 
      width: 160, 
      fixed: 'left',
      sorter: (a: SummaryRow, b: SummaryRow) => a.repName.localeCompare(b.repName, 'ja')
    },
    {
      title: `${axisLabel(mode)} Top${topN === 'all' ? 'All' : topN}`,
      key: 'summary',
      children: [
        {
          title: amountLabel,
          key: 'amount',
          align: 'right' as const,
          width: 150,
          sorter: (a: SummaryRow, b: SummaryRow) => {
            const aTotal = a.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            const bTotal = b.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            return aTotal - bTotal;
          },
          render: (_: unknown, row: SummaryRow) => {
            const totalAmount = row.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            return <Tag color="volcano" style={{ fontSize: '15px', padding: '4px 8px' }}>{fmtCurrency(totalAmount)}</Tag>;
          },
        },
        {
          title: '数量 (kg)',
          key: 'qty',
          align: 'right' as const,
          width: 140,
          sorter: (a: SummaryRow, b: SummaryRow) => {
            const aTotal = a.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            const bTotal = b.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            return aTotal - bTotal;
          },
          render: (_: unknown, row: SummaryRow) => {
            const totalQty = row.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            return <Tag color="green" style={{ fontSize: '15px', padding: '4px 8px' }}>{fmtNumber(totalQty)} kg</Tag>;
          },
        },
        {
          title: countLabel,
          key: 'count',
          align: 'right' as const,
          width: 120,
          sorter: (a: SummaryRow, b: SummaryRow) => {
            const aTotal = a.topN.reduce((s: number, x: MetricEntry) => s + x.count, 0);
            const bTotal = b.topN.reduce((s: number, x: MetricEntry) => s + x.count, 0);
            return aTotal - bTotal;
          },
          render: (_: unknown, row: SummaryRow) => {
            const totalCount = row.topN.reduce((s: number, x: MetricEntry) => s + x.count, 0);
            const suffix = mode === 'item' ? '件' : '台';
            return <Tag color="blue" style={{ fontSize: '15px', padding: '4px 8px' }}>{fmtNumber(totalCount)} {suffix}</Tag>;
          },
        },
        {
          title: '単価',
          key: 'unit_price',
          align: 'right' as const,
          width: 120,
          sorter: (a: SummaryRow, b: SummaryRow) => {
            const aAmount = a.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            const aQty = a.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            const aUnit = aQty > 0 ? aAmount / aQty : 0;
            const bAmount = b.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            const bQty = b.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            const bUnit = bQty > 0 ? bAmount / bQty : 0;
            return aUnit - bUnit;
          },
          render: (_: unknown, row: SummaryRow) => {
            const totalAmount = row.topN.reduce((s: number, x: MetricEntry) => s + x.amount, 0);
            const totalQty = row.topN.reduce((s: number, x: MetricEntry) => s + x.qty, 0);
            const unit = totalQty > 0 ? totalAmount / totalQty : null;
            return <Tag color="gold" style={{ fontSize: '15px', padding: '4px 8px' }}>{fmtUnitPrice(unit)}</Tag>;
          },
        },
      ],
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
              categoryKind={categoryKind}
            />
          ),
          rowExpandable: () => true,
        }}
        scroll={{ x: 'max-content' }}
        rowClassName={(_: unknown, idx: number) => (idx % 2 === 0 ? 'sales-tree-zebra-even' : 'sales-tree-zebra-odd')}
      />
    </Card>
  );
};
