/**
 * inbound-monthly/application/useInboundMonthlyVM.ts
 * 日次搬入量データのフェッチと整形を担当するViewModel
 *
 * 責務：
 * - API経由でデータ取得
 * - 日次実績チャート用データ整形
 * - 累積チャート用データ整形
 * - 営業カレンダーデータの統合
 */

import { useMemo, useState, useCallback, useEffect } from 'react';
import dayjs from 'dayjs';
import type { DailyActualsCardProps } from '../ui/cards/DailyActualsCard';
import type { DailyCumulativeCardProps } from '../ui/cards/DailyCumulativeCard';
import type { InboundDailyRepository } from '../ports/InboundDailyRepository';
import type { ICalendarRepository } from '@/features/calendar/ports/repository';
import type { CalendarDayDTO } from '@/features/calendar/domain/types';

export type UseInboundMonthlyVMParams = {
  repository: InboundDailyRepository;
  /** 営業カレンダーのリポジトリ */
  calendarRepository?: ICalendarRepository;
  /** 選択中の年月（YYYY-MM形式） */
  month: string;
};

export type UseInboundMonthlyVMResult = {
  loading: boolean;
  error: Error | null;
  dailyProps: DailyActualsCardProps | null;
  cumulativeProps: DailyCumulativeCardProps | null;
  refetch: () => void;
};

/**
 * day_type から status を判定（営業カレンダーと統一）
 */
function mapDayTypeToStatus(dayType: string): 'business' | 'holiday' | 'closed' {
  switch (dayType) {
    case 'CLOSED':
      return 'closed';
    case 'RESERVATION':
      return 'holiday';
    case 'NORMAL':
    default:
      return 'business';
  }
}

/**
 * 日次搬入量データのフェッチと整形
 *
 * - month変更時に自動でデータ再取得
 * - cum_scope="month"で累積計算
 * - データ整形してDailyActualsCard/DailyCumulativeCardに渡す
 * - 営業カレンダーのステータスを統合
 */
export function useInboundMonthlyVM(params: UseInboundMonthlyVMParams): UseInboundMonthlyVMResult {
  const { repository, calendarRepository, month } = params;

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [dailyProps, setDailyProps] = useState<DailyActualsCardProps | null>(null);
  const [cumulativeProps, setCumulativeProps] = useState<DailyCumulativeCardProps | null>(null);

  // 月の範囲計算（start=月初、end=月末）
  const { start, end, year, monthNum } = useMemo(() => {
    const monthStart = dayjs(month, 'YYYY-MM').startOf('month');
    const monthEnd = monthStart.endOf('month');
    return {
      start: monthStart.format('YYYY-MM-DD'),
      end: monthEnd.format('YYYY-MM-DD'),
      year: monthStart.year(),
      monthNum: monthStart.month() + 1,
    };
  }, [month]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 営業カレンダーデータを取得（calendarRepositoryがある場合のみ）
      let calendarMap: Map<string, CalendarDayDTO> | null = null;
      if (calendarRepository) {
        try {
          const calendarData = await calendarRepository.fetchMonth({
            year,
            month: monthNum,
          });
          calendarMap = new Map(calendarData.map((d) => [d.ddate, d]));
        } catch (calErr) {
          console.warn(
            '営業カレンダーデータの取得に失敗しました（フォールバックロジックを使用）:',
            calErr
          );
        }
      }

      // cum_scope="month"で月内累積を取得
      const data = await repository.fetchDaily({
        start,
        end,
        segment: null,
        cum_scope: 'month',
      });

      // 日次実績データ整形（営業カレンダーのステータスを統合）
      const dailyChartData = data.map((row) => {
        const calendarDay = calendarMap?.get(row.ddate);
        const status = calendarDay ? mapDayTypeToStatus(calendarDay.day_type) : undefined;

        return {
          label: dayjs(row.ddate).format('DD'),
          actual: row.ton,
          dateFull: row.ddate,
          prevMonth: row.prev_month_ton ?? null, // 先月（4週前）の同曜日データ
          prevYear: row.prev_year_ton ?? null, // 前年の同ISO週・同曜日データ
          status, // 営業カレンダーのステータスを追加
        };
      });

      // 累積データ整形（X軸を0スタートに変更、0日目=0tを追加）
      const cumulativeChartData = [
        // 0日目の初期値（月初前日=0t）
        {
          label: '0',
          yyyyMMdd: dayjs(start).subtract(1, 'day').format('YYYY-MM-DD'),
          actualCumulative: 0,
          prevMonthCumulative: 0,
          prevYearCumulative: 0,
        },
        // 1日目以降のデータ（index+1でラベル付け）
        ...data.map((row, index) => ({
          label: String(index + 1),
          yyyyMMdd: row.ddate,
          actualCumulative: row.cum_ton ?? 0,
          prevMonthCumulative: row.prev_month_cum_ton ?? 0, // 先月の累積データ
          prevYearCumulative: row.prev_year_cum_ton ?? 0, // 前年の累積データ
        })),
      ];

      setDailyProps({ chartData: dailyChartData });
      setCumulativeProps({ cumData: cumulativeChartData });
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [repository, calendarRepository, start, end, year, monthNum]);

  // month変更時に自動再取得
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    loading,
    error,
    dailyProps,
    cumulativeProps,
    refetch: fetchData,
  };
}
