/**
 * features/analytics/sales-pivot/shared/model/useQueryBuilder.ts
 * SummaryQueryの構築（期間とフィルター条件から）
 */

import { useMemo } from "react";
import type { SummaryQuery, Mode, ID, SortKey, SortOrder } from "./types";
import type { Dayjs } from "dayjs";

interface QueryBuilderParams {
  granularity: "month" | "date";
  periodMode: "single" | "range";
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  singleDate: Dayjs;
  dateRange: [Dayjs, Dayjs] | null;
  mode: Mode;
  categoryKind: "waste" | "valuable";
  repIds: ID[];
  filterIds: ID[];
  filterSortBy: SortKey;
  filterOrder: SortOrder;
  filterTopN: 10 | 20 | 50 | "all";
}

export function useQueryBuilder(params: QueryBuilderParams) {
  const {
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    mode,
    categoryKind,
    repIds,
    filterIds,
    filterSortBy,
    filterOrder,
    filterTopN,
  } = params;

  const query: SummaryQuery = useMemo(() => {
    const base = {
      mode,
      categoryKind,
      repIds,
      filterIds,
      sortBy: filterSortBy,
      order: filterOrder,
      topN: filterTopN,
    };

    if (granularity === "date") {
      // 日次モード
      if (periodMode === "range") {
        // 日付範囲
        const dr = dateRange || [singleDate, singleDate];
        return {
          ...base,
          dateFrom: dr[0].format("YYYY-MM-DD"),
          dateTo: dr[1].format("YYYY-MM-DD"),
        };
      } else {
        // 単一日付
        return {
          ...base,
          dateFrom: singleDate.format("YYYY-MM-DD"),
          dateTo: singleDate.format("YYYY-MM-DD"),
        };
      }
    } else {
      // 月次モード
      if (periodMode === "range") {
        // 月範囲
        const r = range || [month, month];
        return {
          ...base,
          monthRange: {
            from: r[0].format("YYYY-MM"),
            to: r[1].format("YYYY-MM"),
          },
        };
      } else {
        // 単月
        return { ...base, month: month.format("YYYY-MM") };
      }
    }
  }, [
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    mode,
    categoryKind,
    repIds,
    filterIds,
    filterSortBy,
    filterOrder,
    filterTopN,
  ]);

  return query;
}
