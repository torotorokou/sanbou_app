/**
 * filters/ui/FilterPanel.tsx
 * フィルタパネル統合UI
 */

import React from 'react';
import { Card, Row, Col, Divider } from 'antd';
import { CategorySelector } from './components/CategorySelector';
import { ModeSelector } from './components/ModeSelector';
import { TopNSortControls } from './components/TopNSortControls';
import { PeriodSelector } from './components/PeriodSelector';
import { RepFilterSelector } from './components/RepFilterSelector';
import { useFilterLayout } from './hooks/useFilterLayout';
import { GRID_GUTTER, MARGINS } from './config/layout.config';
import type { FilterPanelProps } from './types/FilterPanelProps';
import styles from './FilterPanel.module.css';

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
