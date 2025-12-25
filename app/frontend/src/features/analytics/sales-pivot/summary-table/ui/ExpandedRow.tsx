/**
 * summary-table/ui/ExpandedRow.tsx
 * サマリテーブル展開行（TopN詳細 + チャート）
 */

import React from 'react';
import { Card, Table, Tabs, Tag, Space, Button } from 'antd';
import type { TableColumnsType, TableProps } from 'antd';
import { SwapOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Tooltip } from 'antd';
import type {
  SummaryRow,
  MetricEntry,
  Mode,
  SortKey,
  SortOrder,
  SummaryQuery,
  CategoryKind,
  ID,
} from '../../shared/model/types';
import { fmtCurrency, fmtNumber, fmtUnitPrice, axisLabel } from '../../shared/model/metrics';
import { MetricChart } from './MetricChart';

interface SortBadgeProps {
  label: string;
  keyName: string;
  order: string;
}

const SortBadge: React.FC<SortBadgeProps> = ({ label, keyName, order }) => (
  <Tag style={{ marginRight: 8 }}>
    {label}: {keyName} ({order === 'desc' ? '降順' : '昇順'})
  </Tag>
);

interface ExpandedRowProps {
  row: SummaryRow;
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: string;
  order: 'asc' | 'desc';
  onSortChange: (sortBy: string, order: 'asc' | 'desc') => void;
  onRowClick: (entry: MetricEntry, repId: ID) => void;
  repSeriesCache: Record<string, unknown[]>;
  loadDailySeries: (repId: string) => Promise<void>;
  query: SummaryQuery;
  categoryKind: CategoryKind;
}

/**
 * 展開行コンポーネント（営業ごとのTopN詳細）
 */
export const ExpandedRow: React.FC<ExpandedRowProps> = ({
  row,
  mode,
  topN,
  sortBy,
  order,
  onSortChange,
  onRowClick,
  repSeriesCache,
  loadDailySeries,
  query,
  categoryKind,
}) => {
  const data = row.topN;
  const maxAmount = Math.max(1, ...data.map((x: MetricEntry) => x.amount));
  const maxQty = Math.max(1, ...data.map((x: MetricEntry) => x.qty));
  const maxCount = Math.max(1, ...data.map((x: MetricEntry) => x.count));
  const unitCandidates = data.map((x: MetricEntry) => x.unitPrice ?? 0);
  const maxUnit = Math.max(1, ...unitCandidates);
  const nameTitle = axisLabel(mode);

  // 件数/台数ラベルの動的切り替え
  const countLabel = mode === 'item' ? '件数' : '台数';
  const countSuffix = mode === 'item' ? '件' : '台';
  // 売上/仕入ラベルの動的切り替え
  const amountLabel = categoryKind === 'waste' ? '売上' : '仕入';

  const childCols: TableColumnsType<MetricEntry> = [
    {
      title: nameTitle,
      dataIndex: 'name',
      key: 'name',
      width: 150,
      sorter: (a: MetricEntry, b: MetricEntry) => a.name.localeCompare(b.name, 'ja'),
    },
    {
      title: amountLabel,
      dataIndex: 'amount',
      key: 'amount',
      align: 'right',
      width: 130,
      sorter: (a: MetricEntry, b: MetricEntry) => a.amount - b.amount,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 80, textAlign: 'right' }}>{fmtCurrency(v)}</span>
          <div className="sales-tree-mini-bar-bg">
            <div
              className="sales-tree-mini-bar sales-tree-mini-bar-blue"
              style={{ width: `${Math.round((v / maxAmount) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: '数量（kg）',
      dataIndex: 'qty',
      key: 'qty',
      align: 'right',
      width: 130,
      sorter: (a: MetricEntry, b: MetricEntry) => a.qty - b.qty,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtNumber(v)}</span>
          <div className="sales-tree-mini-bar-bg">
            <div
              className="sales-tree-mini-bar sales-tree-mini-bar-green"
              style={{ width: `${Math.round((v / maxQty) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: `${countLabel}（${countSuffix}）`,
      dataIndex: 'count',
      key: 'count',
      align: 'right',
      width: 120,
      sorter: (a: MetricEntry, b: MetricEntry) => a.count - b.count,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 48, textAlign: 'right' }}>
            {fmtNumber(v)} {countSuffix}
          </span>
          <div className="sales-tree-mini-bar-bg">
            <div
              className="sales-tree-mini-bar sales-tree-mini-bar-blue"
              style={{ width: `${Math.round((v / maxCount) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: (
        <Space>
          <span>単価</span>
          <Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'unitPrice',
      key: 'unitPrice',
      align: 'right',
      width: 120,
      sorter: (a: MetricEntry, b: MetricEntry) => (a.unitPrice ?? 0) - (b.unitPrice ?? 0),
      render: (v: number | null) => (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            justifyContent: 'flex-end',
          }}
        >
          <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtUnitPrice(v)}</span>
          <div className="sales-tree-mini-bar-bg">
            <div
              className="sales-tree-mini-bar sales-tree-mini-bar-gold"
              style={{ width: `${v ? Math.round((v / maxUnit) * 100) : 0}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'ops',
      fixed: 'right',
      width: 40,
      render: (_: unknown, rec: MetricEntry) => (
        <Button size="small" icon={<SwapOutlined />} onClick={() => onRowClick(rec, row.repId)}>
          詳細
        </Button>
      ),
    },
  ];

  const onChildChange: TableProps<MetricEntry>['onChange'] = (_p, _f, sorter) => {
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    if (s && 'field' in s && s.field) {
      const f = String(s.field);
      let key: SortKey = sortBy as SortKey;
      // dataIndex から SortKey へのマッピング
      if (f === 'name') key = mode === 'date' ? 'date' : 'name';
      else if (f === 'amount') key = 'amount';
      else if (f === 'qty') key = 'qty';
      else if (f === 'count') key = 'count';
      else if (f === 'unitPrice') key = 'unit_price'; // camelCase -> snake_case
      const ord: SortOrder = s.order === 'ascend' ? 'asc' : 'desc';
      onSortChange(key, ord);
    }
  };

  const repId = row.repId;
  const series = repSeriesCache[repId];

  const handleLoadSeries = async () => {
    if (repSeriesCache[repId]) return;
    await loadDailySeries(repId);
  };

  return (
    <Card
      className="sales-tree-accent-card sales-tree-accent-secondary"
      size="small"
      style={{ marginTop: 8 }}
    >
      <Tabs
        tabBarExtraContent={
          <Space wrap>
            <SortBadge label="並び替え" keyName={sortBy} order={order} />
            <Tag>Top{topN === 'all' ? 'All' : topN}</Tag>
          </Space>
        }
        items={[
          {
            key: 'table',
            label: '表',
            children: (
              <Table<MetricEntry>
                rowKey={(record, index) => `${record.id}-${index}`}
                size="small"
                columns={childCols}
                dataSource={data}
                pagination={false}
                onChange={onChildChange}
                scroll={{ x: 'max-content' }}
                rowClassName={(_: unknown, idx: number) =>
                  idx % 2 === 0 ? 'sales-tree-zebra-even' : 'sales-tree-zebra-odd'
                }
              />
            ),
          },
          {
            key: 'chart',
            label: 'グラフ',
            children: (
              <MetricChart
                data={data}
                series={series}
                repName={row.repName}
                onLoadSeries={handleLoadSeries}
                query={query}
                mode={mode}
                categoryKind={categoryKind}
              />
            ),
          },
        ]}
      />
    </Card>
  );
};
