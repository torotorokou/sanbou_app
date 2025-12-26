/**
 * pages/analytics/SalesTreePage.tsx
 * 売上ツリー分析ページ
 *
 * ページレベルの責務：
 * - ページレイアウト・構成
 * - 各機能sliceの統合
 * - ページタイトル・メタ情報
 *
 * ビジネスロジックは useSalesTreePage フックに統合済み
 */

import React, { useEffect } from "react";
import { Space } from "antd";

// Types
import type { Mode } from "@/features/analytics/sales-pivot/shared/model/types";
import type { DrawerState } from "@/features/analytics/sales-pivot/shared/model/usePivotDrawerState";

// Custom Hook
import { useSalesTreePage } from "./useSalesTreePage";

// UI Components
import { SalesPivotHeader } from "@/features/analytics/sales-pivot/header/ui/SalesPivotHeader";
import { FilterPanel } from "@/features/analytics/sales-pivot/filters/ui/FilterPanel";
import { KpiCards } from "@/features/analytics/sales-pivot/kpi/ui/KpiCards";
import { SummaryTable } from "@/features/analytics/sales-pivot/summary-table/ui/SummaryTable";
import { PivotDrawer } from "@/features/analytics/sales-pivot/pivot-drawer/ui/PivotDrawer";
import { DetailDrawer } from "@/features/analytics/sales-pivot/detail-drawer/ui/DetailDrawer";

// Styles
import styles from "./SalesTreePage.module.css";

/**
 * DrawerStateがopenかどうかを判定する型ガード
 */
const isDrawerOpen = (
  d: DrawerState,
): d is Extract<DrawerState, { open: true }> => d.open;

/**
 * 売上ツリーページ
 */
const SalesTreePage: React.FC = () => {
  const {
    // Core State
    categoryKind,
    setCategoryKind,

    // Period State
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    setGranularity,
    setPeriodMode,
    setMonth,
    setRange,
    setSingleDate,
    setDateRange,

    // Filter State
    mode,
    filterTopN,
    filterSortBy,
    filterOrder,
    repIds,
    filterIds,
    setFilterTopN,
    setFilterSortBy,
    setFilterOrder,
    setRepIds,
    setFilterIds,
    tableSortBy,
    tableOrder,

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
    drawer,
    pivotData,
    pivotCursor,
    pivotLoading,
    repSeriesCache,

    // Detail Drawer
    detailDrawerOpen,
    detailDrawerLoading,
    detailDrawerTitle,
    detailDrawerMode,
    detailDrawerRows,
    detailDrawerTotalCount,

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
  } = useSalesTreePage();

  // Pivot Drawerのデータ読み込み
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
    loadPivot,
  ]);

  return (
    <Space
      direction="vertical"
      size="large"
      style={{ display: "block" }}
      className={`${styles.salesTreePage} ${categoryKind === "valuable" ? styles.valuableMode : ""}`}
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
        onSortChange={handleTableSortChange}
        query={query}
        categoryKind={categoryKind}
      />

      {/* Pivot Drawer */}
      <PivotDrawer
        drawer={drawer}
        pivotData={pivotData}
        pivotCursor={pivotCursor}
        pivotLoading={pivotLoading}
        onClose={handlePivotDrawerClose}
        onActiveAxisChange={handleActiveAxisChange}
        onTopNChange={handlePivotTopNChange}
        onSortByChange={handlePivotSortByChange}
        onOrderChange={handlePivotOrderChange}
        onLoadMore={(axis: Mode, reset: boolean) => loadPivot(axis, reset)}
        categoryKind={categoryKind}
        onRowClick={handlePivotRowClick}
      />

      {/* Detail Drawer */}
      <DetailDrawer
        open={detailDrawerOpen}
        loading={detailDrawerLoading}
        mode={detailDrawerMode}
        rows={detailDrawerRows}
        totalCount={detailDrawerTotalCount}
        title={detailDrawerTitle}
        categoryKind={categoryKind}
        onClose={handleDetailDrawerClose}
      />
    </Space>
  );
};

export default SalesTreePage;
