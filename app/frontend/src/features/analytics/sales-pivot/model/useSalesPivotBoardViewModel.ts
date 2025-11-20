/**
 * sales-pivot/model/useSalesPivotBoardViewModel.ts
 * Sales Pivot Board のViewModel Hook (MVVM)
 * 
 * 責務:
 * - 画面全体の state 管理
 * - Repository を使ったデータ取得
 * - イベントハンドラの提供
 * - エラー処理
 * 
 * View コンポーネントはこの Hook から返される state と handlers を受け取るだけ
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type {
  Mode,
  SortKey,
  SortOrder,
  ID,
  SummaryRow,
  MetricEntry,
  SummaryQuery,
  DrawerState,
  ExportOptions,
  SalesRep,
  UniverseEntry,
  DailyPoint,
} from '../shared/model/types';
import { DEFAULT_EXPORT_OPTIONS } from '../shared/model/types';
import type { SalesPivotRepository } from '../shared/api/salesPivot.repository';
import { axesFromMode } from '../shared/model/metrics';

/**
 * ViewModel Hook の返り値型
 */
export interface UseSalesPivotBoardViewModelResult {
  // ========== State ==========
  // Period
  periodMode: 'single' | 'range';
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;

  // Controls
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  repIds: ID[];
  filterIds: ID[];

  // Export options
  exportOptions: ExportOptions;

  // Data
  summary: SummaryRow[];
  loading: boolean;

  // Drawer
  drawer: DrawerState;
  pivotData: Record<Mode, MetricEntry[]>;
  pivotCursor: Record<Mode, string | null>;
  pivotLoading: boolean;

  // Daily series cache (for charts)
  repSeriesCache: Record<ID, DailyPoint[]>;

  // Masters
  reps: SalesRep[];
  customers: UniverseEntry[];
  items: UniverseEntry[];

  // ========== Computed ==========
  query: SummaryQuery;
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  headerTotals: { amount: number; qty: number; count: number; unit: number | null };
  selectedRepLabel: string;
  periodLabel: string;
  baseAx: Mode;
  axB: Mode;
  axC: Mode;

  // ========== Handlers ==========
  setPeriodMode: (mode: 'single' | 'range') => void;
  setMonth: (month: Dayjs) => void;
  setRange: (range: [Dayjs, Dayjs] | null) => void;
  switchMode: (mode: Mode) => void;
  setTopN: (topN: 10 | 20 | 50 | 'all') => void;
  setSortBy: (sortBy: SortKey) => void;
  setOrder: (order: SortOrder) => void;
  setRepIds: (ids: ID[]) => void;
  setFilterIds: (ids: ID[]) => void;
  setExportOptions: (options: ExportOptions | ((prev: ExportOptions) => ExportOptions)) => void;
  reload: () => Promise<void>;

  // Drawer handlers
  openPivot: (rec: MetricEntry) => void;
  closeDrawer: () => void;
  setDrawerActiveAxis: (axis: Mode) => void;
  setDrawerTopN: (topN: 10 | 20 | 50 | 'all') => void;
  setDrawerSortBy: (sortBy: SortKey) => void;
  setDrawerOrder: (order: SortOrder) => void;
  loadPivot: (axis: Mode, reset?: boolean) => Promise<void>;

  // Daily series
  loadDailySeries: (repId: ID) => Promise<void>;

  // Export
  handleExport: () => Promise<void>;
}

/**
 * ViewModel Hook
 */
export function useSalesPivotBoardViewModel(
  repository: SalesPivotRepository
): UseSalesPivotBoardViewModelResult {
  // ========== Masters（初期ロード） ==========
  const [reps, setReps] = useState<SalesRep[]>([]);
  const [customers, setCustomers] = useState<UniverseEntry[]>([]);
  const [items, setItems] = useState<UniverseEntry[]>([]);

  useEffect(() => {
    void (async () => {
      const [r, c, i] = await Promise.all([
        repository.getSalesReps(),
        repository.getCustomers(),
        repository.getItems(),
      ]);
      setReps(r);
      setCustomers(c);
      setItems(i);
    })();
  }, [repository]);

  // ========== Period ==========
  const [periodMode, setPeriodMode] = useState<'single' | 'range'>('single');
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);

  // ========== Controls ==========
  const [mode, setMode] = useState<Mode>('customer');
  const [topN, setTopN] = useState<10 | 20 | 50 | 'all'>('all');
  const [sortBy, setSortBy] = useState<SortKey>('amount');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [repIds, setRepIds] = useState<ID[]>([]);
  const [filterIds, setFilterIds] = useState<ID[]>([]);

  // ========== Export options (persist) ==========
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

  // ========== Data ==========
  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // ========== Drawer ==========
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

  // ========== Daily series cache ==========
  const [repSeriesCache, setRepSeriesCache] = useState<Record<ID, DailyPoint[]>>({});

  // ========== Query（MaterializeされたQuery） ==========
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

  // ========== Load Summary ==========
  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await repository.fetchSummary(query);
      setSummary(rows);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  }, [repository, query]);

  useEffect(() => {
    void reload();
  }, [reload]);

  // ========== Select options ==========
  const repOptions = useMemo(
    () => reps.map((r) => ({ label: r.name, value: r.id })),
    [reps]
  );

  const filterOptions = useMemo(() => {
    if (mode === 'customer') return customers.map((c) => ({ label: c.name, value: c.id }));
    if (mode === 'item') return items.map((i) => ({ label: i.name, value: i.id }));
    // date mode: 動的に monthDays を生成（metrics から import）
    // 簡略化のため、ここでは空配列を返す（実際は query に応じて生成）
    return [];
  }, [mode, customers, items]);

  const sortKeyOptions = useMemo(() => {
    return [
      { label: mode === 'date' ? '日付' : '名称', value: (mode === 'date' ? 'date' : 'name') as SortKey },
      { label: '売上', value: 'amount' as SortKey },
      { label: '数量', value: 'qty' as SortKey },
      { label: '台数', value: 'count' as SortKey },
      { label: '売単価', value: 'unit_price' as SortKey },
    ];
  }, [mode]);

  // ========== Computed: 残り2軸 ==========
  const [baseAx, axB, axC] = useMemo(() => axesFromMode(mode), [mode]);

  // ========== Header totals ==========
  const headerTotals = useMemo(() => {
    const flat = summary.flatMap((r) => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { amount, qty, count, unit };
  }, [summary]);

  // ========== 選択営業名（KPIタイトル表示用） ==========
  const selectedRepLabel = useMemo(() => {
    if (repIds.length === 0) return '未選択';
    const names = reps.filter((r) => repIds.includes(r.id)).map((r) => r.name);
    return names.length <= 3
      ? names.join('・')
      : `${names.slice(0, 3).join('・')} ほか${names.length - 3}名`;
  }, [repIds, reps]);

  // ========== 期間ラベル ==========
  const periodLabel = useMemo(() => {
    return periodMode === 'single'
      ? month.format('YYYYMM')
      : `${(range?.[0] ?? dayjs()).format('YYYYMM')}-${(range?.[1] ?? dayjs()).format('YYYYMM')}`;
  }, [periodMode, month, range]);

  // ========== Mode switch（フィルタをリセット） ==========
  const switchMode = useCallback((m: Mode) => {
    setMode(m);
    setFilterIds([]);
  }, []);

  // ========== Pivot handlers ==========
  const openPivot = useCallback(
    (rec: MetricEntry) => {
      const others = (['customer', 'item', 'date'] as Mode[]).filter((ax) => ax !== mode);
      const targets: { axis: Mode; label: string }[] = others.map((ax) => ({
        axis: ax,
        label: ax === 'customer' ? '顧客' : ax === 'item' ? '品名' : '日付',
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
    },
    [mode, repIds, sortBy, order, topN, query]
  );

  const closeDrawer = useCallback(() => {
    setDrawer({ open: false });
  }, []);

  const setDrawerActiveAxis = useCallback((axis: Mode) => {
    setDrawer((prev) => (prev.open ? { ...prev, activeAxis: axis } : prev));
  }, []);

  const setDrawerTopN = useCallback((topN: 10 | 20 | 50 | 'all') => {
    setDrawer((prev) => (prev.open ? { ...prev, topN } : prev));
  }, []);

  const setDrawerSortBy = useCallback((sortBy: SortKey) => {
    setDrawer((prev) => (prev.open ? { ...prev, sortBy } : prev));
  }, []);

  const setDrawerOrder = useCallback((order: SortOrder) => {
    setDrawer((prev) => (prev.open ? { ...prev, order } : prev));
  }, []);

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
        month: drawerMonth,
        monthRange: drawerMonthRange,
      } = drawer;
      const targetAxis = axis;
      if (targetAxis === baseAxis) return;

      setPivotLoading(true);
      try {
        const periodParams = drawerMonthRange
          ? { monthRange: drawerMonthRange }
          : { month: drawerMonth };
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
      } catch (error) {
        console.error('Failed to fetch pivot:', error);
      } finally {
        setPivotLoading(false);
      }
    },
    [repository, drawer, pivotCursor]
  );

  // Drawer の activeAxis/sortBy/order/topN が変わったら自動再読込
  useEffect(() => {
    if (!drawer.open) return;
    void loadPivot(drawer.activeAxis, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    drawer.open,
    drawer.open ? drawer.activeAxis : null,
    drawer.open ? drawer.sortBy : null,
    drawer.open ? drawer.order : null,
    drawer.open ? drawer.topN : null,
  ]);

  // ========== Daily series ==========
  const loadDailySeries = useCallback(
    async (repId: ID) => {
      if (repSeriesCache[repId]) return;
      try {
        const s = await repository.fetchDailySeries(
          query.month ? { month: query.month, repId } : { monthRange: query.monthRange!, repId }
        );
        setRepSeriesCache((prev) => ({ ...prev, [repId]: s }));
      } catch (error) {
        console.error('Failed to fetch daily series:', error);
      }
    },
    [repository, query, repSeriesCache]
  );

  // ========== Export ==========
  const handleExport = useCallback(async () => {
    if (repIds.length === 0) return;
    try {
      const blob = await repository.exportModeCube({
        ...query,
        options: exportOptions,
        targetRepIds: repIds,
      });
      // Blob をダウンロード
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sales_pivot_${periodLabel}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export CSV:', error);
    }
  }, [repository, query, exportOptions, repIds, periodLabel]);

  return {
    // State
    periodMode,
    month,
    range,
    mode,
    topN,
    sortBy,
    order,
    repIds,
    filterIds,
    exportOptions,
    summary,
    loading,
    drawer,
    pivotData,
    pivotCursor,
    pivotLoading,
    repSeriesCache,
    reps,
    customers,
    items,

    // Computed
    query,
    repOptions,
    filterOptions,
    sortKeyOptions,
    headerTotals,
    selectedRepLabel,
    periodLabel,
    baseAx,
    axB,
    axC,

    // Handlers
    setPeriodMode,
    setMonth,
    setRange,
    switchMode,
    setTopN,
    setSortBy,
    setOrder,
    setRepIds,
    setFilterIds,
    setExportOptions,
    reload,

    // Drawer
    openPivot,
    closeDrawer,
    setDrawerActiveAxis,
    setDrawerTopN,
    setDrawerSortBy,
    setDrawerOrder,
    loadPivot,

    // Daily series
    loadDailySeries,

    // Export
    handleExport,
  };
}
