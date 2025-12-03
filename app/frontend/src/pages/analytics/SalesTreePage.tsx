/**
 * pages/analytics/SalesTreePage.tsx
 * 売上ツリー分析ページ
 * 
 * ページレベルの責務：
 * - ページレイアウト・構成
 * - 各機能sliceの統合
 * - ページタイトル・メタ情報
 * 
 * ビジネスロジックは features/analytics/sales-pivot の各sliceに分離済み
 * 
 * リファクタリング完了（2025-11-20）:
 * - 8つの機能slice化（header/filters/kpi/summary-table/pivot-drawer/export-menu/detail-chart/shared）
 * - 各sliceが独立したViewModel(Hooks)とUIを持つ
 * - 共通UIコンポーネント層（SortBadge/MiniBarChart/EmptyStateCard/styles）
 * - 完全なslice統合実装完了
 */

import React, { useEffect } from 'react';
import { Space, App } from 'antd';
import dayjs from 'dayjs';
import type {
  Mode,
  SortKey,
} from '@/features/analytics/sales-pivot/shared/model/types';
import { useRepository } from '@/features/analytics/sales-pivot/shared/model/useRepository';
import { usePeriodState } from '@/features/analytics/sales-pivot/shared/model/usePeriodState';
import { useFilterState } from '@/features/analytics/sales-pivot/shared/model/useFilterState';
import { useExportOptions } from '@/features/analytics/sales-pivot/shared/model/useExportOptions';
import { useMasterData } from '@/features/analytics/sales-pivot/shared/model/useMasterData';
import { useDetailDrawerState } from '@/features/analytics/sales-pivot/shared/model/useDetailDrawerState';
import { useDataLoading } from '@/features/analytics/sales-pivot/shared/model/useDataLoading';
import { useSortedSummary } from '@/features/analytics/sales-pivot/shared/model/useSortedSummary';
import { useFilterOptions } from '@/features/analytics/sales-pivot/shared/model/useFilterOptions';
import { usePivotDrawerState, type DrawerState } from '@/features/analytics/sales-pivot/shared/model/usePivotDrawerState';
import { useComputedLabels } from '@/features/analytics/sales-pivot/shared/model/useComputedLabels';
import { useCategoryKindState } from '@/features/analytics/sales-pivot/shared/model/useCategoryKindState';
import { useEventHandlers } from '@/features/analytics/sales-pivot/shared/model/useEventHandlers';
import { useSortKeyOptions } from '@/features/analytics/sales-pivot/shared/model/useSortKeyOptions';
import { useQueryBuilder } from '@/features/analytics/sales-pivot/shared/model/useQueryBuilder';
import { useAxesFromMode } from '@/features/analytics/sales-pivot/shared/model/useAxesFromMode';
import { useDetailDrawerLoader } from '@/features/analytics/sales-pivot/shared/model/useDetailDrawerLoader';
import { usePivotLoader } from '@/features/analytics/sales-pivot/shared/model/usePivotLoader';
import { useOpenPivot } from '@/features/analytics/sales-pivot/shared/model/useOpenPivot';
import { useExportHandler } from '@/features/analytics/sales-pivot/shared/model/useExportHandler';
import { useDailySeriesLoader } from '@/features/analytics/sales-pivot/shared/model/useDailySeriesLoader';
import { usePivotRowClickHandler } from '@/features/analytics/sales-pivot/shared/model/usePivotRowClickHandler';
import { SalesPivotHeader } from '@/features/analytics/sales-pivot/header/ui/SalesPivotHeader';
import { FilterPanel } from '@/features/analytics/sales-pivot/filters/ui/FilterPanel';
import { KpiCards } from '@/features/analytics/sales-pivot/kpi/ui/KpiCards';
import { SummaryTable } from '@/features/analytics/sales-pivot/summary-table/ui/SummaryTable';
import { PivotDrawer } from '@/features/analytics/sales-pivot/pivot-drawer/ui/PivotDrawer';
import { DetailDrawer } from '@/features/analytics/sales-pivot/detail-drawer/ui/DetailDrawer';
import './SalesTreePage.css';

/**
 * 売上ツリーページ
 */
const SalesTreePage: React.FC = () => {
  const appContext = App.useApp?.();
  const message = appContext?.message;

  // CategoryKind state (廃棄物/有価物タブ)
  const { categoryKind, setCategoryKind } = useCategoryKindState('waste');

  // Repository（categoryKindに応じて自動設定）
  const repository = useRepository(categoryKind);

  // Period（期間状態管理）
  const { granularity, periodMode, month, range, singleDate, dateRange, setGranularity, setPeriodMode, setMonth, setRange, setSingleDate, setDateRange } = usePeriodState();

  // Filters（フィルター状態管理）
  const {
    mode,
    filterTopN,
    filterSortBy,
    filterOrder,
    repIds,
    filterIds,
    setMode,
    setFilterTopN,
    setFilterSortBy,
    setFilterOrder,
    setRepIds,
    setFilterIds,
    tableSortBy,
    tableOrder,
    setTableSortBy,
    setTableOrder,
  } = useFilterState();

  // Export options（localStorage連携）
  const { exportOptions, setExportOptions } = useExportOptions();

  // Query materialize (API用 - フィルターパネルの条件）
  const query = useQueryBuilder({
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    mode,
    categoryKind,
    repIds,
    filterIds,
    filterSortBy,
    filterOrder,
    filterTopN,
  });

  // Data loading
  const { rawSummary, loading } = useDataLoading(repository, query);

  // テーブル用のソート（クライアント側処理）
  const summary = useSortedSummary(rawSummary, tableSortBy, tableOrder);

  // Drawer (pivot)
  const {
    drawer,
    setDrawer,
    pivotData,
    setPivotData,
    pivotCursor,
    setPivotCursor,
    pivotLoading,
    setPivotLoading,
    repSeriesCache,
    setRepSeriesCache,
  } = usePivotDrawerState();

  // Detail Drawer（詳細明細行表示用）
  const {
    detailDrawerOpen,
    detailDrawerLoading,
    detailDrawerTitle,
    detailDrawerMode,
    detailDrawerRows,
    detailDrawerTotalCount,
    setDetailDrawerOpen,
    setDetailDrawerLoading,
    setDetailDrawerTitle,
    setDetailDrawerMode,
    setDetailDrawerRows,
    setDetailDrawerTotalCount,
  } = useDetailDrawerState();

  // マスタデータ
  const { reps, customers, items } = useMasterData(repository, categoryKind, (msg) => {
    message?.error?.(msg);
  });

  // フィルターオプション
  const { repOptions, filterOptions } = useFilterOptions(mode, query, reps, customers, items);

  // 計算済みラベルと集計値
  const { periodLabel, headerTotals, selectedRepLabel } = useComputedLabels(
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    summary,
    repIds,
    reps
  );

  // 軸の取得
  const { baseAx, axB, axC } = useAxesFromMode(mode);

  // 詳細Drawerローダー
  const { openDetailDrawer } = useDetailDrawerLoader({
    query,
    categoryKind,
    repository,
    setDetailDrawerOpen,
    setDetailDrawerLoading,
    setDetailDrawerTitle,
    setDetailDrawerMode,
    setDetailDrawerRows,
    setDetailDrawerTotalCount,
    message,
  });

  // Pivotローダー
  const { loadPivot } = usePivotLoader({
    drawer,
    pivotCursor,
    categoryKind,
    repository,
    setPivotData,
    setPivotCursor,
    setPivotLoading,
  });

  // Pivotドロワーを開く
  const { openPivot } = useOpenPivot({
    mode,
    query,
    filterSortBy,
    filterOrder,
    filterTopN,
    setDrawer,
    setPivotData,
    setPivotCursor,
  });

  // CSV出力ハンドラー
  const { handleExport } = useExportHandler({
    repository,
    query,
    exportOptions,
    repIds,
    baseAx,
    periodLabel,
    message,
  });

  // 日次データローダー
  const { loadDailySeries } = useDailySeriesLoader({
    repository,
    query,
    categoryKind,
    repSeriesCache,
    setRepSeriesCache,
  });

  // Pivot行クリックハンドラー
  const { handlePivotRowClick } = usePivotRowClickHandler({
    drawer,
    openDetailDrawer,
  });

  // Sort options
  const sortKeyOptions = useSortKeyOptions(mode);

  // Mode switch
  const { switchMode } = useEventHandlers({ setMode, setFilterIds });

  // Reset handler - すべての条件を初期状態に戻す
  const handleReset = () => {
    // 期間をリセット
    setGranularity('month');
    setPeriodMode('single');
    setMonth(dayjs().startOf('month'));
    setRange(null);
    setSingleDate(dayjs());
    setDateRange(null);
    
    // フィルターをリセット
    setMode('customer');
    setFilterTopN('all');
    setFilterSortBy('amount');
    setFilterOrder('desc');
    setRepIds([]);
    setFilterIds([]);
    setTableSortBy('amount');
    setTableOrder('desc');
    
    // カテゴリ種別はリセットしない（ユーザーの意図的な選択なので保持）
  };

  const isDrawerOpen = (d: DrawerState): d is Extract<DrawerState, { open: true }> => d.open;

  useEffect(() => {
    if (!isDrawerOpen(drawer)) return;
    loadPivot(drawer.activeAxis, true);
  }, [
    drawer.open,
    isDrawerOpen(drawer) ? drawer.activeAxis : null,
    isDrawerOpen(drawer) ? drawer.sortBy : null,
    isDrawerOpen(drawer) ? drawer.order : null,
    isDrawerOpen(drawer) ? drawer.topN : null,
    categoryKind,
  ]);

  return (
    <Space 
      direction="vertical" 
      size="large" 
      style={{ display: 'block' }} 
      className={`sales-tree-page ${categoryKind === 'valuable' ? 'valuable-mode' : ''}`}
    >
      {/* Header */}
      <SalesPivotHeader
        canExport={repIds.length > 0}
        exportOptions={exportOptions}
        onExportOptionsChange={setExportOptions}
        onExport={handleExport}
        periodLabel={periodLabel}
        baseAx={baseAx}
        axB={axB}
        axC={axC}
        categoryKind={categoryKind}
      />

      {/* Filters */}
      <FilterPanel
        granularity={granularity}
        periodMode={periodMode}
        month={month}
        range={range}
        singleDate={singleDate}
        dateRange={dateRange}
        onGranularityChange={setGranularity}
        onPeriodModeChange={setPeriodMode}
        onMonthChange={setMonth}
        onRangeChange={setRange}
        onSingleDateChange={setSingleDate}
        onDateRangeChange={setDateRange}
        mode={mode}
        topN={filterTopN}
        sortBy={filterSortBy}
        order={filterOrder}
        onModeChange={switchMode}
        onTopNChange={setFilterTopN}
        onSortByChange={setFilterSortBy}
        onOrderChange={setFilterOrder}
        repIds={repIds}
        filterIds={filterIds}
        reps={reps}
        repOptions={repOptions}
        filterOptions={filterOptions}
        sortKeyOptions={sortKeyOptions}
        onRepIdsChange={setRepIds}
        onFilterIdsChange={setFilterIds}
        categoryKind={categoryKind}
        onCategoryKindChange={setCategoryKind}
        onReset={handleReset}
      />

      {/* KPI */}
      <KpiCards
        totalAmount={headerTotals.amount}
        totalQty={headerTotals.qty}
        totalCount={headerTotals.count}
        avgUnitPrice={headerTotals.unit}
        selectedRepLabel={selectedRepLabel}
        hasSelection={repIds.length > 0}
        mode={mode}
        categoryKind={categoryKind}
      />

      {/* Summary Table */}
      <SummaryTable
        data={summary}
        loading={loading}
        mode={mode}
        topN={filterTopN}
        hasSelection={repIds.length > 0}
        onRowClick={openPivot}
        repSeriesCache={repSeriesCache}
        loadDailySeries={loadDailySeries}
        sortBy={tableSortBy}
        order={tableOrder}
        onSortChange={(sb, ord) => {
          setTableSortBy(sb as SortKey);
          setTableOrder(ord);
        }}
        query={query}
        categoryKind={categoryKind}
      />

      {/* Pivot Drawer */}
      <PivotDrawer
        drawer={drawer}
        pivotData={pivotData}
        pivotCursor={pivotCursor}
        pivotLoading={pivotLoading}
        onClose={() => setDrawer({ open: false })}
        onActiveAxisChange={(axis) =>
          setDrawer((prev) => (prev.open ? { ...prev, activeAxis: axis } : prev))
        }
        onTopNChange={(tn) => setDrawer((prev) => (prev.open ? { ...prev, topN: tn } : prev))}
        onSortByChange={(sb) => setDrawer((prev) => (prev.open ? { ...prev, sortBy: sb } : prev))}
        onOrderChange={(ord) => setDrawer((prev) => (prev.open ? { ...prev, order: ord } : prev))}
        onLoadMore={async (axis: Mode, reset: boolean) => loadPivot(axis, reset)}
        categoryKind={categoryKind}
        onRowClick={handlePivotRowClick}
      />

      {/* Detail Drawer (詳細明細行表示) */}
      <DetailDrawer
        open={detailDrawerOpen}
        loading={detailDrawerLoading}
        mode={detailDrawerMode}
        rows={detailDrawerRows}
        totalCount={detailDrawerTotalCount}
        title={detailDrawerTitle}
        categoryKind={categoryKind}
        onClose={() => setDetailDrawerOpen(false)}
      />
    </Space>
  );
};

export default SalesTreePage;
