/**
 * features/analytics/sales-pivot/shared/model/useDetailDrawerLoader.ts
 * 詳細明細行ドロワーのデータ読み込みロジック
 */

import { useCallback } from 'react';
import type { GroupBy, DetailLinesFilter, SummaryQuery, DetailLine, DetailMode } from './types';
import type { HttpSalesPivotRepository } from '../infrastructure/salesPivot.repository';

interface DetailDrawerLoaderParams {
  query: SummaryQuery;
  categoryKind: 'waste' | 'valuable';
  repository: HttpSalesPivotRepository;
  setDetailDrawerOpen: (open: boolean) => void;
  setDetailDrawerLoading: (loading: boolean) => void;
  setDetailDrawerTitle: (title: string) => void;
  setDetailDrawerMode: (mode: DetailMode | null) => void;
  setDetailDrawerRows: (rows: DetailLine[]) => void;
  setDetailDrawerTotalCount: (count: number) => void;
  message?: { error?: (msg: string) => void };
}

/**
 * 月末日を計算するヘルパー関数
 */
const getMonthEndDate = (yyyymm: string): string => {
  const [year, month] = yyyymm.split('-').map(Number);
  const nextMonth = new Date(year, month, 1);
  const lastDay = new Date(nextMonth.getTime() - 86400000);
  const dd = String(lastDay.getDate()).padStart(2, '0');
  return `${yyyymm}-${dd}`;
};

export function useDetailDrawerLoader(params: DetailDrawerLoaderParams) {
  const {
    query,
    categoryKind,
    repository,
    setDetailDrawerOpen,
    setDetailDrawerLoading,
    setDetailDrawerTitle,
    setDetailDrawerMode,
    setDetailDrawerRows,
    setDetailDrawerTotalCount,
    message,
  } = params;

  const openDetailDrawer = useCallback(
    async (
      lastGroupBy: GroupBy,
      repId?: string,
      customerId?: string,
      itemId?: string,
      dateValue?: string,
      title?: string
    ) => {
      setDetailDrawerLoading(true);
      setDetailDrawerOpen(true);
      setDetailDrawerTitle(title || '詳細明細');

      try {
        // 期間計算（月次モードと日次モードの両方に対応）
        let dateFrom: string;
        let dateTo: string;

        if (query.dateFrom && query.dateTo) {
          // 日次モード：dateFrom/dateToを直接使用
          dateFrom = query.dateFrom;
          dateTo = query.dateTo;
        } else if (query.monthRange) {
          // 月次モード（範囲）：月末日を正確に計算
          dateFrom = `${query.monthRange.from}-01`;
          dateTo = getMonthEndDate(query.monthRange.to);
        } else if (query.month) {
          // 月次モード（単月）：月末日を正確に計算
          dateFrom = `${query.month}-01`;
          dateTo = getMonthEndDate(query.month);
        } else {
          throw new Error('期間が設定されていません');
        }

        const filter: DetailLinesFilter = {
          dateFrom,
          dateTo,
          lastGroupBy,
          categoryKind,
          repId: repId ? parseInt(repId, 10) : undefined,
          customerId,
          itemId: itemId ? parseInt(itemId, 10) : undefined,
          dateValue,
        };

        console.log('📋 詳細明細取得リクエスト:', filter);

        const response = await repository.fetchDetailLines(filter);

        console.log('✅ 詳細明細取得成功:', {
          mode: response.mode,
          rowCount: response.rows.length,
          totalCount: response.totalCount,
        });

        setDetailDrawerMode(response.mode);
        setDetailDrawerRows(response.rows);
        setDetailDrawerTotalCount(response.totalCount);
      } catch (error) {
        console.error('❌ 詳細明細取得エラー:', error);
        message?.error?.('詳細明細の取得に失敗しました。');
        setDetailDrawerOpen(false);
      } finally {
        setDetailDrawerLoading(false);
      }
    },
    [
      query,
      categoryKind,
      repository,
      setDetailDrawerOpen,
      setDetailDrawerLoading,
      setDetailDrawerTitle,
      setDetailDrawerMode,
      setDetailDrawerRows,
      setDetailDrawerTotalCount,
      message,
    ]
  );

  return { openDetailDrawer };
}
