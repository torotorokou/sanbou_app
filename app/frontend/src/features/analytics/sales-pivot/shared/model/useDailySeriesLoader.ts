/**
 * features/analytics/sales-pivot/shared/model/useDailySeriesLoader.ts
 * 日次推移データ取得ハンドラー
 */

import { useCallback } from 'react';
import type { ID, SummaryQuery, DailyPoint } from './types';
import type { HttpSalesPivotRepository } from '../api/salesPivot.repository';

interface DailySeriesLoaderParams {
  repository: HttpSalesPivotRepository;
  query: SummaryQuery;
  categoryKind: 'waste' | 'valuable';
  repSeriesCache: Record<ID, DailyPoint[]>;
  setRepSeriesCache: (cache: Record<ID, DailyPoint[]> | ((prev: Record<ID, DailyPoint[]>) => Record<ID, DailyPoint[]>)) => void;
}

export function useDailySeriesLoader(params: DailySeriesLoaderParams) {
  const { repository, query, categoryKind, repSeriesCache, setRepSeriesCache } = params;

  const loadDailySeries = useCallback(
    async (repId: ID) => {
      if (repSeriesCache[repId]) return;
      const s = await repository.fetchDailySeries(
        query.month
          ? { month: query.month, categoryKind, repId }
          : { monthRange: query.monthRange!, categoryKind, repId }
      );
      setRepSeriesCache((prev) => ({ ...prev, [repId]: s }));
    },
    [repository, query, categoryKind, repSeriesCache, setRepSeriesCache]
  );

  return { loadDailySeries };
}
