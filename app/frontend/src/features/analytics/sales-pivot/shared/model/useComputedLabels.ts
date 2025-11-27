/**
 * 計算済みラベルと集計値フック
 * 期間ラベル、ヘッダー集計、選択営業ラベル等の算出ロジック
 */

import { useMemo } from 'react';
import type { SummaryRow, ID } from './types';
import type { Dayjs } from 'dayjs';

export interface ComputedLabelsState {
  periodLabel: string;
  headerTotals: {
    amount: number;
    qty: number;
    count: number;
    unit: number | null;
  };
  selectedRepLabel: string;
}

/**
 * 計算済みラベルと集計値フック
 * @param granularity 粒度（月次/日次）
 * @param periodMode 期間モード（単一/期間）
 * @param month 単月
 * @param range 月範囲
 * @param singleDate 単一日付
 * @param dateRange 日付範囲
 * @param summary サマリーデータ
 * @param repIds 選択営業ID配列
 * @param reps 営業マスタ
 */
export function useComputedLabels(
  granularity: 'month' | 'date',
  periodMode: 'single' | 'range',
  month: Dayjs,
  range: [Dayjs, Dayjs] | null,
  singleDate: Dayjs,
  dateRange: [Dayjs, Dayjs] | null,
  summary: SummaryRow[],
  repIds: ID[],
  reps: Array<{ id: ID; name: string }>
): ComputedLabelsState {
  // 期間ラベル
  const periodLabel = useMemo(() => {
    if (granularity === 'date') {
      if (periodMode === 'range') {
        const dr = dateRange || [singleDate, singleDate];
        return `${dr[0].format('YYYY-MM-DD')} - ${dr[1].format('YYYY-MM-DD')}`;
      } else {
        return singleDate.format('YYYY-MM-DD');
      }
    } else {
      if (periodMode === 'range') {
        const r = range || [month, month];
        return `${r[0].format('YYYYMM')}-${r[1].format('YYYYMM')}`;
      } else {
        return month.format('YYYYMM');
      }
    }
  }, [granularity, periodMode, month, range, singleDate, dateRange]);

  // Header totals
  const headerTotals = useMemo(() => {
    const flat = summary.flatMap((r) => r.topN);
    const amount = flat.reduce((s, x) => s + x.amount, 0);
    const qty = flat.reduce((s, x) => s + x.qty, 0);
    const count = flat.reduce((s, x) => s + x.count, 0);
    const unit = qty > 0 ? Math.round((amount / qty) * 100) / 100 : null;
    return { amount, qty, count, unit };
  }, [summary]);

  // 選択営業名（KPIタイトル表示用）
  const selectedRepLabel = useMemo(() => {
    if (repIds.length === 0) return '未選択';
    const names = reps.filter((r) => repIds.includes(r.id)).map((r) => r.name);
    return names.length <= 3 ? names.join('・') : `${names.slice(0, 3).join('・')} ほか${names.length - 3}名`;
  }, [repIds, reps]);

  return { periodLabel, headerTotals, selectedRepLabel };
}
