/**
 * useManualDoc Hook (ViewModel)
 * マニュアルドキュメントURL生成のロジック
 */

import { useMemo } from 'react';
import type { ManualRepository } from '@/features/manual/search/repository/ManualRepository';
import { ManualRepositoryImpl } from '@/features/manual/search/repository/ManualRepositoryImpl';

export function useManualDoc() {
  const repo: ManualRepository = useMemo(() => new ManualRepositoryImpl(), []);

  const getUrl = (docId: string, filename: string, query?: Record<string, string>) =>
    repo.getDocUrl(docId, filename, query);

  return { getUrl };
}
