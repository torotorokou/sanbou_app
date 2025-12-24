/**
 * useSalesTreePage.ts
 * SalesTreePageの状態・ロジックを統合する複合フック
 * 
 * 責務:
 * - 各種状態フックの統合
 * - データ取得フックの統合
 * - アクションハンドラーの統合
 */

import { useCallback } from 'react';
import { App } from 'antd';
import dayjs from 'dayjs';

import type { Mode, SortKey, SortOrder } from '@/features/analytics/sales-pivot/shared/model/types';

// State Hooks
import { useCategoryKindState } from '@/features/analytics/sales-pivot/shared/model/useCategoryKindState';
import { useRepository } from '@/features/analytics/sales-pivot/shared/model/useRepository';
import { usePeriodState } from '@/features/analytics/sales-pivot/shared/model/usePeriodState';
import { useFilterState } from '@/features/analytics/sales-pivot/shared/model/useFilterState';
import { useExportOptions } from '@/features/analytics/sales-pivot/shared/model/useExportOptions';
import { usePivotDrawerState } from '@/features/analytics/sales-pivot/shared/model/usePivotDrawerState';
import { useDetailDrawerState } from '@/features/analytics/sales-pivot/shared/model/useDetailDrawerState';

// Data Hooks
import { useMasterData } from '@/features/analytics/sales-pivot/shared/model/useMasterData';
import { useDataLoading } from '@/features/analytics/sales-pivot/shared/model/useDataLoading';
import { useQueryBuilder } from '@/features/analytics/sales-pivot/shared/model/useQueryBuilder';

// Computed Hooks
import { useSortedSummary } from '@/features/analytics/sales-pivot/shared/model/useSortedSummary';
import { useFilterOptions } from '@/features/analytics/sales-pivot/shared/model/useFilterOptions';
import { useComputedLabels } from '@/features/analytics/sales-pivot/shared/model/useComputedLabels';
import { useAxesFromMode } from '@/features/analytics/sales-pivot/shared/model/useAxesFromMode';
import { useSortKeyOptions } from '@/features/analytics/sales-pivot/shared/model/useSortKeyOptions';

// Action Hooks
import { useEventHandlers } from '@/features/analytics/sales-pivot/shared/model/useEventHandlers';
import { useDetailDrawerLoader } from '@/features/analytics/sales-pivot/shared/model/useDetailDrawerLoader';
import { usePivotLoader } from '@/features/analytics/sales-pivot/shared/model/usePivotLoader';
import { useOpenPivot } from '@/features/analytics/sales-pivot/shared/model/useOpenPivot';
import { useExportHandler } from '@/features/analytics/sales-pivot/shared/model/useExportHandler';
import { useDailySeriesLoader } from '@/features/analytics/sales-pivot/shared/model/useDailySeriesLoader';
import { usePivotRowClickHandler } from '@/features/analytics/sales-pivot/shared/model/usePivotRowClickHandler';

/**
 * SalesTreePageの全状態・ロジックを統合するフック
 */
export function useSalesTreePage() {
  const appContext = App.useApp?.();
  const message = appContext?.message;

  // ========================================
  // Core State
  // ========================================
  const { categoryKind, setCategoryKind } = useCategoryKindState('waste');
  const repository = useRepository(categoryKind);
  const periodState = usePeriodState();
  const filterState = useFilterState();
  const { exportOptions, setExportOptions } = useExportOptions();

  // ========================================
  // Drawer State
  // ========================================
  const pivotDrawerState = usePivotDrawerState();
  const detailDrawerState = useDetailDrawerState();

  // ========================================
  // Query Building
  // ========================================
  const query = useQueryBuilder({
    granularity: periodState.granularity,
    periodMode: periodState.periodMode,
    month: periodState.month,
    range: periodState.range,
    singleDate: periodState.singleDate,
    dateRange: periodState.dateRange,
    mode: filterState.mode,
    categoryKind,
    repIds: filterState.repIds,
    filterIds: filterState.filterIds,
    filterSortBy: filterState.filterSortBy,
    filterOrder: filterState.filterOrder,
    filterTopN: filterState.filterTopN,
  });

  // ========================================
  // Data Loading
  // ========================================
  const { rawSummary, loading } = useDataLoading(repository, query);
  const summary = useSortedSummary(rawSummary, filterState.tableSortBy, filterState.tableOrder);

  const { reps, customers, items } = useMasterData(repository, categoryKind, (msg) => {
    message?.error?.(msg);
  });

  // ========================================
  // Computed Values
  // ========================================
  const { repOptions, filterOptions } = useFilterOptions(
    filterState.mode, query, reps, customers, items
  );

  const { periodLabel, headerTotals, selectedRepLabel } = useComputedLabels(
    periodState.granularity,
    periodState.periodMode,
    periodState.month,
    periodState.range,
    periodState.singleDate,
    periodState.dateRange,
    summary,
    filterState.repIds,
    reps
  );

  const { baseAx, axB, axC } = useAxesFromMode(filterState.mode);
  const sortKeyOptions = useSortKeyOptions(filterState.mode);

  // ========================================
  // Action Handlers
  // ========================================
  const { switchMode } = useEventHandlers({
    setMode: filterState.setMode,
    setFilterIds: filterState.setFilterIds,
  });

  const { openDetailDrawer } = useDetailDrawerLoader({
    query,
    categoryKind,
    repository,
    setDetailDrawerOpen: detailDrawerState.setDetailDrawerOpen,
    setDetailDrawerLoading: detailDrawerState.setDetailDrawerLoading,
    setDetailDrawerTitle: detailDrawerState.setDetailDrawerTitle,
    setDetailDrawerMode: detailDrawerState.setDetailDrawerMode,
    setDetailDrawerRows: detailDrawerState.setDetailDrawerRows,
    setDetailDrawerTotalCount: detailDrawerState.setDetailDrawerTotalCount,
    message,
  });

  const { loadPivot } = usePivotLoader({
    drawer: pivotDrawerState.drawer,
    pivotCursor: pivotDrawerState.pivotCursor,
    categoryKind,
    repository,
    setPivotData: pivotDrawerState.setPivotData,
    setPivotCursor: pivotDrawerState.setPivotCursor,
    setPivotLoading: pivotDrawerState.setPivotLoading,
  });

  const { openPivot } = useOpenPivot({
    mode: filterState.mode,
    query,
    filterSortBy: filterState.filterSortBy,
    filterOrder: filterState.filterOrder,
    filterTopN: filterState.filterTopN,
    setDrawer: pivotDrawerState.setDrawer,
    setPivotData: pivotDrawerState.setPivotData,
    setPivotCursor: pivotDrawerState.setPivotCursor,
  });

  const { handleExport } = useExportHandler({
    repository,
    query,
    exportOptions,
    repIds: filterState.repIds,
    baseAx,
    periodLabel,
    message,
  });

  const { loadDailySeries } = useDailySeriesLoader({
    repository,
    query,
    categoryKind,
    repSeriesCache: pivotDrawerState.repSeriesCache,
    setRepSeriesCache: pivotDrawerState.setRepSeriesCache,
  });

  const { handlePivotRowClick } = usePivotRowClickHandler({
    drawer: pivotDrawerState.drawer,
    openDetailDrawer,
  });

  // ========================================
  // Reset Handler
  // ========================================
  const handleReset = useCallback(() => {
    // 期間をリセット
    periodState.setGranularity('month');
    periodState.setPeriodMode('single');
    periodState.setMonth(dayjs().startOf('month'));
    periodState.setRange(null);
    periodState.setSingleDate(dayjs());
    periodState.setDateRange(null);
    
    // フィルターをリセット
    filterState.setMode('customer');
    filterState.setFilterTopN('all');
    filterState.setFilterSortBy('amount');
    filterState.setFilterOrder('desc');
    filterState.setRepIds([]);
    filterState.setFilterIds([]);
    filterState.setTableSortBy('amount');
    filterState.setTableOrder('desc');
  }, [periodState, filterState]);

  // ========================================
  // Table Sort Handler
  // ========================================
  const handleTableSortChange = useCallback((sortBy: string, order: SortOrder) => {
    filterState.setTableSortBy(sortBy as SortKey);
    filterState.setTableOrder(order);
  }, [filterState]);

  // ========================================
  // Pivot Drawer Handlers
  // ========================================
  const handlePivotDrawerClose = useCallback(() => {
    pivotDrawerState.setDrawer({ open: false });
  }, [pivotDrawerState]);

  const handleActiveAxisChange = useCallback((axis: Mode) => {
    pivotDrawerState.setDrawer((prev) => 
      prev.open ? { ...prev, activeAxis: axis } : prev
    );
  }, [pivotDrawerState]);

  const handlePivotTopNChange = useCallback((topN: 10 | 20 | 50 | 'all') => {
    pivotDrawerState.setDrawer((prev) => 
      prev.open ? { ...prev, topN } : prev
    );
  }, [pivotDrawerState]);

  const handlePivotSortByChange = useCallback((sortBy: SortKey) => {
    pivotDrawerState.setDrawer((prev) => 
      prev.open ? { ...prev, sortBy } : prev
    );
  }, [pivotDrawerState]);

  const handlePivotOrderChange = useCallback((order: SortOrder) => {
    pivotDrawerState.setDrawer((prev) => 
      prev.open ? { ...prev, order } : prev
    );
  }, [pivotDrawerState]);

  const handleDetailDrawerClose = useCallback(() => {
    detailDrawerState.setDetailDrawerOpen(false);
  }, [detailDrawerState]);

  // ========================================
  // Return
  // ========================================
  return {
    // Core State
    categoryKind,
    setCategoryKind,
    
    // Period State (展開)
    ...periodState,
    
    // Filter State (展開)
    ...filterState,
    
    // Export
    exportOptions,
    setExportOptions,
    
    // Query
    query,
    
    // Data
    summary,
    loading,
    reps,
    
    // Computed
    repOptions,
    filterOptions,
    periodLabel,
    headerTotals,
    selectedRepLabel,
    baseAx,
    axB,
    axC,
    sortKeyOptions,
    
    // Pivot Drawer
    drawer: pivotDrawerState.drawer,
    pivotData: pivotDrawerState.pivotData,
    pivotCursor: pivotDrawerState.pivotCursor,
    pivotLoading: pivotDrawerState.pivotLoading,
    repSeriesCache: pivotDrawerState.repSeriesCache,
    
    // Detail Drawer
    detailDrawerOpen: detailDrawerState.detailDrawerOpen,
    detailDrawerLoading: detailDrawerState.detailDrawerLoading,
    detailDrawerTitle: detailDrawerState.detailDrawerTitle,
    detailDrawerMode: detailDrawerState.detailDrawerMode,
    detailDrawerRows: detailDrawerState.detailDrawerRows,
    detailDrawerTotalCount: detailDrawerState.detailDrawerTotalCount,
    
    // Handlers
    switchMode,
    handleReset,
    handleTableSortChange,
    openPivot,
    loadPivot,
    loadDailySeries,
    handleExport,
    handlePivotRowClick,
    
    // Drawer Handlers
    handlePivotDrawerClose,
    handleActiveAxisChange,
    handlePivotTopNChange,
    handlePivotSortByChange,
    handlePivotOrderChange,
    handleDetailDrawerClose,
  };
}

