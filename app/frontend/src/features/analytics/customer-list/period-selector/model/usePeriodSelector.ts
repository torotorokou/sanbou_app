/**
 * Period Selector - ViewModel
 *
 * 期間選択の状態管理Hook
 */

import { useState } from "react";
import type { Dayjs } from "dayjs";
import type { ComparisonPeriods } from "../domain/types";
import { isValidPeriodRange } from "./utils";

export interface PeriodSelectorViewModel {
  currentStart: Dayjs | null;
  currentEnd: Dayjs | null;
  previousStart: Dayjs | null;
  previousEnd: Dayjs | null;
  setCurrentStart: (date: Dayjs | null) => void;
  setCurrentEnd: (date: Dayjs | null) => void;
  setPreviousStart: (date: Dayjs | null) => void;
  setPreviousEnd: (date: Dayjs | null) => void;
  isCurrentPeriodValid: boolean;
  isPreviousPeriodValid: boolean;
  isAllPeriodsValid: boolean;
  resetPeriods: () => void;
  getComparisonPeriods: () => ComparisonPeriods;
}

/**
 * 期間選択の状態管理Hook
 */
export function usePeriodSelector(): PeriodSelectorViewModel {
  const [currentStart, setCurrentStart] = useState<Dayjs | null>(null);
  const [currentEnd, setCurrentEnd] = useState<Dayjs | null>(null);
  const [previousStart, setPreviousStart] = useState<Dayjs | null>(null);
  const [previousEnd, setPreviousEnd] = useState<Dayjs | null>(null);

  const isCurrentPeriodValid = isValidPeriodRange(currentStart, currentEnd);
  const isPreviousPeriodValid = isValidPeriodRange(previousStart, previousEnd);
  const isAllPeriodsValid = isCurrentPeriodValid && isPreviousPeriodValid;

  const resetPeriods = () => {
    setCurrentStart(null);
    setCurrentEnd(null);
    setPreviousStart(null);
    setPreviousEnd(null);
  };

  const getComparisonPeriods = (): ComparisonPeriods => ({
    current: { start: currentStart, end: currentEnd },
    previous: { start: previousStart, end: previousEnd },
  });

  return {
    currentStart,
    currentEnd,
    previousStart,
    previousEnd,
    setCurrentStart,
    setCurrentEnd,
    setPreviousStart,
    setPreviousEnd,
    isCurrentPeriodValid,
    isPreviousPeriodValid,
    isAllPeriodsValid,
    resetPeriods,
    getComparisonPeriods,
  };
}
