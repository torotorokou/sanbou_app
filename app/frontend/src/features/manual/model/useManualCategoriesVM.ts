/**
 * useManualCategories Hook (ViewModel)
 * マニュアルカテゴリ一覧取得のロジック
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import type { ManualRepository } from '../ports/repository';
import { ManualRepositoryImpl } from '../infrastructure/manual.repository';
import type { ManualCategory } from '../domain/types/manual.types';

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
