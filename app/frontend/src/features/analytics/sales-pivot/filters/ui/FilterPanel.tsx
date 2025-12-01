/**
 * filters/ui/FilterPanel.tsx
 * フィルタパネル統合UI
 */

import React from 'react';
import { Card, Row, Col, Divider } from 'antd';
import type { Dayjs } from 'dayjs';
import type { Mode, SortKey, SortOrder, ID, SalesRep, CategoryKind } from '../../shared/model/types';
import { CategorySelector } from './components/CategorySelector';
import { ModeSelector } from './components/ModeSelector';
import { TopNSortControls } from './components/TopNSortControls';
import { PeriodSelector } from './components/PeriodSelector';
import { RepFilterSelector } from './components/RepFilterSelector';
import { useFilterLayout } from './hooks/useFilterLayout';
import { GRID_GUTTER, MARGINS } from './config/layout.config';
import styles from './FilterPanel.module.css';

interface FilterPanelProps {
  // Period
  granularity: 'month' | 'date';
  periodMode: 'single' | 'range';
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  singleDate: Dayjs;
  dateRange: [Dayjs, Dayjs] | null;
  onGranularityChange: (granularity: 'month' | 'date') => void;
  onPeriodModeChange: (mode: 'single' | 'range') => void;
  onMonthChange: (month: Dayjs) => void;
  onRangeChange: (range: [Dayjs, Dayjs] | null) => void;
  onSingleDateChange: (date: Dayjs) => void;
  onDateRangeChange: (range: [Dayjs, Dayjs] | null) => void;

  // Category
  categoryKind: CategoryKind;
  onCategoryKindChange: (kind: CategoryKind) => void;

  // Mode & Controls
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  onModeChange: (mode: Mode) => void;
  onTopNChange: (topN: 10 | 20 | 50 | 'all') => void;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;

  // Rep & Filter
  repIds: ID[];
  filterIds: ID[];
  reps: SalesRep[];
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  onRepIdsChange: (ids: ID[]) => void;
  onFilterIdsChange: (ids: ID[]) => void;
}

/**
 * フィルタパネルコンポーネント
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
}) => {
  const layout = useFilterLayout();

  return (
    <Card 
      className={`${styles.accentCard} ${styles.accentPrimary} sales-tree-accent-card sales-tree-accent-primary`}
      title={<div className={`${styles.cardSectionHeader} sales-tree-card-section-header`}>条件</div>}
    >
      {/* 1行目（xl以上）/ 1行目（xl以下）: 種別 */}
      <Row gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]} align="middle">
        {/* 種別切り替え */}
        <Col {...layout.categoryGrid}>
          <CategorySelector
            value={categoryKind}
            onChange={onCategoryKindChange}
          />
        </Col>

        {/* xl以上: モード+TopN・ソートを同じ行に表示 */}
        {layout.isDesktop && (
          <>
            {/* モード */}
            <Col {...layout.modeGrid}>
              <ModeSelector value={mode} onChange={onModeChange} />
            </Col>

            {/* TopN・ソート */}
            <Col {...layout.topNSortGrid}>
              <TopNSortControls
                topN={topN}
                sortBy={sortBy}
                order={order}
                sortKeyOptions={sortKeyOptions}
                onTopNChange={onTopNChange}
                onSortByChange={onSortByChange}
                onOrderChange={onOrderChange}
              />
            </Col>
          </>
        )}
      </Row>

      {/* xl以下: 2行目にモード+TopN・ソートを表示 */}
      {!layout.isDesktop && (
        <Row gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]} align="middle" style={{ marginTop: MARGINS.sectionTop }}>
          {/* モード */}
          <Col {...layout.modeGrid}>
            <ModeSelector value={mode} onChange={onModeChange} />
          </Col>

          {/* TopN・ソート */}
          <Col {...layout.topNSortGrid}>
            <TopNSortControls
              topN={topN}
              sortBy={sortBy}
              order={order}
              sortKeyOptions={sortKeyOptions}
              onTopNChange={onTopNChange}
              onSortByChange={onSortByChange}
              onOrderChange={onOrderChange}
            />
          </Col>
        </Row>
      )}
      {/* 期間選択 */}
      <Row gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]} align="middle" style={{ marginTop: MARGINS.sectionTop }}>
        <Col {...layout.periodGrid}>
          <PeriodSelector
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
        </Col>
      </Row>

      <Divider style={{ margin: MARGINS.divider }} />

      {/* 営業・絞り込み */}
      <Row gutter={[GRID_GUTTER.horizontal, GRID_GUTTER.vertical]}>
        <Col xs={24}>
          <RepFilterSelector
            mode={mode}
            repIds={repIds}
            filterIds={filterIds}
            reps={reps}
            repOptions={repOptions}
            filterOptions={filterOptions}
            onRepIdsChange={onRepIdsChange}
            onFilterIdsChange={onFilterIdsChange}
          />
        </Col>
      </Row>
    </Card>
  );
};
