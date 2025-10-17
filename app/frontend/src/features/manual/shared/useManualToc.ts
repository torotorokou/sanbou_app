/**
 * useManualToc Hook (ViewModel)
 * マニュアル目次取得のロジック
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import type { ManualRepository } from '@/features/manual/search/repository/ManualRepository';
import { ManualRepositoryImpl } from '@/features/manual/search/repository/ManualRepositoryImpl';
import type { ManualTocItem } from './model/types';

export function useManualToc() {
  const repo: ManualRepository = useMemo(() => new ManualRepositoryImpl(), []);

  const [toc, setToc] = useState<ManualTocItem[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await repo.toc();
      setToc(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [repo]);

  useEffect(() => {
    const controller = new AbortController();
    fetch();
    return () => controller.abort();
  }, [fetch]);

  return { toc, isLoading, error, refetch: fetch };
}
