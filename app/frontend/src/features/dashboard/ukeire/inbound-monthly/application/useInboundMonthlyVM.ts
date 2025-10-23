/**
 * inbound-monthly/application/useInboundMonthlyVM.ts
 * 月次実績集計・累積整形を担当するViewModel
 * TODO: 日次実績・累積カードのデータ整形ロジックをここに集約
 */

import { useMemo } from "react";
import type { DailyActualsCardProps } from "../ui/DailyActualsCard";
import type { DailyCumulativeCardProps } from "../ui/DailyCumulativeCard";

export type UseInboundMonthlyVMParams = {
  // TODO: 必要なパラメータを定義（例：日次データ配列、累積データ配列など）
  dailyData: Array<{
    date: string;
    actual?: number;
    prevMonth?: number;
    prevYear?: number;
  }>;
  cumulativeData: Array<{
    date: string;
    cumActual: number;
    cumPrevMonth: number;
    cumPrevYear: number;
  }>;
};

export type UseInboundMonthlyVMResult = {
  dailyProps: DailyActualsCardProps;
  cumulativeProps: DailyCumulativeCardProps;
};

/**
 * 月次実績用のVMロジック
 * - 日次実績チャートデータ整形
 * - 累積チャートデータ整形
 */
export function useInboundMonthlyVM(params: UseInboundMonthlyVMParams): UseInboundMonthlyVMResult {
  const { dailyData, cumulativeData } = params;

  // TODO: 実装を追加
  // 仮実装：受け取ったデータをそのまま返す
  const dailyProps: DailyActualsCardProps = useMemo(
    () => ({
      chartData: dailyData.map((d) => ({
        label: d.date.slice(8, 10),
        actual: d.actual,
        dateFull: d.date,
        prevMonth: d.prevMonth ?? null,
        prevYear: d.prevYear ?? null,
      })),
    }),
    [dailyData]
  );

  const cumulativeProps: DailyCumulativeCardProps = useMemo(
    () => ({
      cumData: cumulativeData.map((d) => ({
        label: d.date.slice(8, 10),
        yyyyMMdd: d.date,
        actualCumulative: d.cumActual,
        prevMonthCumulative: d.cumPrevMonth,
        prevYearCumulative: d.cumPrevYear,
      })),
    }),
    [cumulativeData]
  );

  return { dailyProps, cumulativeProps };
}
