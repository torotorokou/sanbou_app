/**
 * features/analytics/sales-pivot/shared/model/useSortKeyOptions.ts
 * ソートキーオプションの生成
 */

import { useMemo } from "react";
import type { Mode, SortKey } from "./types";

export function useSortKeyOptions(mode: Mode) {
  const sortKeyOptions = useMemo(() => {
    return [
      {
        label: mode === "date" ? "日付" : "名称",
        value: (mode === "date" ? "date" : "name") as SortKey,
      },
      { label: "売上", value: "amount" as SortKey },
      { label: "数量", value: "qty" as SortKey },
      { label: "件数", value: "count" as SortKey },
      { label: "単価", value: "unit_price" as SortKey },
    ];
  }, [mode]);

  return sortKeyOptions;
}
