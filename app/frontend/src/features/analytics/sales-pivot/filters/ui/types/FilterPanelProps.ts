/**
 * FilterPanel コンポーネントのProps型定義
 * 
 * 各責務ごとに型を分離し、型安全性と可読性を向上させます。
 */

import type { Dayjs } from 'dayjs';
import type { Mode, SortKey, SortOrder, ID, SalesRep, CategoryKind } from '../../../shared/model/types';

/**
 * 期間選択関連のProps
 */
export interface PeriodProps {
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
}

/**
 * カテゴリ種別関連のProps
 */
export interface CategoryProps {
  categoryKind: CategoryKind;
  onCategoryKindChange: (kind: CategoryKind) => void;
}

/**
 * モード・TopN・ソート関連のProps
 */
export interface ModeControlProps {
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  onModeChange: (mode: Mode) => void;
  onTopNChange: (topN: 10 | 20 | 50 | 'all') => void;
  onSortByChange: (sortBy: SortKey) => void;
  onOrderChange: (order: SortOrder) => void;
}

/**
 * 営業・フィルタ関連のProps
 */
export interface RepFilterProps {
  repIds: ID[];
  filterIds: ID[];
  reps: SalesRep[];
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
  onRepIdsChange: (ids: ID[]) => void;
  onFilterIdsChange: (ids: ID[]) => void;
}

/**
 * FilterPanelの全Props
 * 各責務の型を結合
 */
export type FilterPanelProps = 
  & PeriodProps 
  & CategoryProps 
  & ModeControlProps 
  & RepFilterProps;
