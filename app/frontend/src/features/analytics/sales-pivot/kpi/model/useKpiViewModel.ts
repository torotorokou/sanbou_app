/**
 * kpi/model/useKpiViewModel.ts
 * KPIサマリ計算ViewModel
 */

import { useMemo } from 'react';
import type { SummaryRow } from '../../shared/model/types';

export interface UseKpiViewModelParams {
  summary: SummaryRow[];
}

export interface UseKpiViewModelResult {
  totalAmount: number;
  totalQty: number;
  totalCount: number;
  avgUnitPrice: number | null;
}

/**
 * KPI ViewModel Hook
 * サマリデータから集計値を計算
 */
export function useKpiViewModel(params: UseKpiViewModelParams): UseKpiViewModelResult {
  const { summary } = params;

  const { totalAmount, totalQty, totalCount, avgUnitPrice } = useMemo(() => {
    const flat = summary.flatMap((r) => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { totalAmount: amount, totalQty: qty, totalCount: count, avgUnitPrice: unit };
  }, [summary]);

  return { totalAmount, totalQty, totalCount, avgUnitPrice };
}
