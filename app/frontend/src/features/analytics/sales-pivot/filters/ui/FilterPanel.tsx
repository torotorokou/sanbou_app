/**
 * filters/ui/FilterPanel.tsx
 * フィルタパネル統合UI
 */

import React from 'react';
import { Card, Divider, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { CategoryModeSection } from './components/sections/CategoryModeSection';
import { PeriodSection } from './components/sections/PeriodSection';
import { RepFilterSection } from './components/sections/RepFilterSection';
import { useFilterLayout } from './hooks/useFilterLayout';
import { GRID_GUTTER, MARGINS } from './config/layout.config';
import type { FilterPanelProps } from './types/FilterPanelProps';
import styles from './FilterPanel.module.css';

/**
 * フィルタパネルコンポーネント
 * 
 * 【構成】
 * 1. 種別・モード・TopN/ソート セクション
 * 2. 期間選択 セクション
 * 3. 営業・絞り込み セクション
 * 
 * 【レスポンシブ】
 * xl: 1280px以下で2行レイアウト（種別 / モード+Top&並び替え）
 */
export const FilterPanel: React.FC<FilterPanelProps> = ({
  granularity,
  periodMode,
  month,
  range,
  singleDate,
  dateRange,
  onGranularityChange,
  onPeriodModeChange,
  onMonthChange,
  onRangeChange,
  onSingleDateChange,
  onDateRangeChange,
  categoryKind,
  onCategoryKindChange,
  mode,
  topN,
  sortBy,
  order,
  onModeChange,
  onTopNChange,
  onSortByChange,
  onOrderChange,
  repIds,
  filterIds,
  reps,
  repOptions,
  filterOptions,
  sortKeyOptions,
  onRepIdsChange,
  onFilterIdsChange,
  onReset,
}) => {
  const layout = useFilterLayout();

  return (
    <Card 
      className={`${styles.accentCard} ${styles.accentPrimary} sales-tree-accent-card sales-tree-accent-primary`}
      title={<div className={`${styles.cardSectionHeader} sales-tree-card-section-header`}>条件</div>}
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={onReset}
          size="small"
        >
          リセット
        </Button>
      }
    >
      {/* セクション1: 種別・モード・TopN/ソート */}
      <CategoryModeSection
        layout={layout}
        gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]}
        categoryKind={categoryKind}
        onCategoryKindChange={onCategoryKindChange}
        mode={mode}
        onModeChange={onModeChange}
        topN={topN}
        sortBy={sortBy}
        order={order}
        sortKeyOptions={sortKeyOptions}
        onTopNChange={onTopNChange}
        onSortByChange={onSortByChange}
        onOrderChange={onOrderChange}
      />

      {/* セクション2: 期間選択 */}
      <PeriodSection
        gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]}
        periodGrid={layout.periodGrid}
        marginTop={MARGINS.sectionTop}
        granularity={granularity}
        periodMode={periodMode}
        month={month}
        range={range}
        singleDate={singleDate}
        dateRange={dateRange}
        onGranularityChange={onGranularityChange}
        onPeriodModeChange={onPeriodModeChange}
        onMonthChange={onMonthChange}
        onRangeChange={onRangeChange}
        onSingleDateChange={onSingleDateChange}
        onDateRangeChange={onDateRangeChange}
      />

      <Divider style={{ margin: MARGINS.divider }} />

      {/* セクション3: 営業・絞り込み */}
      <RepFilterSection
        gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]}
        mode={mode}
        repIds={repIds}
        filterIds={filterIds}
        reps={reps}
        repOptions={repOptions}
        filterOptions={filterOptions}
        onRepIdsChange={onRepIdsChange}
        onFilterIdsChange={onFilterIdsChange}
      />
    </Card>
  );
};
