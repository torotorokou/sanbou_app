/**
 * features/analytics/sales-pivot/index.ts
 * Public API - 機能ごとのsliceをエクスポート
 * 
 * 【概要】
 * 売上ピボット分析機能の公開インターフェース
 * 外部から使用する全てのコンポーネント、Hook、型をエクスポート
 * 
 * 【アーキテクチャ】
 * Feature-Sliced Design (FSD) + MVVM + Repository パターン
 * 
 * 【構成】
 * - shared: 共通層（型定義、Repository、ユーティリティ、共通UI）
 * - header: ヘッダー機能（タイトル、CSV出力）
 * - filters: フィルタ機能（期間、モード、ソート条件）
 * - kpi: KPI集計機能（売上合計、数量合計等）
 * - summary-table: サマリテーブル機能（営業別TopN表示）
 * - pivot-drawer: Pivotドロワー機能（詳細ドリルダウン）
 * - export-menu: CSV出力メニュー
 * - detail-chart: 詳細チャート（TopNバー、日次折れ線）
 * 
 * 【使用例】
 * ```typescript
 * // 型定義のインポート
 * import type { SummaryQuery, MetricEntry } from '@/features/analytics/sales-pivot';
 * 
 * // コンポーネントのインポート
 * import { SalesPivotHeader, FilterPanel, KpiCards } from '@/features/analytics/sales-pivot';
 * 
 * // ViewModelフックのインポート
 * import { useFiltersViewModel, useKpiViewModel } from '@/features/analytics/sales-pivot';
 * 
 * // Repositoryのインポート
 * import { salesPivotRepository } from '@/features/analytics/sales-pivot';
 * ```
 */

// ========== Shared（共通層） ==========
export * from './shared/model/types';
export * from './shared/model/metrics';
export type { SalesPivotRepository } from './shared/api/salesPivot.repository';
export { salesPivotRepository, MockSalesPivotRepository } from './shared/api/salesPivot.repository';
export * from './shared/ui';

// ========== Header Slice（ヘッダー機能） ==========
export { SalesPivotHeader } from './header/ui/SalesPivotHeader';
export { useHeaderViewModel } from './header/model/useHeaderViewModel';
export type { UseHeaderViewModelParams, UseHeaderViewModelResult } from './header/model/useHeaderViewModel';

// ========== Filters Slice（フィルタ機能） ==========
export { FilterPanel } from './filters/ui/FilterPanel';
export { useFiltersViewModel } from './filters/model/useFiltersViewModel';
export { useMasters } from './filters/model/useMasters';
export type { UseFiltersViewModelParams, UseFiltersViewModelResult } from './filters/model/useFiltersViewModel';
export type { UseMastersResult } from './filters/model/useMasters';

// ========== KPI Slice（KPI集計機能） ==========
export { KpiCards } from './kpi/ui/KpiCards';
export { useKpiViewModel } from './kpi/model/useKpiViewModel';
export type { UseKpiViewModelParams, UseKpiViewModelResult } from './kpi/model/useKpiViewModel';

// ========== Summary Table Slice（サマリテーブル機能） ==========
export * from './summary-table/ui';
export { useSummaryViewModel } from './summary-table/model/useSummaryViewModel';
export type { UseSummaryViewModelParams, UseSummaryViewModelResult } from './summary-table/model/useSummaryViewModel';

// ========== Pivot Drawer Slice（Pivotドロワー機能） ==========
export * from './pivot-drawer/ui';
export { usePivotViewModel } from './pivot-drawer/model/usePivotViewModel';
export type { UsePivotViewModelParams, UsePivotViewModelResult } from './pivot-drawer/model/usePivotViewModel';

// ========== Export Menu Slice（CSV出力メニュー） ==========
export * from './export-menu/ui';

// ========== Detail Chart Slice（詳細チャート） ==========
export * from './detail-chart/ui';

/**
 * 【注意】
 * 旧統合ページ `SalesPivotBoardPage` は削除済み（2025-11-20）
 * 現在は必要なスライスの ViewModel Hook と UI コンポーネントを
 * 個別にインポートして使用してください
 */
