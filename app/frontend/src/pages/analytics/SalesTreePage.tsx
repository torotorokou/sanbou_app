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
import dayjs, { type Dayjs } from 'dayjs';
import type {
  Mode,
  SortKey,
  SortOrder,
  ID,
  YYYYMM,
  SummaryQuery,
  SummaryRow,
  MetricEntry,
  ExportOptions,
  DailyPoint,
} from '@/features/analytics/sales-pivot/shared/model/types';
import { axesFromMode, axisLabel, monthDays, allDaysInRange } from '@/features/analytics/sales-pivot/shared/model/metrics';
import { HttpSalesPivotRepository } from '@/features/analytics/sales-pivot/shared/api/salesPivot.repository';
import { SalesPivotHeader } from '@/features/analytics/sales-pivot/header/ui/SalesPivotHeader';
import { FilterPanel } from '@/features/analytics/sales-pivot/filters/ui/FilterPanel';
import { KpiCards } from '@/features/analytics/sales-pivot/kpi/ui/KpiCards';
import { SummaryTable } from '@/features/analytics/sales-pivot/summary-table/ui/SummaryTable';
import { PivotDrawer } from '@/features/analytics/sales-pivot/pivot-drawer/ui/PivotDrawer';
import './SalesTreePage.css';

// Repository（実API連携版）
const repository = new HttpSalesPivotRepository();

// ダウンロードヘルパー
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// デフォルトのExportOptions
const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  addAxisB: false,
  addAxisC: false,
  excludeZero: true,
  splitBy: 'none',
};

/**
 * 売上ツリーページ
 */
const SalesTreePage: React.FC = () => {
  const appContext = App.useApp?.();
  const message = appContext?.message;

  // Period
  const [periodMode, setPeriodMode] = useState<'single' | 'range'>('single');
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);

  // Controls
  const [mode, setMode] = useState<Mode>('customer');
  const [topN, setTopN] = useState<10 | 20 | 50 | 'all'>('all');
  const [sortBy, setSortBy] = useState<SortKey>('amount');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]);

  // Export options
  const [exportOptions, setExportOptions] = useState<ExportOptions>(() => {
    try {
      const raw = localStorage.getItem('exportOptions_v1');
      return raw ? (JSON.parse(raw) as ExportOptions) : DEFAULT_EXPORT_OPTIONS;
    } catch {
      return DEFAULT_EXPORT_OPTIONS;
    }
  });

  useEffect(() => {
    localStorage.setItem('exportOptions_v1', JSON.stringify(exportOptions));
  }, [exportOptions]);

  // Data
  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Drawer (pivot)
  type DrawerState =
    | { open: false }
    | {
        open: true;
        baseAxis: Mode;
        baseId: ID;
        baseName: string;
        month?: YYYYMM;
        monthRange?: { from: YYYYMM; to: YYYYMM };
        repIds: ID[];
        targets: { axis: Mode; label: string }[];
        activeAxis: Mode;
        sortBy: SortKey;
        order: SortOrder;
        topN: 10 | 20 | 50 | 'all';
      };
  const [drawer, setDrawer] = useState<DrawerState>({ open: false });

  const [pivotData, setPivotData] = useState<Record<Mode, MetricEntry[]>>({
    customer: [],
    item: [],
    date: [],
  });
  const [pivotCursor, setPivotCursor] = useState<Record<Mode, string | null>>({
    customer: null,
    item: null,
    date: null,
  });
  const [pivotLoading, setPivotLoading] = useState<boolean>(false);

  const [repSeriesCache, setRepSeriesCache] = useState<Record<ID, DailyPoint[]>>({});

  // Query materialize
  const query: SummaryQuery = useMemo(() => {
    const base = { mode, repIds, filterIds, sortBy, order, topN };
    if (periodMode === 'single') return { ...base, month: month.format('YYYY-MM') };
    if (range)
      return {
        ...base,
        monthRange: { from: range[0].format('YYYY-MM'), to: range[1].format('YYYY-MM') },
      };
    return { ...base, month: month.format('YYYY-MM') };
  }, [periodMode, month, range, mode, repIds, filterIds, sortBy, order, topN]);

  // Load
  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await repository.fetchSummary(query);
      setSummary(rows);
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    reload();
  }, [query]);

  // マスタデータ
  const [reps, setReps] = useState<Array<{ id: ID; name: string }>>([]);
  const [customers, setCustomers] = useState<Array<{ id: ID; name: string }>>([]);
  const [items, setItems] = useState<Array<{ id: ID; name: string }>>([]);

  useEffect(() => {
    const loadMasters = async () => {
      const [repData, custData, itemData] = await Promise.all([
        repository.getSalesReps(),
        repository.getCustomers(),
        repository.getItems(),
      ]);
      setReps(repData);
      setCustomers(custData);
      setItems(itemData);
    };
    loadMasters();
  }, []);

  const repOptions = useMemo(
    () => reps.map((r) => ({ label: r.name, value: r.id })),
    [reps]
  );

  const filterOptions = useMemo(() => {
    if (mode === 'customer') return customers.map((c) => ({ label: c.name, value: c.id }));
    if (mode === 'item') return items.map((i) => ({ label: i.name, value: i.id }));
    
    // date mode
    const days = query.monthRange
      ? allDaysInRange(query.monthRange)
      : monthDays(query.month!);
    return days.map((d) => ({ label: d.name, value: d.id }));
  }, [mode, query, customers, items]);

  // 残り2軸の候補リスト
  const [baseAx, axB, axC] = useMemo(() => axesFromMode(mode), [mode]);

  // Header totals
  const headerTotals = useMemo(() => {
    const flat = summary.flatMap((r) => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { amount, qty, count, unit };
  }, [summary]);

  // 選択営業名（KPIタイトル表示用）
  const selectedRepLabel = useMemo(() => {
    if (repIds.length === 0) return '未選択';
    const names = reps.filter((r) => repIds.includes(r.id)).map((r) => r.name);
    return names.length <= 3 ? names.join('・') : `${names.slice(0, 3).join('・')} ほか${names.length - 3}名`;
  }, [repIds, reps]);

  // 期間ラベル
  const periodLabel = useMemo(() => {
    return periodMode === 'single'
      ? month.format('YYYYMM')
      : `${(range?.[0] ?? dayjs()).format('YYYYMM')}-${(range?.[1] ?? dayjs()).format('YYYYMM')}`;
  }, [periodMode, month, range]);

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
      { label: '売単価', value: 'unit_price' as SortKey },
    ];
  }, [mode]);

  // Mode switch
  const switchMode = (m: Mode) => {
    setMode(m);
    setFilterIds([]);
  };

  // Pivot drawer
  const openPivot = (rec: MetricEntry) => {
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
      repIds,
      targets,
      activeAxis: firstTarget?.axis ?? mode,
      sortBy,
      order,
      topN,
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
    [drawer, pivotCursor]
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
  ]);

  // 日次推移データ取得
  const loadDailySeries = async (repId: ID) => {
    if (repSeriesCache[repId]) return;
    const s = await repository.fetchDailySeries(
      query.month ? { month: query.month, repId } : { monthRange: query.monthRange!, repId }
    );
    setRepSeriesCache((prev) => ({ ...prev, [repId]: s }));
  };

  return (
    <Space direction="vertical" size="large" style={{ display: 'block' }} className="sales-tree-page">
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
        topN={topN}
        sortBy={sortBy}
        order={order}
        onModeChange={switchMode}
        onTopNChange={setTopN}
        onSortByChange={setSortBy}
        onOrderChange={setOrder}
        repIds={repIds}
        filterIds={filterIds}
        reps={reps}
        repOptions={repOptions}
        filterOptions={filterOptions}
        sortKeyOptions={sortKeyOptions}
        onRepIdsChange={setRepIds}
        onFilterIdsChange={setFilterIds}
      />

      {/* KPI */}
      <KpiCards
        totalAmount={headerTotals.amount}
        totalQty={headerTotals.qty}
        totalCount={headerTotals.count}
        avgUnitPrice={headerTotals.unit}
        selectedRepLabel={selectedRepLabel}
        hasSelection={repIds.length > 0}
      />

      {/* Summary Table */}
      <SummaryTable
        data={summary}
        loading={loading}
        mode={mode}
        topN={topN}
        hasSelection={repIds.length > 0}
        onRowClick={openPivot}
        repSeriesCache={repSeriesCache}
        loadDailySeries={loadDailySeries}
        sortBy={sortBy}
        order={order}
        onSortChange={(sb, ord) => {
          setSortBy(sb as SortKey);
          setOrder(ord);
        }}
        query={query}
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
      />
    </Space>
  );
};

export default SalesTreePage;
