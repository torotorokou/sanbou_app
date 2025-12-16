/**
 * useReservationCalendarVM - 予約履歴カレンダー ViewModel
 * 
 * Model (状態管理・ビジネスロジック)
 * 規約: ViewModel hooks は useXxxVM.ts 命名に統一
 * 
 * 責務: 履歴カレンダーの表示データ管理
 */

import { useState, useCallback, useEffect } from 'react';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type {
  ReservationDailyRepository,
  ReservationForecastDaily,
} from '../../shared';
import { reservationDailyMockRepository } from '../../shared';

export interface ReservationCalendarViewModel {
  // State
  historyMonth: Dayjs;
  historyData: ReservationForecastDaily[];
  isLoadingHistory: boolean;

  // Events
  onChangeHistoryMonth: (month: Dayjs) => void;
  refreshData: () => void;
}

export const useReservationCalendarVM = (
  repository: ReservationDailyRepository = reservationDailyMockRepository
): ReservationCalendarViewModel => {
  const [historyMonth, setHistoryMonth] = useState<Dayjs>(dayjs());
  const [historyData, setHistoryData] = useState<ReservationForecastDaily[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);

  const fetchHistoryData = useCallback(async (month: Dayjs) => {
    setIsLoadingHistory(true);
    try {
      const from = month.startOf('month').format('YYYY-MM-DD');
      const to = month.endOf('month').format('YYYY-MM-DD');
      const data = await repository.getForecastDaily(from, to);
      setHistoryData(data);
    } catch (err: unknown) {
      console.error('Failed to fetch history data:', err);
      setHistoryData([]);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [repository]);

  const onChangeHistoryMonth = useCallback((month: Dayjs) => {
    setHistoryMonth(month);
    fetchHistoryData(month);
  }, [fetchHistoryData]);

  const refreshData = useCallback(() => {
    fetchHistoryData(historyMonth);
  }, [historyMonth, fetchHistoryData]);

  // 初回データ取得
  useEffect(() => {
    fetchHistoryData(historyMonth);
  }, [fetchHistoryData, historyMonth]);

  return {
    historyMonth,
    historyData,
    isLoadingHistory,
    onChangeHistoryMonth,
    refreshData,
  };
};
