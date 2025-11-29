/**
 * filters/model/useMasters.ts
 * マスタデータ取得Hook
 */

import { useState, useEffect } from 'react';
import type { SalesRep, UniverseEntry } from '../../shared/model/types';
import type { SalesPivotRepository } from '../../shared/infrastructure/salesPivot.repository';

export interface UseMastersResult {
  reps: SalesRep[];
  customers: UniverseEntry[];
  items: UniverseEntry[];
  loading: boolean;
}

/**
 * マスタデータ取得Hook
 */
export function useMasters(repository: SalesPivotRepository): UseMastersResult {
  const [reps, setReps] = useState<SalesRep[]>([]);
  const [customers, setCustomers] = useState<UniverseEntry[]>([]);
  const [items, setItems] = useState<UniverseEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const [r, c, i] = await Promise.all([
          repository.getSalesReps(),
          repository.getCustomers(),
          repository.getItems(),
        ]);
        setReps(r);
        setCustomers(c);
        setItems(i);
      } catch (error) {
        console.error('Failed to load masters:', error);
      } finally {
        setLoading(false);
      }
    })();
  }, [repository]);

  return { reps, customers, items, loading };
}
