/**
 * フィルターオプション生成フック
 * モード別のフィルター選択肢を生成
 */

import { useMemo } from 'react';
import type { Mode, ID, SummaryQuery } from './types';
import { allDaysInRange, monthDays } from './metrics';

export interface FilterOptionsState {
  repOptions: Array<{ label: string; value: ID }>;
  filterOptions: Array<{ label: string; value: ID }>;
}

/**
 * フィルターオプション生成フック
 * @param mode 現在のモード（customer/item/date）
 * @param query APIクエリ（日付モード用）
 * @param reps 営業担当者リスト
 * @param customers 顧客リスト
 * @param items 商品リスト
 */
export function useFilterOptions(
  mode: Mode,
  query: SummaryQuery,
  reps: Array<{ id: ID; name: string }>,
  customers: Array<{ id: ID; name: string }>,
  items: Array<{ id: ID; name: string }>
): FilterOptionsState {
  const repOptions = useMemo(() => reps.map((r) => ({ label: r.name, value: r.id })), [reps]);

  const filterOptions = useMemo(() => {
    if (mode === 'customer') {
      // 顧客名の重複を削除（idでユニーク化）
      const seen = new Set<ID>();
      const uniqueCustomers: Array<{ label: string; value: ID }> = [];

      for (const customer of customers) {
        if (!seen.has(customer.id)) {
          seen.add(customer.id);
          uniqueCustomers.push({ label: customer.name, value: customer.id });
        }
      }

      // 名前順でソート
      return uniqueCustomers.sort((a, b) => a.label.localeCompare(b.label));
    }

    if (mode === 'item') {
      // 品名の重複を削除（idでユニーク化）
      const seen = new Set<ID>();
      const uniqueItems: Array<{ label: string; value: ID }> = [];

      for (const item of items) {
        if (!seen.has(item.id)) {
          seen.add(item.id);
          uniqueItems.push({ label: item.name, value: item.id });
        }
      }

      // 名前順でソート
      return uniqueItems.sort((a, b) => a.label.localeCompare(b.label));
    }

    // date mode - 日付は重複なし想定だが念のため処理
    const days = query.monthRange ? allDaysInRange(query.monthRange) : monthDays(query.month!);
    const seen = new Set<ID>();
    const uniqueDays: Array<{ label: string; value: ID }> = [];

    for (const day of days) {
      if (!seen.has(day.id)) {
        seen.add(day.id);
        uniqueDays.push({ label: day.name, value: day.id });
      }
    }

    // 日付順でソート（日付文字列の自然順）
    return uniqueDays.sort((a, b) => a.label.localeCompare(b.label));
  }, [mode, query, customers, items]);

  return { repOptions, filterOptions };
}
