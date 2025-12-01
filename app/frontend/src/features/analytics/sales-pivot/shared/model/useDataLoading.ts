/**
 * データローディング状態管理フック
 * サマリーデータの取得とローディング状態管理
 */

import { useState, useEffect, useCallback } from 'react';
import type { SummaryRow, SummaryQuery } from './types';
import type { SalesPivotRepository } from '../infrastructure/salesPivot.repository';

export interface DataLoadingState {
  rawSummary: SummaryRow[];
  loading: boolean;
  reload: () => Promise<void>;
}

/**
 * データローディング状態管理フック
 * @param repository リポジトリインスタンス
 * @param baseQuery APIクエリパラメータ
 */
export function useDataLoading(
  repository: SalesPivotRepository,
  baseQuery: SummaryQuery
): DataLoadingState {
  const [rawSummary, setRawSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await repository.fetchSummary(baseQuery);
      setRawSummary(rows);
    } finally {
      setLoading(false);
    }
  }, [repository, baseQuery]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const rows = await repository.fetchSummary(baseQuery);
        setRawSummary(rows);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [repository, baseQuery]);

  return { rawSummary, loading, reload };
}
