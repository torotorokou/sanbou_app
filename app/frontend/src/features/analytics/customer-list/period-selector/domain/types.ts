/**
 * Period Selector Sub-Feature
 * 
 * 期間選択機能を独立したサブフィーチャーとして実装
 */

import type { Dayjs } from 'dayjs';

/**
 * 期間範囲
 */
export interface PeriodRange {
    start: Dayjs | null;
    end: Dayjs | null;
}

/**
 * 比較期間（今期 vs 前期）
 */
export interface ComparisonPeriods {
    current: PeriodRange;
    previous: PeriodRange;
}

/**
 * 月範囲（YYYY-MM形式の配列）
 */
export type MonthRange = string[];
