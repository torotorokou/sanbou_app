/**
 * kpi-targets/application/useTargetsVM.ts
 * KPI目標達成率計算・表示整形を担当するViewModel
 *
 * 達成率モード:
 *   - "toDate": 昨日までの累計目標に対する達成率
 *   - "toEnd": 期末（週末・月末）のトータル目標に対する達成率
 */

import { useMemo } from "react";
import type { TargetCardRowData } from "../ui/cards/TargetCard";

export type AchievementMode = "toDate" | "toEnd";

export type UseTargetsVMParams = {
  mode: AchievementMode;
  // Cumulative targets (month_start/week_start to yesterday)
  monthTargetToDate: number | null;
  weekTargetToDate: number | null;
  dayTarget: number | null;
  // Total targets (entire period)
  monthTargetTotal: number | null;
  weekTargetTotal: number | null;
  // Actuals (cumulative to yesterday)
  todayActual: number | null;
  weekActual: number | null;
  monthActual: number | null;
  // 週次・日次を非表示にするかどうか(当月以外の場合true)
  hideWeekAndDay?: boolean;
};

export type UseTargetsVMResult = {
  rows: TargetCardRowData[];
};

/**
 * 目標カード用のVMロジック
 * - mode に応じて目標値（分母）を切り替え
 * - "toDate" モード: 昨日までの累計目標に対する達成率
 * - "toEnd" モード: 期末（週末・月末）のトータル目標に対する達成率
 */
export function useTargetsVM(params: UseTargetsVMParams): UseTargetsVMResult {
  const {
    mode,
    monthTargetToDate,
    weekTargetToDate,
    dayTarget,
    monthTargetTotal,
    weekTargetTotal,
    todayActual,
    weekActual,
    monthActual,
  } = params;

  // mode に応じて分母となる目標値を選択
  const monthTarget = mode === "toDate" ? monthTargetToDate : monthTargetTotal;
  const weekTarget = mode === "toDate" ? weekTargetToDate : weekTargetTotal;

  const rows = useMemo<TargetCardRowData[]>(
    () => [
      {
        key: "month",
        // 改行を入れて UI 側で縦に並べて表示できるようにする
        label: mode === "toDate" ? "当月\n（昨日）" : "当月",
        target: monthTarget,
        actual: monthActual,
      },
      {
        key: "week",
        // 今週ラベルも改行対応（必要に応じて表示が整うように）
        label: mode === "toDate" ? "今週\n（昨日）" : "今週",
        target: weekTarget,
        actual: weekActual,
      },
      {
        key: "day",
        label: "日目標",
        target: dayTarget,
        actual: todayActual,
      },
    ],
    [
      mode,
      monthTarget,
      weekTarget,
      dayTarget,
      todayActual,
      weekActual,
      monthActual,
    ],
  );

  return { rows };
}
