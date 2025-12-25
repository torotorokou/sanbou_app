/**
 * Period Selector - Pure Functions
 *
 * 期間選択に関する純粋関数（ビジネスロジック）
 */

import type { Dayjs } from 'dayjs';
import type { MonthRange } from '../domain/types';

/**
 * 月範囲を計算する
 *
 * @param start - 開始月
 * @param end - 終了月
 * @returns YYYY-MM形式の月の配列（最大24ヶ月）
 */
export function getMonthRange(start: Dayjs | null, end: Dayjs | null): MonthRange {
  if (!start || !end) return [];

  const range: string[] = [];
  let current = start.startOf('month');

  while (current.isBefore(end.endOf('month')) || current.isSame(end, 'month')) {
    range.push(current.format('YYYY-MM'));
    current = current.add(1, 'month');
    if (range.length > 24) break;
  }

  return range;
}

/**
 * 期間範囲が有効かチェックする
 */
export function isValidPeriodRange(start: Dayjs | null, end: Dayjs | null): boolean {
  if (!start || !end) return false;
  return !end.isBefore(start, 'month');
}
