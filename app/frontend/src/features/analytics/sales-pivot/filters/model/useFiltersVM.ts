/**
 * filters/model/useFiltersVM.ts
 * フィルタ状態管理ViewModel
 */

import { useState, useMemo, useCallback } from 'react';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type {
  Mode,
  SortKey,
  SortOrder,
  ID,
  SummaryQuery,
  UniverseEntry,
} from '../../shared/model/types';

export interface UseFiltersViewModelParams {
  customers: UniverseEntry[];
  items: UniverseEntry[];
}

export interface UseFiltersViewModelResult {
  // Period
  periodMode: 'single' | 'range';
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  setPeriodMode: (mode: 'single' | 'range') => void;
  setMonth: (month: Dayjs) => void;
  setRange: (range: [Dayjs, Dayjs] | null) => void;

  // Mode & Controls
  mode: Mode;
  topN: 10 | 20 | 50 | 'all';
  sortBy: SortKey;
  order: SortOrder;
  switchMode: (mode: Mode) => void;
  setTopN: (topN: 10 | 20 | 50 | 'all') => void;
  setSortBy: (sortBy: SortKey) => void;
  setOrder: (order: SortOrder) => void;

  // Rep & Filter
  repIds: ID[];
  filterIds: ID[];
  setRepIds: (ids: ID[]) => void;
  setFilterIds: (ids: ID[]) => void;

  // Computed
  query: SummaryQuery;
  filterOptions: Array<{ label: string; value: ID }>;
  sortKeyOptions: Array<{ label: string; value: SortKey }>;
  periodLabel: string;
}

/**
 * フィルタViewModelフック
 */
export function useFiltersViewModel(params: UseFiltersViewModelParams): UseFiltersViewModelResult {
  const { customers, items } = params;

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

  // ========== Mode switch（フィルタリセット） ==========
  const switchMode = useCallback((m: Mode) => {
    setMode(m);
    setFilterIds([]);
  }, []);

  // ========== Query ==========
  const query: SummaryQuery = useMemo(() => {
    const base = {
      mode,
      repIds,
      filterIds,
      sortBy,
      order,
      topN,
      categoryKind: 'waste' as const,
    };
    if (periodMode === 'single') return { ...base, month: month.format('YYYY-MM') };
    if (range)
      return {
        ...base,
        monthRange: {
          from: range[0].format('YYYY-MM'),
          to: range[1].format('YYYY-MM'),
        },
      };
    return { ...base, month: month.format('YYYY-MM') };
  }, [periodMode, month, range, mode, repIds, filterIds, sortBy, order, topN]);

  // ========== Filter options ==========
  const filterOptions = useMemo(() => {
    if (mode === 'customer') return customers.map((c) => ({ label: c.name, value: c.id }));
    if (mode === 'item') return items.map((i) => ({ label: i.name, value: i.id }));
    return []; // date mode
  }, [mode, customers, items]);

  // ========== Sort key options ==========
  const sortKeyOptions = useMemo(() => {
    // 件数/台数ラベルの動的切り替え
    const countLabel = mode === 'item' ? '件数' : '台数';

    return [
      {
        label: mode === 'date' ? '日付' : '名称',
        value: (mode === 'date' ? 'date' : 'name') as SortKey,
      },
      { label: '売上', value: 'amount' as SortKey },
      { label: '数量', value: 'qty' as SortKey },
      { label: countLabel, value: 'count' as SortKey },
      { label: '単価', value: 'unit_price' as SortKey },
    ];
  }, [mode]);

  // ========== Period label ==========
  const periodLabel = useMemo(() => {
    return periodMode === 'single'
      ? month.format('YYYYMM')
      : `${(range?.[0] ?? dayjs()).format('YYYYMM')}-${(range?.[1] ?? dayjs()).format('YYYYMM')}`;
  }, [periodMode, month, range]);

  return {
    periodMode,
    month,
    range,
    setPeriodMode,
    setMonth,
    setRange,
    mode,
    topN,
    sortBy,
    order,
    switchMode,
    setTopN,
    setSortBy,
    setOrder,
    repIds,
    filterIds,
    setRepIds,
    setFilterIds,
    query,
    filterOptions,
    sortKeyOptions,
    periodLabel,
  };
}
