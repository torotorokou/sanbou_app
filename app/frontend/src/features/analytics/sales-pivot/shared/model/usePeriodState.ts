/**
 * shared/model/usePeriodState.ts
 * 期間状態管理用カスタムフック
 */

import { useState } from 'react';
import dayjs, { type Dayjs } from 'dayjs';

/**
 * 粒度: 月次 or 日次
 */
export type Granularity = 'month' | 'date';

/**
 * 期間モード: 単一 or 期間範囲
 */
export type PeriodMode = 'single' | 'range';

/**
 * 期間状態管理の戻り値
 */
export interface PeriodState {
  granularity: Granularity;
  periodMode: PeriodMode;
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  singleDate: Dayjs;
  dateRange: [Dayjs, Dayjs] | null;
  setGranularity: (granularity: Granularity) => void;
  setPeriodMode: (mode: PeriodMode) => void;
  setMonth: (month: Dayjs) => void;
  setRange: (range: [Dayjs, Dayjs] | null) => void;
  setSingleDate: (date: Dayjs) => void;
  setDateRange: (range: [Dayjs, Dayjs] | null) => void;
}

/**
 * 期間関連の状態を管理するカスタムフック
 * 
 * @description
 * - periodMode: 'single' (単月) or 'range' (期間範囲)
 * - month: 単月モード時の対象月
 * - range: 期間範囲モード時の開始月〜終了月
 * 
 * @returns {PeriodState} 期間状態とセッター関数
 */
export function usePeriodState(): PeriodState {
  const [granularity, setGranularity] = useState<Granularity>('month');
  const [periodMode, setPeriodMode] = useState<PeriodMode>('single');
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [singleDate, setSingleDate] = useState<Dayjs>(dayjs());
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);

  return {
    granularity,
    periodMode,
    month,
    range,
    singleDate,
    dateRange,
    setGranularity,
    setPeriodMode,
    setMonth,
    setRange,
    setSingleDate,
    setDateRange,
  };
}
