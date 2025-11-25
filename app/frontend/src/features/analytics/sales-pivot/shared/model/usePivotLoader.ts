/**
 * features/analytics/sales-pivot/shared/model/usePivotLoader.ts
 * Pivotドロワーのデータ読み込みロジック
 */

import { useCallback } from 'react';
import type { Mode, MetricEntry } from './types';
import type { DrawerState } from './usePivotDrawerState';
import type { HttpSalesPivotRepository } from '../api/salesPivot.repository';

interface PivotLoaderParams {
  drawer: DrawerState;
  pivotCursor: Record<Mode, string | null>;
  categoryKind: 'waste' | 'valuable';
  repository: HttpSalesPivotRepository;
  setPivotData: (data: Record<Mode, MetricEntry[]> | ((prev: Record<Mode, MetricEntry[]>) => Record<Mode, MetricEntry[]>)) => void;
  setPivotCursor: (cursor: Record<Mode, string | null> | ((prev: Record<Mode, string | null>) => Record<Mode, string | null>)) => void;
  setPivotLoading: (loading: boolean) => void;
}

export function usePivotLoader(params: PivotLoaderParams) {
  const {
    drawer,
    pivotCursor,
    categoryKind,
    repository,
    setPivotData,
    setPivotCursor,
    setPivotLoading,
  } = params;

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
    [drawer, pivotCursor, categoryKind, repository, setPivotData, setPivotCursor, setPivotLoading]
  );

  return { loadPivot };
}
