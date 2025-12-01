/**
 * kpi/model/useKpiVM.ts
 * KPIサマリ計算ViewModel
 * 
 * 【概要】
 * サマリデータから全体のKPI（売上合計、数量合計等）を計算するViewModel
 * 
 * 【責務】
 * - サマリデータ（営業ごとのTopN）を集約して全体KPIを算出
 * - 売上合計、数量合計、件数合計、平均単価の計算
 * 
 * 【使用例】
 * ```typescript
 * const { totalAmount, totalQty, totalCount, avgUnitPrice } = useKpiViewModel({
 *   summary: summaryRows
 * });
 * 
 * console.log(`総売上: ${totalAmount}円`);
 * console.log(`総数量: ${totalQty}kg`);
 * console.log(`平均単価: ${avgUnitPrice}円/kg`);
 * ```
 */

import { useMemo } from 'react';
import type { SummaryRow } from '../../shared/model/types';

/**
 * KPIViewModel入力パラメータ
 * 
 * @property summary - サマリデータ配列（営業ごとのTopNメトリクス）
 */
export interface UseKpiViewModelParams {
  summary: SummaryRow[];
}

/**
 * KPIViewModel出力
 * 
 * @property totalAmount - 総売上金額（円）
 * @property totalQty - 総数量（kg）
 * @property totalCount - 総件数
 * @property avgUnitPrice - 平均単価（円/kg）。総数量が0の場合はnull
 */
export interface UseKpiViewModelResult {
  totalAmount: number;
  totalQty: number;
  totalCount: number;
  avgUnitPrice: number | null;
}

/**
 * KPI ViewModel Hook
 * 
 * @param params - ViewModel入力パラメータ
 * @returns 計算されたKPI値
 * 
 * @description
 * サマリデータから集計値を計算
 * - 全営業の全メトリクスをフラット化して合計
 * - 平均単価は「総売上 ÷ 総数量」で算出
 * - 総数量が0の場合、平均単価はnull
 */
export function useKpiViewModel(params: UseKpiViewModelParams): UseKpiViewModelResult {
  const { summary } = params;

  const { totalAmount, totalQty, totalCount, avgUnitPrice } = useMemo(() => {
    // 全営業のTopNメトリクスをフラット化
    const flat = summary.flatMap((r) => r.topN);
    
    // 各メトリクスを合計
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    
    // 平均単価を計算（総売上 ÷ 総数量、小数点2桁）
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    
    return { totalAmount: amount, totalQty: qty, totalCount: count, avgUnitPrice: unit };
  }, [summary]);

  return { totalAmount, totalQty, totalCount, avgUnitPrice };
}
