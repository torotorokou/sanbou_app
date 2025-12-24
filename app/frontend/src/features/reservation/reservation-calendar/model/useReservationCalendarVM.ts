/**
 * useReservationCalendarVM - 予約履歴カレンダー ViewModel
 * 
 * Model (状態管理・ビジネスロジック)
 * 規約: ViewModel hooks は useXxxVM.ts 命名に統一
 * 
 * 責務: 履歴カレンダーの表示データ管理
 */

import { useState, useCallback, useEffect } from 'react';
import { message } from 'antd';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type {
  ReservationDailyRepository,
  ReservationForecastDaily,
} from '../../shared';
import { reservationDailyRepository } from '../../shared';

export interface ReservationCalendarViewModel {
  // State
  historyMonth: Dayjs;
  historyData: ReservationForecastDaily[];
  isLoadingHistory: boolean;
  isDeletingDate: string | null;

  // Events
  onChangeHistoryMonth: (month: Dayjs) => void;
  onDeleteDate: (date: string) => Promise<void>;
  goToCurrentMonth: () => void;
  refreshData: () => void;
}

export const useReservationCalendarVM = (
  repository: ReservationDailyRepository = reservationDailyRepository
): ReservationCalendarViewModel => {
  const [historyMonth, setHistoryMonth] = useState<Dayjs>(dayjs());
  const [historyData, setHistoryData] = useState<ReservationForecastDaily[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [isDeletingDate, setIsDeletingDate] = useState<string | null>(null);

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

  const onDeleteDate = useCallback(async (date: string) => {
    setIsDeletingDate(date);
    try {
      await repository.deleteManual(date);
      message.success('削除しました');
      // データを再取得
      await fetchHistoryData(historyMonth);
    } catch (err: unknown) {
      console.error('Failed to delete manual data:', err);
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      message.error(`削除に失敗しました: ${errorMessage}`);
    } finally {
      setIsDeletingDate(null);
    }
  }, [repository, historyMonth, fetchHistoryData]);

  const goToCurrentMonth = useCallback(() => {
    const currentMonth = dayjs();
    setHistoryMonth(currentMonth);
    fetchHistoryData(currentMonth);
  }, [fetchHistoryData]);

  // 初回データ取得
  useEffect(() => {
    fetchHistoryData(historyMonth);
  }, [fetchHistoryData, historyMonth]);

  return {
    historyMonth,
    historyData,
    isLoadingHistory,
    isDeletingDate,
    onChangeHistoryMonth,
    onDeleteDate,
    goToCurrentMonth,
    refreshData,
  };
};
