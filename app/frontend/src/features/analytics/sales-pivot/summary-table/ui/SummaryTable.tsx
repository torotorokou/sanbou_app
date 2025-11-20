/**
 * summary-table/ui/SummaryTable.tsx
 * サマリテーブルメインコンポーネント
 */

import React from 'react';
import { Card, Table, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { Tag, Space } from 'antd';
import type { SummaryRow, Mode } from '../../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice, axisLabel } from '../../shared/model/metrics';
import { ExpandedRow } from './ExpandedRow';

interface SummaryTableProps {
  data: SummaryRow[];
  loading: boolean;
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  hasSelection: boolean;
  onRowClick: (repId: string) => void;
  repSeriesCache: Record<string, any[]>;
  loadDailySeries: (repId: string) => Promise<void>;
  sortBy: string;
  order: 'asc' | 'desc';
  onSortChange: (sortBy: string, order: 'asc' | 'desc') => void;
  query: any;
  repName: string;
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
  repName,
}) => {
  if (!hasSelection) {
    return (
      <Card className="accent-card accent-primary">
        <div style={{ padding: 12 }}>
          <Typography.Text type="secondary">
            営業が未選択のため、一覧は表示されません。左上の「営業」から選択してください。
          </Typography.Text>
        </div>

        <style>{`
          .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
          .accent-primary { border-left-color: #237804; }
        `}</style>
      </Card>
    );
  }

  const parentCols: TableColumnsType<SummaryRow> = [
    { title: '営業', dataIndex: 'repName', key: 'repName', width: 160, fixed: 'left' },
    {
      title: `${axisLabel(mode)} Top${topN === 'all' ? 'All' : topN}`,
      key: 'summary',
      render: (_: any, row: SummaryRow) => {
        const totalAmount = row.topN.reduce((s: number, x: any) => s + x.amount, 0);
        const totalQty = row.topN.reduce((s: number, x: any) => s + x.qty, 0);
        const totalCount = row.topN.reduce((s: number, x: any) => s + x.count, 0);
        const unit = totalQty > 0 ? Math.round((totalAmount / totalQty) * 100) / 100 : null;
        return (
          <Space wrap size="small" className="summary-tags">
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
      className="accent-card accent-primary"
      title={<div className="card-section-header">一覧</div>}
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
        rowClassName={(_: any, idx: number) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
      />

      <style>{`
        .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
        .accent-primary { border-left-color: #237804; }
        .card-section-header { 
          font-weight: 600; 
          padding: 6px 10px; 
          margin-bottom: 12px; 
          border-radius: 6px; 
          background: #f3fff4; 
          border: 1px solid #e6f7e6; 
        }
        .zebra-even { background: #ffffff; }
        .zebra-odd { background: #fbfcfe; }
        .ant-table-tbody > tr:hover > td { background: #f6fff4 !important; }
        .summary-tags { font-size: 14px; }
        .summary-tags .ant-tag { font-size: 14px; padding: 0 10px; }
      `}</style>
    </Card>
  );
};
