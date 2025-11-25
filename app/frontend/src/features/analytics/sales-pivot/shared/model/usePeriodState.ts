/**
 * shared/model/usePeriodState.ts
 * 期間状態管理用カスタムフック
 */

import { useState } from 'react';
import dayjs, { type Dayjs } from 'dayjs';

/**
 * 期間モード: 単月 or 期間範囲
 */
export type PeriodMode = 'single' | 'range';

/**
 * 期間状態管理の戻り値
 */
export interface PeriodState {
  periodMode: PeriodMode;
  month: Dayjs;
  range: [Dayjs, Dayjs] | null;
  setPeriodMode: (mode: PeriodMode) => void;
  setMonth: (month: Dayjs) => void;
  setRange: (range: [Dayjs, Dayjs] | null) => void;
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
  const [periodMode, setPeriodMode] = useState<PeriodMode>('single');
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);

  return {
    periodMode,
    month,
    range,
    setPeriodMode,
    setMonth,
    setRange,
  };
}
