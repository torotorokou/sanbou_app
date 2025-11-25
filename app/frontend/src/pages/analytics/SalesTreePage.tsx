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

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Space, App } from 'antd';
import type {
  Mode,
  SortKey,
  ID,
  SummaryQuery,
  MetricEntry,
  CategoryKind,
  DetailLinesFilter,
  GroupBy,
} from '@/features/analytics/sales-pivot/shared/model/types';
import { axesFromMode, axisLabel } from '@/features/analytics/sales-pivot/shared/model/metrics';
import { downloadBlob } from '@/features/analytics/sales-pivot/shared/lib/utils';
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
  const [categoryKind, setCategoryKind] = useState<CategoryKind>('waste');

  // Repository（categoryKindに応じて自動設定）
  const repository = useRepository(categoryKind);

  // Period（期間状態管理）
  const { periodMode, month, range, setPeriodMode, setMonth, setRange } = usePeriodState();

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
  const baseQuery: SummaryQuery = useMemo(() => {
    const base = { mode, categoryKind, repIds, filterIds, sortBy: filterSortBy, order: filterOrder, topN: filterTopN };
    if (periodMode === 'single') return { ...base, month: month.format('YYYY-MM') };
    if (range)
      return {
        ...base,
        monthRange: { from: range[0].format('YYYY-MM'), to: range[1].format('YYYY-MM') },
      };
    return { ...base, month: month.format('YYYY-MM') };
  }, [periodMode, month, range, mode, categoryKind, repIds, filterIds, filterSortBy, filterOrder, filterTopN]);

  // Data loading
  const { rawSummary, loading } = useDataLoading(repository, baseQuery);

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

  // エクスポート用のクエリ（フィルターパネルの条件を使用）
  const query: SummaryQuery = useMemo(() => {
    return { ...baseQuery };
  }, [baseQuery]);

  // マスタデータ
  const { reps, customers, items } = useMasterData(repository, categoryKind, (msg) => {
    message?.error?.(msg);
  });

  // フィルターオプション
  const { repOptions, filterOptions } = useFilterOptions(mode, query, reps, customers, items);

  // 計算済みラベルと集計値
  const { periodLabel, headerTotals, selectedRepLabel } = useComputedLabels(
    periodMode,
    month,
    range,
    summary,
    repIds,
    reps
  );

  // 残り2軸の候補リスト
  const [baseAx, axB, axC] = useMemo(() => axesFromMode(mode), [mode]);

  // CSV Export
  const handleExport = async () => {
    if (repIds.length === 0) return;
    try {
      const blob = await repository.exportModeCube({
        ...query,
        options: exportOptions,
        targetRepIds: repIds,
      });
      downloadBlob(blob, `csv_${axisLabel(baseAx)}_${periodLabel}.csv`);
      message?.success?.('CSVを出力しました。');
    } catch (e) {
      console.error(e);
      message?.error?.('CSV出力でエラーが発生しました。');
    }
  };

  // Sort options
  const sortKeyOptions = useMemo(() => {
    return [
      { label: mode === 'date' ? '日付' : '名称', value: (mode === 'date' ? 'date' : 'name') as SortKey },
      { label: '売上', value: 'amount' as SortKey },
      { label: '数量', value: 'qty' as SortKey },
      { label: '件数', value: 'count' as SortKey },
      { label: '単価', value: 'unit_price' as SortKey },
    ];
  }, [mode]);

  // Mode switch
  const switchMode = useCallback((m: Mode) => {
    setMode(m);
    setFilterIds([]);
  }, []);

  // Pivot drawer
  const openPivot = (rec: MetricEntry, repId: ID) => {
    const others = (['customer', 'item', 'date'] as Mode[]).filter((ax) => ax !== mode);
    const targets: { axis: Mode; label: string }[] = others.map((ax) => ({
      axis: ax,
      label: axisLabel(ax),
    }));
    const firstTarget = targets[0];

    const drawerState: Extract<DrawerState, { open: true }> = {
      open: true,
      baseAxis: mode,
      baseId: rec.id,
      baseName: rec.name,
      repIds: [repId],
      targets,
      activeAxis: firstTarget?.axis ?? mode,
      sortBy: filterSortBy,
      order: filterOrder,
      topN: filterTopN,
      ...(query.monthRange ? { monthRange: query.monthRange } : { month: query.month }),
    };

    setDrawer(drawerState);
    setPivotData({ customer: [], item: [], date: [] });
    setPivotCursor({ customer: null, item: null, date: null });
  };

  const loadPivot = useCallback(
    async (axis: Mode, reset = false) => {
      if (!drawer.open) return;
      const {
        baseAxis,
        baseId,
        repIds: drawerRepIds,
        sortBy: drawerSortBy,
        order: drawerOrder,
        topN: drawerTopN,
        month,
        monthRange,
      } = drawer;
      const targetAxis = axis;
      if (targetAxis === baseAxis) return;
      
      setPivotLoading(true);
      try {
        const periodParams = monthRange ? { monthRange } : { month };
        const page = await repository.fetchPivot({
          ...periodParams,
          baseAxis,
          baseId,
          categoryKind,
          repIds: drawerRepIds,
          targetAxis,
          sortBy: drawerSortBy,
          order: drawerOrder,
          topN: drawerTopN,
          cursor: reset ? null : pivotCursor[targetAxis],
        });
        setPivotData((prev) => ({
          ...prev,
          [targetAxis]: reset ? page.rows : prev[targetAxis].concat(page.rows),
        }));
        setPivotCursor((prev) => ({ ...prev, [targetAxis]: page.next_cursor }));
      } finally {
        setPivotLoading(false);
      }
    },
    [drawer, pivotCursor, categoryKind]
  );

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

  // 日次推移データ取得
  const loadDailySeries = async (repId: ID) => {
    if (repSeriesCache[repId]) return;
    const s = await repository.fetchDailySeries(
      query.month 
        ? { month: query.month, categoryKind, repId } 
        : { monthRange: query.monthRange!, categoryKind, repId }
    );
    setRepSeriesCache((prev) => ({ ...prev, [repId]: s }));
  };

  // 詳細Drawer を開く（内部処理）
  const openDetailDrawer = useCallback(async (
    lastGroupBy: GroupBy,
    repId?: string,
    customerId?: string,
    itemId?: string,
    dateValue?: string,
    title?: string
  ) => {
    setDetailDrawerLoading(true);
    setDetailDrawerOpen(true);
    setDetailDrawerTitle(title || '詳細明細');
    
    try {
      // 期間計算（月末日を正確に計算）
      let dateFrom: string;
      let dateTo: string;
      
      const getMonthEndDate = (yyyymm: string): string => {
        const [year, month] = yyyymm.split('-').map(Number);
        const nextMonth = new Date(year, month, 1);
        const lastDay = new Date(nextMonth.getTime() - 86400000);
        const dd = String(lastDay.getDate()).padStart(2, '0');
        return `${yyyymm}-${dd}`;
      };
      
      if (query.monthRange) {
        dateFrom = `${query.monthRange.from}-01`;
        dateTo = getMonthEndDate(query.monthRange.to);
      } else if (query.month) {
        dateFrom = `${query.month}-01`;
        dateTo = getMonthEndDate(query.month);
      } else {
        throw new Error('期間が設定されていません');
      }

      const filter: DetailLinesFilter = {
        dateFrom,
        dateTo,
        lastGroupBy,
        categoryKind,
        repId: repId ? parseInt(repId, 10) : undefined,
        customerId,
        itemId: itemId ? parseInt(itemId, 10) : undefined,
        dateValue,
      };

      console.log('📋 詳細明細取得リクエスト:', filter);

      const response = await repository.fetchDetailLines(filter);
      
      console.log('✅ 詳細明細取得成功:', {
        mode: response.mode,
        rowCount: response.rows.length,
        totalCount: response.totalCount
      });
      
      setDetailDrawerMode(response.mode);
      setDetailDrawerRows(response.rows);
      setDetailDrawerTotalCount(response.totalCount);
    } catch (error) {
      console.error('❌ 詳細明細取得エラー:', error);
      message?.error?.('詳細明細の取得に失敗しました。');
      setDetailDrawerOpen(false);
    } finally {
      setDetailDrawerLoading(false);
    }
  }, [query, categoryKind, repository, message]);

  // Pivot行クリック時のハンドラー
  const handlePivotRowClick = useCallback(async (row: MetricEntry, axis: Mode) => {
    if (!drawer.open) return;
    
    // 現在のDrawer状態から必要な情報を取得
    const { baseAxis, baseId, repIds } = drawer;
    
    // 集計パスの構築: baseAxis → activeAxis → クリックした行の軸
    // 例: 顧客(base) → 品名(active) → 行をクリック
    // lastGroupBy = activeAxis (クリックされたタブの軸)
    const lastGroupBy = axis as GroupBy;
    
    // フィルタ条件を構築
    const repId = repIds[0]; // 最初の営業IDを使用
    let customerId: string | undefined;
    let itemId: string | undefined;
    let dateValue: string | undefined;
    
    // baseAxisに応じてフィルタを設定
    if (baseAxis === 'customer') {
      customerId = baseId;
    } else if (baseAxis === 'item') {
      itemId = baseId;
    } else if (baseAxis === 'date') {
      dateValue = baseId;
    }
    
    // activeAxis（クリックされた行の軸）に応じてフィルタを追加
    if (axis === 'customer') {
      customerId = row.id;
    } else if (axis === 'item') {
      itemId = row.id;
    } else if (axis === 'date') {
      dateValue = row.id;
    }
    
    console.log('🔍 Pivot行クリック:', {
      baseAxis,
      baseId,
      clickedAxis: axis,
      clickedRow: { id: row.id, name: row.name },
      lastGroupBy,
      filters: { repId, customerId, itemId, dateValue }
    });
    
    // タイトル構築
    const title = `${row.name} の詳細明細`;
    
    await openDetailDrawer(lastGroupBy, repId, customerId, itemId, dateValue, title);
  }, [drawer, openDetailDrawer]);

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
        periodMode={periodMode}
        month={month}
        range={range}
        onPeriodModeChange={setPeriodMode}
        onMonthChange={setMonth}
        onRangeChange={setRange}
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
