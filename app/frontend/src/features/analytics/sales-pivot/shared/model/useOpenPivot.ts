/**
 * features/analytics/sales-pivot/shared/model/useOpenPivot.ts
 * Pivotドロワーを開くロジック
 */

import { useCallback } from 'react';
import type { Mode, ID, MetricEntry, SummaryQuery, SortKey, SortOrder } from './types';
import type { DrawerState } from './usePivotDrawerState';
import { axisLabel } from './metrics';

interface OpenPivotParams {
  mode: Mode;
  query: SummaryQuery;
  filterSortBy: SortKey;
  filterOrder: SortOrder;
  filterTopN: 10 | 20 | 50 | 'all';
  setDrawer: (drawer: DrawerState | ((prev: DrawerState) => DrawerState)) => void;
  setPivotData: (data: Record<Mode, MetricEntry[]> | ((prev: Record<Mode, MetricEntry[]>) => Record<Mode, MetricEntry[]>)) => void;
  setPivotCursor: (cursor: Record<Mode, string | null> | ((prev: Record<Mode, string | null>) => Record<Mode, string | null>)) => void;
}

export function useOpenPivot(params: OpenPivotParams) {
  const {
    mode,
    query,
    filterSortBy,
    filterOrder,
    filterTopN,
    setDrawer,
    setPivotData,
    setPivotCursor,
  } = params;

  const openPivot = useCallback(
    (rec: MetricEntry, repId: ID) => {
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
    },
    [mode, query, filterSortBy, filterOrder, filterTopN, setDrawer, setPivotData, setPivotCursor]
  );

  return { openPivot };
}
