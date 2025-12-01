import React from 'react';
import { Row, Col } from 'antd';
import { CategorySelector } from '../CategorySelector';
import { ModeSelector } from '../ModeSelector';
import { TopNSortControls } from '../TopNSortControls';
import type { Mode, SortKey, SortOrder, CategoryKind } from '../../../../shared/model/types';
import type { FilterLayoutResult } from '../../hooks/useFilterLayout';
import type { GridConfig } from '../../config/layout.config';

interface CategoryModeSectionProps {
  // Layout
  layout: FilterLayoutResult;
  gutter: [number, number];
  
  // Category
  categoryKind: CategoryKind;
  onCategoryKindChange: (kind: CategoryKind) => void;
  
  // Mode
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  
  // TopN & Sort
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  onTopNChange: (topN: 10 | 20 | 50 | 'all') => void;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;
}

/**
 * 種別・モード・TopN/ソートセクション
 * 
 * デスクトップ（xl≥1280px）: 1行に3要素を配置
 * モバイル（xl<1280px）: 種別のみ1行目、モード+TopNを2行目
 */
export const CategoryModeSection: React.FC<CategoryModeSectionProps> = ({
  layout,
  gutter,
  categoryKind,
  onCategoryKindChange,
  mode,
  onModeChange,
  topN,
  sortBy,
  order,
  sortKeyOptions,
  onTopNChange,
  onSortByChange,
  onOrderChange,
}) => {
  const modeTopNControls = (
    <>
      <Col {...layout.modeGrid}>
        <ModeSelector value={mode} onChange={onModeChange} />
      </Col>
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
  );

  return (
    <>
      {/* 1行目: 種別 + (デスクトップのみ)モード+TopN */}
      <Row gutter={gutter} align="middle">
        <Col {...layout.categoryGrid}>
          <CategorySelector
            value={categoryKind}
            onChange={onCategoryKindChange}
          />
        </Col>
        
        {layout.isDesktop && modeTopNControls}
      </Row>

      {/* モバイルのみ: 2行目にモード+TopN */}
      {!layout.isDesktop && (
        <Row gutter={gutter} align="middle" style={{ marginTop: 16 }}>
          {modeTopNControls}
        </Row>
      )}
    </>
  );
};
