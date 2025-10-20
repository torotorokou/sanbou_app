/**
 * Ukeire Volume Combined ViewModel
 * actuals/history/forecast の3つのVMを統合し、UI用に整形
 */

import { useState } from "react";
import dayjs from "dayjs";
import type { IsoMonth } from "../../model/types";
import type { UkeireActualsRepository } from "../../actuals/repository/UkeireActualsRepository";
import type { UkeireHistoryRepository } from "../../history/repository/UkeireHistoryRepository";
import type { UkeireForecastRepository } from "../../forecast/repository/UkeireForecastRepository";
import { useUkeireActualsVM } from "../../actuals/hooks/useUkeireActualsVM";
import { useUkeireHistoryVM } from "../../history/hooks/useUkeireHistoryVM";
import { useUkeireForecastVM } from "../../forecast/hooks/useUkeireForecastVM";
import type { TargetCardProps } from "@/features/kpiTarget/ui/TargetCard";
import type { DailyActualsCardProps } from "../../actuals/ui/DailyActualsCard";
import type { DailyCumulativeCardProps } from "../../actuals/ui/DailyCumulativeCard";
import type { CombinedDailyCardProps } from "../../history/ui/CombinedDailyCard";
import type { ForecastCardProps } from "../../forecast/ui/ForecastCard";

export type UkeireVolumeCombinedViewState = {
  month: IsoMonth;
  monthJP: string;
  loading: boolean;
  error: Error | null;
  
  // Card Props
  targetCardProps: TargetCardProps | null;
  dailyActualsProps: DailyActualsCardProps | null;
  dailyCumulativeProps: DailyCumulativeCardProps | null;
  combinedDailyProps: CombinedDailyCardProps | null;
  forecastCardProps: ForecastCardProps | null;
  
  // Header
  headerProps: {
    todayBadge: string;
  } | null;
};

export type UkeireVolumeCombinedViewProps = {
  actualsRepository: UkeireActualsRepository;
  historyRepository: UkeireHistoryRepository;
  forecastRepository: UkeireForecastRepository;
  initialMonth?: IsoMonth;
};

/**
 * 受入量ダッシュボード統合ViewModel
 * 3つのRepositoryから独立してデータ取得し、UI Propsに変換
 */
export function useUkeireVolumeCombinedVM({
  actualsRepository,
  historyRepository,
  forecastRepository,
  initialMonth,
}: UkeireVolumeCombinedViewProps): UkeireVolumeCombinedViewState & {
  setMonth: (m: IsoMonth) => void;
} {
  const [month, setMonth] = useState<IsoMonth>(
    initialMonth || dayjs().format("YYYY-MM")
  );

  // 各VMを呼び出し
  const forecastVM = useUkeireForecastVM(forecastRepository, month);
  const actualsVM = useUkeireActualsVM(actualsRepository, month);
  const historyVM = useUkeireHistoryVM(historyRepository, month);

  // 統合状態
  const loading = forecastVM.loading || actualsVM.loading || historyVM.loading;
  const error = actualsVM.error || historyVM.error || null;

  // forecastVMから必要なpropsを取得（既存実装を再利用）
  // TODO: 実際には各VMから必要なデータを組み合わせて新しいpropsを生成
  // 現状はforecastVMが全データを持っているため、それを流用
  
  return {
    month,
    monthJP: dayjs(month).format("YYYY年MM月"),
    loading,
    error,
    targetCardProps: forecastVM.targetCardProps,
    dailyActualsProps: null, // TODO: actualsVMから生成
    dailyCumulativeProps: null, // TODO: actualsVMから生成
    combinedDailyProps: forecastVM.combinedDailyProps,
    forecastCardProps: forecastVM.forecastCardProps,
    headerProps: forecastVM.headerProps,
    setMonth,
  };
}
