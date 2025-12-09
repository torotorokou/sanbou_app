/**
 * features/analytics/sales-pivot/shared/model/usePivotLoader.ts
 * Pivotドロワーのデータ読み込みロジック
 */

import { useCallback } from 'react';
import type { Mode, MetricEntry } from './types';
import type { DrawerState } from './usePivotDrawerState';
import type { HttpSalesPivotRepository } from '../infrastructure/salesPivot.repository';

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
      
      const baseAxis = drawer.baseAxis;
      const baseId = drawer.baseId;
      const drawerRepIds = drawer.repIds;
      const drawerSortBy = drawer.sortBy;
      const drawerOrder = drawer.order;
      const drawerTopN = drawer.topN;
      const month = drawer.month;
      const monthRange = drawer.monthRange;
      // オプショナルプロパティを明示的にundefinedとして扱う
      const dateFrom: string | undefined = ('dateFrom' in drawer ? drawer.dateFrom : undefined) as string | undefined;
      const dateTo: string | undefined = ('dateTo' in drawer ? drawer.dateTo : undefined) as string | undefined;
      
      const targetAxis = axis;
      if (targetAxis === baseAxis) return;

      setPivotLoading(true);
      try {
        // 期間パラメータの構築
        let periodParams: {
          month?: string;
          monthRange?: { from: string; to: string };
          dateFrom?: string;
          dateTo?: string;
        } = {};
        
        if (dateFrom && dateTo) {
          periodParams = { dateFrom, dateTo };
        } else if (monthRange) {
          periodParams = { monthRange };
        } else if (month) {
          periodParams = { month };
        }
        
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
        setPivotCursor((prev) => ({ ...prev, [targetAxis]: page.nextCursor }));
      } finally {
        setPivotLoading(false);
      }
    },
    [drawer, pivotCursor, categoryKind, repository, setPivotData, setPivotCursor, setPivotLoading]
  );

  return { loadPivot };
}
