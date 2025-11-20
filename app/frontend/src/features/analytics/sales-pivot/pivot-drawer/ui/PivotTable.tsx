/**
 * pivot-drawer/ui/PivotTable.tsx
 * Pivotテーブルコンポーネント（タブ形式）
 */

import React from 'react';
import { Tabs, Table, Space, Button, Empty, Tooltip, Typography } from 'antd';
import type { TableColumnsType, TableProps } from 'antd';
import { ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { Mode, MetricEntry, SortKey, SortOrder } from '../../shared/model/types';
import { axisLabel, fmtCurrency, fmtNumber, fmtUnitPrice } from '../../shared/model/metrics';

interface PivotTableProps {
  targets: { axis: Mode; label: string }[];
  activeAxis: Mode;
  pivotData: Record<Mode, MetricEntry[]>;
  pivotCursor: Record<Mode, string | null>;
  pivotLoading: boolean;
  topN: 10 | 20 | 50 | 'all';
  onActiveAxisChange: (axis: Mode) => void;
  onLoadMore: (axis: Mode, reset: boolean) => Promise<void>;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;
}

/**
 * Pivotテーブルコンポーネント
 * - 各軸ごとにTabで切り替え
 * - 各テーブルはミニバーグラフ付き
 */
export const PivotTable: React.FC<PivotTableProps> = ({
  targets,
  activeAxis,
  pivotData,
  pivotCursor,
  pivotLoading,
  topN,
  onActiveAxisChange,
  onLoadMore,
  onSortByChange,
  onOrderChange,
}) => {
  /**
   * テーブルソート変更ハンドラ
   */
  const handleTableChange: TableProps<MetricEntry>['onChange'] = (
    _pagination,
    _filters,
    sorter
  ) => {
    if (!Array.isArray(sorter) && sorter.field && sorter.order) {
      onSortByChange(sorter.field as SortKey);
      onOrderChange(sorter.order === 'ascend' ? 'asc' : 'desc');
    }
  };

  return (
    <Tabs
      activeKey={activeAxis}
      onChange={(key) => onActiveAxisChange(key as Mode)}
      items={targets.map((target) => {
        const rows = pivotData[target.axis];
        const maxA = Math.max(1, ...rows.map((x) => x.amount));
        const maxQ = Math.max(1, ...rows.map((x) => x.qty));
        const maxC = Math.max(1, ...rows.map((x) => x.count));
        const maxU = Math.max(1, ...rows.map((x) => x.unit_price ?? 0));

        const columns: TableColumnsType<MetricEntry> = [
          {
            title: axisLabel(target.axis),
            dataIndex: 'name',
            key: 'name',
            width: 220,
            sorter: true,
          },
          {
            title: '売上',
            dataIndex: 'amount',
            key: 'amount',
            align: 'right',
            width: 170,
            sorter: true,
            render: (v: number) => (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  justifyContent: 'flex-end',
                }}
              >
                <span style={{ minWidth: 72, textAlign: 'right' }}>
                  {fmtCurrency(v)}
                </span>
                <div className="sales-tree-mini-bar-bg">
                  <div
                    className="sales-tree-mini-bar sales-tree-mini-bar-blue"
                    style={{ width: `${Math.round((v / maxA) * 100)}%` }}
                  />
                </div>
              </div>
            ),
          },
          {
            title: '数量',
            dataIndex: 'qty',
            key: 'qty',
            align: 'right',
            width: 150,
            sorter: true,
            render: (v: number) => (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  justifyContent: 'flex-end',
                }}
              >
                <span style={{ minWidth: 60, textAlign: 'right' }}>
                  {fmtNumber(v)}
                </span>
                <div className="sales-tree-mini-bar-bg">
                  <div
                    className="sales-tree-mini-bar sales-tree-mini-bar-green"
                    style={{ width: `${Math.round((v / maxQ) * 100)}%` }}
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
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  justifyContent: 'flex-end',
                }}
              >
                <span style={{ minWidth: 48, textAlign: 'right' }}>
                  {fmtNumber(v)} 台
                </span>
                <div className="sales-tree-mini-bar-bg">
                  <div
                    className="sales-tree-mini-bar sales-tree-mini-bar-blue"
                    style={{ width: `${Math.round((v / maxC) * 100)}%` }}
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
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  justifyContent: 'flex-end',
                }}
              >
                <span style={{ minWidth: 64, textAlign: 'right' }}>
                  {fmtUnitPrice(v)}
                </span>
                <div className="sales-tree-mini-bar-bg">
                  <div
                    className="sales-tree-mini-bar sales-tree-mini-bar-gold"
                    style={{ width: `${v ? Math.round((v / maxU) * 100) : 0}%` }}
                  />
                </div>
              </div>
            ),
          },
        ];

        return {
          key: target.axis,
          label: target.label,
          children: (
            <>
              <Table<MetricEntry>
                rowKey="id"
                size="small"
                columns={columns}
                dataSource={rows}
                loading={pivotLoading}
                pagination={false}
                onChange={handleTableChange}
                locale={{
                  emptyText: pivotLoading ? '読込中...' : <Empty description="該当なし" />,
                }}
                scroll={{ x: 980 }}
                rowClassName={(_, idx) => (idx % 2 === 0 ? 'sales-tree-zebra-even' : 'sales-tree-zebra-odd')}
              />
              <Space style={{ marginTop: 8 }}>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => onLoadMore(target.axis, true)}
                >
                  再読込
                </Button>
                {topN === 'all' && pivotCursor[target.axis] && (
                  <Button
                    type="primary"
                    onClick={() => onLoadMore(target.axis, false)}
                    loading={pivotLoading}
                  >
                    さらに読み込む
                  </Button>
                )}
                {topN === 'all' && !pivotCursor[target.axis] && (
                  <Typography.Text type="secondary">すべて読み込み済み</Typography.Text>
                )}
              </Space>
            </>
          ),
        };
      })}
    />
  );
};
