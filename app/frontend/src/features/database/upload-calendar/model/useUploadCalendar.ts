/**
 * アップロードカレンダー ViewModel Hook
 * カレンダー表示に必要な状態とロジックを提供
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import dayjs from 'dayjs';
import type { UploadCalendarItem, CalendarDay, CalendarWeek } from './types';
import { uploadCalendarRepository } from '../infrastructure/uploadCalendar.repository';

export interface UseUploadCalendarResult {
  currentMonth: Date;
  weeks: CalendarWeek[];
  isLoading: boolean;
  error: string | null;
  goPrevMonth: () => void;
  goNextMonth: () => void;
  reload: () => void;
  deleteUpload: (params: {
    uploadFileId: number;
    date: string;
    csvKind: UploadCalendarItem['kind'];
  }) => Promise<void>;
  uploadsByDate: Record<string, UploadCalendarItem[]>;
}

/**
 * アップロードカレンダー Hook
 */
export function useUploadCalendar(): UseUploadCalendarResult {
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [items, setItems] = useState<UploadCalendarItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // データ取得
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth() + 1; // JavaScript の月は 0-indexed
      const data = await uploadCalendarRepository.fetchMonthly({ year, month });
      setItems(data.filter(item => !item.deleted)); // 削除済みは除外
    } catch (err) {
      console.error('Failed to fetch upload calendar:', err);
      setError(err instanceof Error ? err.message : 'データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [currentMonth.getFullYear(), currentMonth.getMonth()]);

  // 初回マウント時と currentMonth 変更時にデータ取得
  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  // 月移動
  const goPrevMonth = useCallback(() => {
    setCurrentMonth(prev => {
      const d = dayjs(prev).subtract(1, 'month');
      return d.toDate();
    });
  }, []);

  const goNextMonth = useCallback(() => {
    setCurrentMonth(prev => {
      const d = dayjs(prev).add(1, 'month');
      return d.toDate();
    });
  }, []);

  // 再読み込み
  const reload = useCallback(() => {
    void fetchData();
  }, [fetchData]);

  // 削除
  const deleteUpload = useCallback(async (params: {
    uploadFileId: number;
    date: string;
    csvKind: UploadCalendarItem['kind'];
  }) => {
    await uploadCalendarRepository.deleteUpload(params);
    // 削除後に再取得
    await fetchData();
  }, [fetchData]);

  // 日付ごとのアップロードマップを作成
  const uploadsByDate = useMemo(() => {
    const map: Record<string, UploadCalendarItem[]> = {};
    for (const item of items) {
      if (!map[item.date]) {
        map[item.date] = [];
      }
      map[item.date].push(item);
    }
    return map;
  }, [items]);

  // カレンダーの週構造を生成
  const weeks = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    // 月の最初の日と最後の日
    const firstDayOfMonth = dayjs(new Date(year, month, 1));
    const lastDayOfMonth = firstDayOfMonth.endOf('month');

    // カレンダー表示の開始日（週の始まりを日曜日とする）
    const startDate = firstDayOfMonth.startOf('week');
    // カレンダー表示の終了日（週の終わりを土曜日とする）
    const endDate = lastDayOfMonth.endOf('week');

    const calendarWeeks: CalendarWeek[] = [];
    let currentWeek: CalendarDay[] = [];
    let currentDate = startDate;

    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate, 'day')) {
      const dateStr = currentDate.format('YYYY-MM-DD');
      const isCurrentMonth = currentDate.month() === month;

      // その日のアップロード情報を種別ごとに整理
      const dayUploads = uploadsByDate[dateStr] || [];
      const uploadsByKind: CalendarDay['uploadsByKind'] = {};
      for (const upload of dayUploads) {
        if (!uploadsByKind[upload.kind]) {
          uploadsByKind[upload.kind] = [];
        }
        uploadsByKind[upload.kind]!.push(upload);
      }

      currentWeek.push({
        date: dateStr,
        isCurrentMonth,
        uploadsByKind,
      });

      // 週の終わり（土曜日）に達したら週を確定
      if (currentWeek.length === 7) {
        calendarWeeks.push({ days: currentWeek });
        currentWeek = [];
      }

      currentDate = currentDate.add(1, 'day');
    }

    // 最後の週が残っていたら追加
    if (currentWeek.length > 0) {
      calendarWeeks.push({ days: currentWeek });
    }

    return calendarWeeks;
  }, [currentMonth, uploadsByDate]);

  return {
    currentMonth,
    weeks,
    isLoading,
    error,
    goPrevMonth,
    goNextMonth,
    reload,
    deleteUpload,
    uploadsByDate,
  };
}
