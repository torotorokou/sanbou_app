/**
 * features/analytics/sales-pivot/index.ts
 * Public API - 機能ごとのsliceをエクスポート
 */

// ========== Shared ==========
export * from './shared/model/types';
export * from './shared/model/metrics';
export type { SalesPivotRepository } from './shared/api/salesPivot.repository';
export { salesPivotRepository, MockSalesPivotRepository } from './shared/api/salesPivot.repository';
export * from './shared/ui';

// ========== Header Slice ==========
export { SalesPivotHeader } from './header/ui/SalesPivotHeader';
export { useHeaderViewModel } from './header/model/useHeaderViewModel';
export type { UseHeaderViewModelParams, UseHeaderViewModelResult } from './header/model/useHeaderViewModel';

// ========== Filters Slice ==========
export { FilterPanel } from './filters/ui/FilterPanel';
export { useFiltersViewModel } from './filters/model/useFiltersViewModel';
export { useMasters } from './filters/model/useMasters';
export type { UseFiltersViewModelParams, UseFiltersViewModelResult } from './filters/model/useFiltersViewModel';
export type { UseMastersResult } from './filters/model/useMasters';

// ========== KPI Slice ==========
export { KpiCards } from './kpi/ui/KpiCards';
export { useKpiViewModel } from './kpi/model/useKpiViewModel';
export type { UseKpiViewModelParams, UseKpiViewModelResult } from './kpi/model/useKpiViewModel';

// ========== Summary Table Slice ==========
export * from './summary-table/ui';
export { useSummaryViewModel } from './summary-table/model/useSummaryViewModel';
export type { UseSummaryViewModelParams, UseSummaryViewModelResult } from './summary-table/model/useSummaryViewModel';

// ========== Pivot Drawer Slice ==========
export * from './pivot-drawer/ui';
export { usePivotViewModel } from './pivot-drawer/model/usePivotViewModel';
export type { UsePivotViewModelParams, UsePivotViewModelResult } from './pivot-drawer/model/usePivotViewModel';

// ========== Export Menu Slice ==========
export * from './export-menu/ui';

// ========== Detail Chart Slice ==========
export * from './detail-chart/ui';

// （旧）統合ページ `SalesPivotBoardPage` は削除済み（2025-11-20）
