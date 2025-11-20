/**
 * summary-table/ui/ExpandedRow.tsx
 * サマリテーブル展開行（TopN詳細 + チャート）
 */

import React from 'react';
import { Card, Table, Tabs, Tag, Space, Button, Row, Col } from 'antd';
import type { TableColumnsType, TableProps } from 'antd';
import { SwapOutlined, ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Tooltip } from 'antd';
import type { SummaryRow, MetricEntry, Mode, SortKey, SortOrder } from '../../shared/model/types';
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
  onRowClick: (repId: string) => void;
  repSeriesCache: Record<string, any[]>;
  loadDailySeries: (repId: string) => Promise<void>;
  query: any;
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
}) => {
  const data = row.topN;
  const maxAmount = Math.max(1, ...data.map((x: any) => x.amount));
  const maxQty = Math.max(1, ...data.map((x: any) => x.qty));
  const maxCount = Math.max(1, ...data.map((x: any) => x.count));
  const unitCandidates = data.map((x: any) => x.unit_price ?? 0);
  const maxUnit = Math.max(1, ...unitCandidates);
  const nameTitle = axisLabel(mode);

  const childCols: TableColumnsType<MetricEntry> = [
    { title: nameTitle, dataIndex: 'name', key: 'name', width: 220, sorter: true },
    {
      title: '売上',
      dataIndex: 'amount',
      key: 'amount',
      align: 'right',
      width: 180,
      sorter: true,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 80, textAlign: 'right' }}>{fmtCurrency(v)}</span>
          <div className="mini-bar-bg">
            <div
              className="mini-bar mini-bar-blue"
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
      width: 160,
      sorter: true,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtNumber(v)}</span>
          <div className="mini-bar-bg">
            <div
              className="mini-bar mini-bar-green"
              style={{ width: `${Math.round((v / maxQty) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: '台数（台）',
      dataIndex: 'count',
      key: 'count',
      align: 'right',
      width: 120,
      sorter: true,
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ minWidth: 48, textAlign: 'right' }}>{fmtNumber(v)} 台</span>
          <div className="mini-bar-bg">
            <div
              className="mini-bar mini-bar-blue"
              style={{ width: `${Math.round((v / maxCount) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      title: (
        <Space>
          <span>売単価</span>
          <Tooltip title="単価＝Σ金額 / Σ数量（数量=0は未定義）">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'unit_price',
      key: 'unit_price',
      align: 'right',
      width: 170,
      sorter: true,
      render: (v: number | null) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
          <span style={{ minWidth: 64, textAlign: 'right' }}>{fmtUnitPrice(v)}</span>
          <div className="mini-bar-bg">
            <div
              className="mini-bar mini-bar-gold"
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
      width: 120,
      render: (_: any, rec: MetricEntry) => (
        <Button size="small" icon={<SwapOutlined />} onClick={() => onRowClick(rec.id)}>
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
      if (f === 'name') key = mode === 'date' ? 'date' : 'name';
      else if ((['amount', 'qty', 'count', 'unit_price'] as string[]).includes(f))
        key = f as SortKey;
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
    <Card className="accent-card accent-secondary" size="small" style={{ marginTop: 8 }}>
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
                rowKey="id"
                size="small"
                columns={childCols}
                dataSource={data}
                pagination={false}
                onChange={onChildChange}
                scroll={{ x: 1280 }}
                rowClassName={(_: any, idx: number) => (idx % 2 === 0 ? 'zebra-even' : 'zebra-odd')}
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
              />
            ),
          },
        ]}
      />

      <style>{`
        .accent-card { border-left: 4px solid #23780410; overflow: hidden; }
        .accent-secondary { border-left-color: #52c41a; }
        .mini-bar-bg { flex: 1; height: 6px; background: #f6f7fb; border-radius: 4px; overflow: hidden; }
        .mini-bar { height: 100%; }
        .mini-bar-blue { background: #237804; }
        .mini-bar-green { background: #52c41a; }
        .mini-bar-gold { background: #faad14; }
        .zebra-even { background: #ffffff; }
        .zebra-odd { background: #fbfcfe; }
      `}</style>
    </Card>
  );
};
