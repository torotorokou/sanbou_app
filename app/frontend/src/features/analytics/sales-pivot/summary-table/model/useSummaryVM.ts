/**
 * summary-table/model/useSummaryVM.ts
 * サマリテーブル機能のViewModel
 */

import { useState, useCallback } from 'react';
import type { SummaryRow, SummaryQuery, MetricEntry, ID, DailyPoint } from '../../shared/model/types';
import type { SalesPivotRepository } from '../../shared/api/salesPivot.repository';

export interface UseSummaryViewModelParams {
  repository: SalesPivotRepository;
  query: SummaryQuery;
}

export interface UseSummaryViewModelResult {
  summary: SummaryRow[];
  loading: boolean;
  reload: () => Promise<void>;
  
  // Daily series for charts
  repSeriesCache: Record<ID, DailyPoint[]>;
  loadDailySeries: (repId: ID) => Promise<void>;
  
  // Pivot trigger
  onRowClick: (rec: MetricEntry) => void;
}

/**
 * サマリテーブルViewModel Hook
 */
export function useSummaryViewModel(
  params: UseSummaryViewModelParams,
  onPivotOpen?: (rec: MetricEntry) => void
): UseSummaryViewModelResult {
  const { repository, query } = params;

  const [summary, setSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [repSeriesCache, setRepSeriesCache] = useState<Record<ID, DailyPoint[]>>({});

  // Reload summary
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

  // Load daily series
  const loadDailySeries = useCallback(
    async (repId: ID) => {
      if (repSeriesCache[repId]) return;
      try {
        const s = await repository.fetchDailySeries(
          query.month
            ? { month: query.month, repId, categoryKind: 'waste' }
            : { monthRange: query.monthRange!, repId, categoryKind: 'waste' }
        );
        setRepSeriesCache((prev) => ({ ...prev, [repId]: s }));
      } catch (error) {
        console.error('Failed to fetch daily series:', error);
      }
    },
    [repository, query, repSeriesCache]
  );

  // Pivot open handler
  const onRowClick = useCallback(
    (rec: MetricEntry) => {
      onPivotOpen?.(rec);
    },
    [onPivotOpen]
  );

  return {
    summary,
    loading,
    reload,
    repSeriesCache,
    loadDailySeries,
    onRowClick,
  };
}
