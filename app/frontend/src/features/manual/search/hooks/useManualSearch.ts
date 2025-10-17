/**
 * useManualSearch Hook (ViewModel)
 * マニュアル検索のビジネスロジックとステート管理
 */

import { useEffect, useMemo, useState } from 'react';
import type { ManualRepository } from '../repository/ManualRepository';
import { ManualRepositoryImpl } from '../repository/ManualRepositoryImpl';
import type { ManualSearchQuery, ManualSearchResult } from '../../shared/model/types';

export function useManualSearch(initial: ManualSearchQuery) {
  const repo: ManualRepository = useMemo(() => new ManualRepositoryImpl(), []);
  const [query, setQuery] = useState<ManualSearchQuery>(initial);
  const [data, setData] = useState<ManualSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);

    repo
      .search(query, ctrl.signal)
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err as Error);
          setData(null);
        }
      })
      .finally(() => setLoading(false));

    return () => ctrl.abort();
  }, [query, repo]);

  return {
    query,
    setQuery,
    data,
    loading,
    error,
    refetch: () => setQuery({ ...query }),
  };
}
