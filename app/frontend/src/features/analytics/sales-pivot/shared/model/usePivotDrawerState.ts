/**
 * PivotDrawer状態管理フック
 * ピボットドロワーの状態管理（drawer, pivotData, pivotCursor, pivotLoading, repSeriesCache）
 */

import { useState } from 'react';
import type { Mode, ID, YYYYMM, SortKey, SortOrder, MetricEntry, DailyPoint } from './types';

export type DrawerState =
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

export interface PivotDrawerState {
  drawer: DrawerState;
  setDrawer: (drawer: DrawerState | ((prev: DrawerState) => DrawerState)) => void;
  pivotData: Record<Mode, MetricEntry[]>;
  setPivotData: (
    data:
      | Record<Mode, MetricEntry[]>
      | ((prev: Record<Mode, MetricEntry[]>) => Record<Mode, MetricEntry[]>)
  ) => void;
  pivotCursor: Record<Mode, string | null>;
  setPivotCursor: (
    cursor:
      | Record<Mode, string | null>
      | ((prev: Record<Mode, string | null>) => Record<Mode, string | null>)
  ) => void;
  pivotLoading: boolean;
  setPivotLoading: (loading: boolean) => void;
  repSeriesCache: Record<ID, DailyPoint[]>;
  setRepSeriesCache: (
    cache: Record<ID, DailyPoint[]> | ((prev: Record<ID, DailyPoint[]>) => Record<ID, DailyPoint[]>)
  ) => void;
}

/**
 * PivotDrawer状態管理フック
 */
export function usePivotDrawerState(): PivotDrawerState {
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

  return {
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
  };
}
