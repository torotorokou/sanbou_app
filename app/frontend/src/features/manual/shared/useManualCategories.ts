/**
 * useManualCategories Hook (ViewModel)
 * マニュアルカテゴリ一覧取得のロジック
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import type { ManualRepository } from '@/features/manual/search/repository/ManualRepository';
import { ManualRepositoryImpl } from '@/features/manual/search/repository/ManualRepositoryImpl';
import type { ManualCategory } from './model/types';

export function useManualCategories() {
  const repo: ManualRepository = useMemo(() => new ManualRepositoryImpl(), []);

  const [categories, setCategories] = useState<ManualCategory[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await repo.categories();
      setCategories(result);
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

  return { categories, isLoading, error, refetch: fetch };
}
