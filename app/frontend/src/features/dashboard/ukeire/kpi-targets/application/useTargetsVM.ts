/**
 * kpi-targets/application/useTargetsVM.ts
 * KPI目標達成率計算・表示整形を担当するViewModel
 * TODO: TargetCard内のロジックをここに抽出してビジネスロジックを分離
 */

import { useMemo } from "react";
import type { TargetCardRowData } from "../ui/cards/TargetCard";

export type UseTargetsVMParams = {
  monthTarget: number;
  weekTarget: number;
  dayTarget: number;
  todayActual: number;
  weekActual: number;
  monthActual: number;
};

export type UseTargetsVMResult = {
  rows: TargetCardRowData[];
};

/**
 * 目標カード用のVMロジック
 * - 各期間の達成率計算
 * - 色分け判定（将来的にここで実施）
 */
export function useTargetsVM(params: UseTargetsVMParams): UseTargetsVMResult {
  const { monthTarget, weekTarget, dayTarget, todayActual, weekActual, monthActual } = params;

  const rows = useMemo<TargetCardRowData[]>(
    () => [
      { key: "month", label: "当月目標", target: monthTarget, actual: monthActual },
      { key: "week", label: "週目標", target: weekTarget, actual: weekActual },
      { key: "day", label: "日目標", target: dayTarget, actual: todayActual },
    ],
    [monthTarget, weekTarget, dayTarget, todayActual, weekActual, monthActual]
  );

  return { rows };
}
