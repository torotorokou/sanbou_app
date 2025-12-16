/**
 * useReservationDailyViewModel - 予約表 ViewModel
 * 
 * Model (状態管理・ビジネスロジック)
 */

import { useState, useCallback, useEffect } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import type { ReservationDailyRepository, ReservationForecastDaily } from '../ports/ReservationDailyRepository';
import { reservationDailyRepository } from '../infrastructure/ReservationDailyHttpRepository';

export interface ReservationDailyViewModel {
  // State
  currentMonth: Dayjs;
  forecastData: ReservationForecastDaily[];
  selectedDate: string | null;
  totalTrucks: number;
  fixedTrucks: number;
  note: string;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  successMessage: string | null;

  // Events
  onChangeMonth: (month: Dayjs) => void;
  onSelectDate: (date: string) => void;
  onChangeTotalTrucks: (value: number) => void;
  onChangeFixedTrucks: (value: number) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => Promise<void>;
  onDelete: () => Promise<void>;
  clearMessages: () => void;
}

export const useReservationDailyViewModel = (
  repository: ReservationDailyRepository = reservationDailyRepository
): ReservationDailyViewModel => {
  const [currentMonth, setCurrentMonth] = useState<Dayjs>(dayjs());
  const [forecastData, setForecastData] = useState<ReservationForecastDaily[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [totalTrucks, setTotalTrucks] = useState<number>(0);
  const [fixedTrucks, setFixedTrucks] = useState<number>(0);
  const [note, setNote] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 当月データを取得
  const fetchMonthData = useCallback(async (month: Dayjs) => {
    setIsLoading(true);
    setError(null);
    try {
      const from = month.startOf('month').format('YYYY-MM-DD');
      const to = month.endOf('month').format('YYYY-MM-DD');
      const data = await repository.getForecastDaily(from, to);
      setForecastData(data);
    } catch (err) {
      console.error('Failed to fetch forecast data:', err);
      setError('データの取得に失敗しました');
      setForecastData([]);
    } finally {
      setIsLoading(false);
    }
  }, [repository]);

  // 月変更
  const onChangeMonth = useCallback((month: Dayjs) => {
    setCurrentMonth(month);
  }, []);

  // 月が変わったら再取得
  useEffect(() => {
    fetchMonthData(currentMonth);
  }, [currentMonth, fetchMonthData]);

  // 日付選択
  const onSelectDate = useCallback((date: string) => {
    setSelectedDate(date);
    setError(null);
    setSuccessMessage(null);
    
    // 既存データがあればフォームに反映
    const existing = forecastData.find(d => d.date === date);
    if (existing && existing.source === 'manual') {
      setTotalTrucks(existing.reserve_trucks);
      setFixedTrucks(existing.reserve_fixed_trucks);
    } else {
      setTotalTrucks(0);
      setFixedTrucks(0);
    }
    setNote('');
  }, [forecastData]);

  // フォーム変更
  const onChangeTotalTrucks = useCallback((value: number) => {
    setTotalTrucks(value);
    setError(null);
  }, []);

  const onChangeFixedTrucks = useCallback((value: number) => {
    setFixedTrucks(value);
    setError(null);
  }, []);

  const onChangeNote = useCallback((value: string) => {
    setNote(value);
  }, []);

  // バリデーション
  const validate = (): boolean => {
    if (!selectedDate) {
      setError('日付を選択してください');
      return false;
    }
    if (totalTrucks < 0) {
      setError('合計台数は0以上を入力してください');
      return false;
    }
    if (fixedTrucks < 0) {
      setError('固定客台数は0以上を入力してください');
      return false;
    }
    if (fixedTrucks > totalTrucks) {
      setError('固定客台数は合計台数以下にしてください');
      return false;
    }
    return true;
  };

  // 保存
  const onSubmit = useCallback(async () => {
    if (!validate()) return;

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await repository.upsertManual({
        reserve_date: selectedDate!,
        total_trucks: totalTrucks,
        fixed_trucks: fixedTrucks,
        note: note || undefined,
      });
      
      setSuccessMessage('保存しました');
      
      // カレンダーを再取得して即反映
      await fetchMonthData(currentMonth);
    } catch (err) {
      console.error('Failed to save manual data:', err);
      setError('保存に失敗しました');
    } finally {
      setIsSaving(false);
    }
  }, [selectedDate, totalTrucks, fixedTrucks, note, repository, fetchMonthData, currentMonth]);

  // 削除
  const onDelete = useCallback(async () => {
    if (!selectedDate) return;

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await repository.deleteManual(selectedDate);
      
      setSuccessMessage('削除しました');
      setTotalTrucks(0);
      setFixedTrucks(0);
      setNote('');
      
      // カレンダーを再取得
      await fetchMonthData(currentMonth);
    } catch (err) {
      console.error('Failed to delete manual data:', err);
      setError('削除に失敗しました');
    } finally {
      setIsSaving(false);
    }
  }, [selectedDate, repository, fetchMonthData, currentMonth]);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccessMessage(null);
  }, []);

  return {
    currentMonth,
    forecastData,
    selectedDate,
    totalTrucks,
    fixedTrucks,
    note,
    isLoading,
    isSaving,
    error,
    successMessage,
    onChangeMonth,
    onSelectDate,
    onChangeTotalTrucks,
    onChangeFixedTrucks,
    onChangeNote,
    onSubmit,
    onDelete,
    clearMessages,
  };
};
