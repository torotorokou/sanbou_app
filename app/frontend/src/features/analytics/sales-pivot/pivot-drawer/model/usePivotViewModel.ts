/**
 * pivot-drawer/model/usePivotViewModel.ts
 * Pivotドロワー機能のViewModel
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  Mode,
  SortKey,
  SortOrder,
  ID,
  MetricEntry,
  DrawerState,
  SummaryQuery,
} from '../../shared/model/types';
import type { SalesPivotRepository } from '../../shared/api/salesPivot.repository';

export interface UsePivotViewModelParams {
  repository: SalesPivotRepository;
  query: SummaryQuery;
}

export interface UsePivotViewModelResult {
  drawer: DrawerState;
  pivotData: Record<Mode, MetricEntry[]>;
  pivotCursor: Record<Mode, string | null>;
  pivotLoading: boolean;
  
  openPivot: (rec: MetricEntry, mode: Mode, repIds: ID[], sortBy: SortKey, order: SortOrder, topN: 10 | 20 | 50 | 'all') => void;
  closeDrawer: () => void;
  setDrawerActiveAxis: (axis: Mode) => void;
  setDrawerTopN: (topN: 10 | 20 | 50 | 'all') => void;
  setDrawerSortBy: (sortBy: SortKey) => void;
  setDrawerOrder: (order: SortOrder) => void;
  loadPivot: (axis: Mode, reset?: boolean) => Promise<void>;
}

/**
 * Pivot ViewModel Hook
 */
export function usePivotViewModel(params: UsePivotViewModelParams): UsePivotViewModelResult {
  const { repository, query } = params;

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

  // Open pivot
  const openPivot = useCallback(
    (rec: MetricEntry, mode: Mode, repIds: ID[], sortBy: SortKey, order: SortOrder, topN: 10 | 20 | 50 | 'all') => {
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
    [query]
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
          categoryKind: 'waste',
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

  // Auto-reload on drawer params change
  useEffect(() => {
    if (!drawer.open) return;
    void loadPivot(drawer.activeAxis, true);
  }, [
    drawer.open,
    drawer.open ? drawer.activeAxis : null,
    drawer.open ? drawer.sortBy : null,
    drawer.open ? drawer.order : null,
    drawer.open ? drawer.topN : null,
  ]);

  return {
    drawer,
    pivotData,
    pivotCursor,
    pivotLoading,
    openPivot,
    closeDrawer,
    setDrawerActiveAxis,
    setDrawerTopN,
    setDrawerSortBy,
    setDrawerOrder,
    loadPivot,
  };
}
