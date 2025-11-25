/**
 * features/analytics/sales-pivot/shared/model/useQueryBuilder.ts
 * SummaryQueryの構築（期間とフィルター条件から）
 */

import { useMemo } from 'react';
import type { SummaryQuery, Mode, ID, SortKey, SortOrder } from './types';
import type { Dayjs } from 'dayjs';

interface QueryBuilderParams {
  periodMode: 'single' | 'range';
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  mode: Mode;
  categoryKind: 'waste' | 'valuable';
  repIds: ID[];
  filterIds: ID[];
  filterSortBy: SortKey;
  filterOrder: SortOrder;
  filterTopN: 10 | 20 | 50 | 'all';
}

export function useQueryBuilder(params: QueryBuilderParams) {
  const {
    periodMode,
    month,
    range,
    mode,
    categoryKind,
    repIds,
    filterIds,
    filterSortBy,
    filterOrder,
    filterTopN,
  } = params;

  const query: SummaryQuery = useMemo(() => {
    const base = { mode, categoryKind, repIds, filterIds, sortBy: filterSortBy, order: filterOrder, topN: filterTopN };
    if (periodMode === 'single') return { ...base, month: month.format('YYYY-MM') };
    if (range)
      return {
        ...base,
        monthRange: { from: range[0].format('YYYY-MM'), to: range[1].format('YYYY-MM') },
      };
    return { ...base, month: month.format('YYYY-MM') };
  }, [periodMode, month, range, mode, categoryKind, repIds, filterIds, filterSortBy, filterOrder, filterTopN]);

  return query;
}
