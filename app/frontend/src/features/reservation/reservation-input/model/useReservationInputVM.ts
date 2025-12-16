/**
 * useReservationInputVM - 予約手入力 ViewModel
 * 
 * Model (状態管理・ビジネスロジック)
 * 規約: ViewModel hooks は useXxxVM.ts 命名に統一
 * 
 * 責務: 手入力フォームの状態管理・保存・削除
 */

import { useState, useCallback } from 'react';
import { message } from 'antd';
import type { Dayjs } from 'dayjs';
import type {
  ReservationDailyRepository,
  ReservationManualInput,
} from '../../shared';
import { reservationDailyMockRepository } from '../../shared';

export interface ReservationInputViewModel {
  // State
  selectedDate: Dayjs | null;
  totalTrucks: number | null;
  fixedTrucks: number | null;
  note: string;
  isSaving: boolean;
  error: string | null;
  hasManualData: boolean;

  // Events
  onSelectDate: (date: Dayjs | null) => void;
  onChangeTotalTrucks: (value: number | null) => void;
  onChangeFixedTrucks: (value: number | null) => void;
  onChangeNote: (value: string) => void;
  onSubmit: () => Promise<void>;
  onDelete: () => Promise<void>;
  clearMessages: () => void;
}

export const useReservationInputVM = (
  repository: ReservationDailyRepository = reservationDailyMockRepository,
  onDataChanged?: () => void
): ReservationInputViewModel => {
  const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
  const [totalTrucks, setTotalTrucks] = useState<number | null>(null);
  const [fixedTrucks, setFixedTrucks] = useState<number | null>(null);
  const [note, setNote] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasManualData, setHasManualData] = useState<boolean>(false);

  const clearMessages = useCallback(() => {
    setError(null);
  }, []);

  const onSelectDate = useCallback((date: Dayjs | null) => {
    setSelectedDate(date);
    clearMessages();
    // TODO: 選択日のデータを取得してhasManualDataを更新
    setHasManualData(false);
  }, [clearMessages]);

  const onChangeTotalTrucks = useCallback((value: number | null) => {
    setTotalTrucks(value);
    clearMessages();
  }, [clearMessages]);

  const onChangeFixedTrucks = useCallback((value: number | null) => {
    setFixedTrucks(value);
    clearMessages();
  }, [clearMessages]);

  const onChangeNote = useCallback((value: string) => {
    setNote(value);
  }, []);

  const onSubmit = useCallback(async () => {
    if (!selectedDate) {
      setError('日付を選択してください');
      return;
    }
    if (totalTrucks === null || totalTrucks === undefined) {
      setError('総台数を入力してください');
      return;
    }
    if (fixedTrucks === null || fixedTrucks === undefined) {
      setError('固定客数を入力してください');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const payload: ReservationManualInput = {
        reserve_date: selectedDate.format('YYYY-MM-DD'),
        total_trucks: totalTrucks,
        fixed_trucks: fixedTrucks,
        note: note || undefined,
      };

      await repository.upsertManual(payload);
      message.success('保存しました');
      setHasManualData(true);
      
      // 親コンポーネントに変更を通知
      if (onDataChanged) {
        onDataChanged();
      }
    } catch (err: unknown) {
      console.error('Failed to save manual data:', err);
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      setError(`保存に失敗しました: ${errorMessage}`);
    } finally {
      setIsSaving(false);
    }
  }, [selectedDate, totalTrucks, fixedTrucks, note, repository, onDataChanged]);

  const onDelete = useCallback(async () => {
    if (!selectedDate) return;

    setIsSaving(true);
    setError(null);

    try {
      await repository.deleteManual(selectedDate.format('YYYY-MM-DD'));
      message.success('削除しました');
      setTotalTrucks(null);
      setFixedTrucks(null);
      setNote('');
      setHasManualData(false);
      
      // 親コンポーネントに変更を通知
      if (onDataChanged) {
        onDataChanged();
      }
    } catch (err: unknown) {
      console.error('Failed to delete manual data:', err);
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      setError(`削除に失敗しました: ${errorMessage}`);
    } finally {
      setIsSaving(false);
    }
  }, [selectedDate, repository, onDataChanged]);

  return {
    selectedDate,
    totalTrucks,
    fixedTrucks,
    note,
    isSaving,
    error,
    hasManualData,
    onSelectDate,
    onChangeTotalTrucks,
    onChangeFixedTrucks,
    onChangeNote,
    onSubmit,
    onDelete,
    clearMessages,
  };
};
