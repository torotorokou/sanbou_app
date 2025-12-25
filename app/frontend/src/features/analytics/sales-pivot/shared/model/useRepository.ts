/**
 * shared/model/useRepository.ts
 * Repository管理用カスタムフック
 */

import { useEffect, useMemo } from 'react';
import type { CategoryKind } from './types';
import { HttpSalesPivotRepository } from '../infrastructure/salesPivot.repository';

/**
 * SalesPivotRepositoryインスタンスを管理し、
 * categoryKindの変更に応じて自動的に設定を更新する
 */
export function useRepository(categoryKind: CategoryKind) {
  const repository = useMemo(() => new HttpSalesPivotRepository(), []);

  useEffect(() => {
    if (repository && 'setCategoryKind' in repository) {
      (repository as { setCategoryKind: (kind: string) => void }).setCategoryKind(categoryKind);
    }
  }, [categoryKind, repository]);

  return repository;
}
