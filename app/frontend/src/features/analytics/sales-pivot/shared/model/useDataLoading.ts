/**
 * データローディング状態管理フック
 * サマリーデータの取得とローディング状態管理
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import type { SummaryRow, SummaryQuery } from "./types";
import type { SalesPivotRepository } from "../infrastructure/salesPivot.repository";

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
  baseQuery: SummaryQuery,
): DataLoadingState {
  const [rawSummary, setRawSummary] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // クエリの安定したキーを生成（オブジェクト参照の変化による不要な再実行を防止）
  const queryKey = useMemo(() => JSON.stringify(baseQuery), [baseQuery]);

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
      // データ取得前に既存データをクリア（増殖防止）
      setRawSummary([]);
      setLoading(true);
      try {
        const rows = await repository.fetchSummary(baseQuery);
        setRawSummary(rows);
      } finally {
        setLoading(false);
      }
    };
    loadData();
    // queryKeyを使用することで、実際のクエリ内容が変わった時のみ再実行
  }, [repository, queryKey]);

  return { rawSummary, loading, reload };
}
