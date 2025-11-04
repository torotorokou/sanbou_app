/**
 * inbound-monthly/application/useInboundMonthlyVM.ts
 * 日次搬入量データのフェッチと整形を担当するViewModel
 * 
 * 責務：
 * - API経由でデータ取得
 * - 日次実績チャート用データ整形
 * - 累積チャート用データ整形
 */

import { useMemo, useState, useCallback, useEffect } from "react";
import dayjs from "dayjs";
import type { DailyActualsCardProps } from "../ui/cards/DailyActualsCard";
import type { DailyCumulativeCardProps } from "../ui/cards/DailyCumulativeCard";
import type { InboundDailyRepository } from "../ports/InboundDailyRepository";

export type UseInboundMonthlyVMParams = {
  repository: InboundDailyRepository;
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
 * 日次搬入量データのフェッチと整形
 * 
 * - month変更時に自動でデータ再取得
 * - cum_scope="month"で累積計算
 * - データ整形してDailyActualsCard/DailyCumulativeCardに渡す
 */
export function useInboundMonthlyVM(params: UseInboundMonthlyVMParams): UseInboundMonthlyVMResult {
  const { repository, month } = params;

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [dailyProps, setDailyProps] = useState<DailyActualsCardProps | null>(null);
  const [cumulativeProps, setCumulativeProps] = useState<DailyCumulativeCardProps | null>(null);

  // 月の範囲計算（start=月初、end=月末）
  const { start, end } = useMemo(() => {
    const monthStart = dayjs(month, "YYYY-MM").startOf("month");
    const monthEnd = monthStart.endOf("month");
    return {
      start: monthStart.format("YYYY-MM-DD"),
      end: monthEnd.format("YYYY-MM-DD"),
    };
  }, [month]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // cum_scope="month"で月内累積を取得
      const data = await repository.fetchDaily({
        start,
        end,
        segment: null,
        cum_scope: "month",
      });

      // 日次実績データ整形
      const dailyChartData = data.map((row) => ({
        label: dayjs(row.ddate).format("DD"),
        actual: row.ton,
        dateFull: row.ddate,
        prevMonth: null, // TODO: 前月・前年データは別途取得が必要
        prevYear: null,
      }));

      // 累積データ整形
      const cumulativeChartData = data.map((row) => ({
        label: dayjs(row.ddate).format("DD"),
        yyyyMMdd: row.ddate,
        actualCumulative: row.cum_ton ?? 0,
        prevMonthCumulative: 0, // TODO: 前月・前年データは別途取得が必要
        prevYearCumulative: 0,
      }));

      setDailyProps({ chartData: dailyChartData });
      setCumulativeProps({ cumData: cumulativeChartData });
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [repository, start, end]);

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

