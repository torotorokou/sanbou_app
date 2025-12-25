/**
 * pivot-drawer/ui/PivotDrawer.tsx
 * Pivotドロワーコンテナ
 */

import React from "react";
import { Drawer, Card, Space, Tag, Segmented } from "antd";
import type {
  DrawerState,
  Mode,
  SortKey,
  SortOrder,
  MetricEntry,
  CategoryKind,
} from "../../shared/model/types";
import { axisLabel } from "../../shared/model/metrics";
import { PivotTable } from "./PivotTable";

interface PivotDrawerProps {
  drawer: DrawerState;
  onClose: () => void;
  pivotData: Record<Mode, MetricEntry[]>;
  pivotCursor: Record<Mode, string | null>;
  pivotLoading: boolean;
  onActiveAxisChange: (axis: Mode) => void;
  onTopNChange: (topN: 10 | 20 | 50 | "all") => void;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;
  onLoadMore: (axis: Mode, reset: boolean) => Promise<void>;
  categoryKind: CategoryKind;
  onRowClick?: (row: MetricEntry, axis: Mode) => void;
}

/**
 * Pivotドロワーコンポーネント
 */
export const PivotDrawer: React.FC<PivotDrawerProps> = ({
  drawer,
  onClose,
  pivotData,
  pivotCursor,
  pivotLoading,
  onActiveAxisChange,
  onTopNChange,
  onSortByChange,
  onOrderChange,
  onLoadMore,
  categoryKind,
  onRowClick,
}) => {
  if (!drawer.open) return null;

  // 売上/仕入ラベルの動的切り替え
  const amountLabel = categoryKind === "waste" ? "売上" : "仕入";

  return (
    <Drawer
      title={`詳細：${axisLabel(drawer.baseAxis)}「${drawer.baseName}」`}
      open={drawer.open}
      onClose={onClose}
      width={1000}
    >
      <Card
        className="sales-tree-accent-card sales-tree-accent-secondary"
        title={<div className="sales-tree-card-section-header">ピボット</div>}
      >
        {/* ヘッダー情報 */}
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <Tag color="#237804">ベース：{axisLabel(drawer.baseAxis)}</Tag>
            <Tag>{drawer.baseName}</Tag>
            <Tag>
              並び替え: {drawer.sortBy} (
              {drawer.order === "desc" ? "降順" : "昇順"})
            </Tag>
            <Tag>Top{drawer.topN === "all" ? "All" : drawer.topN}</Tag>
          </Space>
        </div>

        {/* コントロール */}
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <Segmented
              options={[
                { label: "10", value: "10" },
                { label: "20", value: "20" },
                { label: "50", value: "50" },
                { label: "All", value: "all" },
              ]}
              value={String(drawer.topN)}
              onChange={(v: string | number) =>
                onTopNChange(v === "all" ? "all" : (Number(v) as 10 | 20 | 50))
              }
            />
            <Segmented
              options={[
                { label: amountLabel, value: "amount" },
                { label: "数量", value: "qty" },
                {
                  label: drawer.activeAxis === "item" ? "件数" : "台数",
                  value: "count",
                },
                { label: "単価", value: "unit_price" },
                {
                  label: drawer.activeAxis === "date" ? "日付" : "名称",
                  value: drawer.activeAxis === "date" ? "date" : "name",
                },
              ]}
              value={drawer.sortBy}
              onChange={(v) => onSortByChange(v as SortKey)}
            />
            <Segmented
              options={[
                { label: "降順", value: "desc" },
                { label: "昇順", value: "asc" },
              ]}
              value={drawer.order}
              onChange={(v) => onOrderChange(v as SortOrder)}
            />
          </Space>
        </div>

        {/* Pivot Table（タブ形式） */}
        <PivotTable
          targets={drawer.targets}
          activeAxis={drawer.activeAxis}
          pivotData={pivotData}
          pivotCursor={pivotCursor}
          pivotLoading={pivotLoading}
          topN={drawer.topN}
          onActiveAxisChange={onActiveAxisChange}
          onLoadMore={onLoadMore}
          onSortByChange={onSortByChange}
          onOrderChange={onOrderChange}
          categoryKind={categoryKind}
          onRowClick={onRowClick}
        />
      </Card>
    </Drawer>
  );
};
