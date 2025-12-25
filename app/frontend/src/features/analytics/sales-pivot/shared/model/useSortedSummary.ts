/**
 * ソート済みサマリーデータフック
 * テーブル表示用のクライアント側ソート処理
 */

import { useMemo } from "react";
import type { SummaryRow, SortKey, SortOrder } from "./types";

/**
 * サマリーデータをテーブルソート条件でソート
 * @param rawSummary APIから取得した生データ
 * @param tableSortBy ソートキー
 * @param tableOrder ソート順
 */
export function useSortedSummary(
  rawSummary: SummaryRow[],
  tableSortBy: SortKey,
  tableOrder: SortOrder,
): SummaryRow[] {
  return useMemo(() => {
    // API取得結果に対してテーブルのソートのみ適用
    const sorted = rawSummary.map((row) => {
      const sortedTopN = [...row.topN].sort((a, b) => {
        let aVal: number | string;
        let bVal: number | string;

        switch (tableSortBy) {
          case "amount":
            aVal = a.amount;
            bVal = b.amount;
            break;
          case "qty":
            aVal = a.qty;
            bVal = b.qty;
            break;
          case "count":
            aVal = a.count;
            bVal = b.count;
            break;
          case "unit_price":
            aVal = a.qty > 0 ? a.amount / a.qty : 0;
            bVal = b.qty > 0 ? b.amount / b.qty : 0;
            break;
          case "name":
            aVal = a.name;
            bVal = b.name;
            break;
          case "date":
            aVal = a.name;
            bVal = b.name;
            break;
          default:
            aVal = a.amount;
            bVal = b.amount;
        }

        if (typeof aVal === "string" && typeof bVal === "string") {
          return tableOrder === "asc"
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }
        return tableOrder === "asc"
          ? (aVal as number) - (bVal as number)
          : (bVal as number) - (aVal as number);
      });

      return { ...row, topN: sortedTopN };
    });

    return sorted;
  }, [rawSummary, tableSortBy, tableOrder]);
}
