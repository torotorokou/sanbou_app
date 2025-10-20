/**
 * 受入量 - Calendar Service
 * カレンダー関連のドメインロジック
 */

import type { CalendarDay, IsoDate } from "../model/types";

/**
 * ISO Date文字列からDateオブジェクトを生成
 */
export const toDate = (s: string): Date => new Date(s + "T00:00:00");

/**
 * 指定日が第2日曜日かどうかを判定
 */
export const isSecondSunday = (date: IsoDate): boolean => {
  const d = toDate(date);
  const dow = d.getDay();
  if (dow !== 0) return false;

  const monthStart = new Date(d.getFullYear(), d.getMonth(), 1);
  let count = 0;
  let cur = new Date(monthStart);

  while (cur <= d) {
    if (cur.getDay() === 0) count += 1;
    cur.setDate(cur.getDate() + 1);
  }

  return count === 2;
};

/**
 * 日付の色を取得（営業日カレンダー用）
 */
export const getDateColor = (date: IsoDate): string => {
  const C = {
    ok: "#52c41a",
    danger: "#cf1322",
    sunday: "#ff85c0",
  };

  if (isSecondSunday(date)) return C.danger;

  const d = toDate(date);
  const dow = d.getDay();
  if (dow === 0) return C.sunday;

  return C.ok;
};

/**
 * 日種別ごとのカウントを算出
 */
export const countDayTypes = (
  days: CalendarDay[],
  today: IsoDate
): {
  weekday: number;
  sunday: number;
  secondSunday: number;
  weekdayRem: number;
  sundayRem: number;
  secondSundayRem: number;
} => {
  let weekday = 0,
    sunday = 0,
    secondSunday = 0;
  let weekdayRem = 0,
    sundayRem = 0,
    secondSundayRem = 0;

  days.forEach((d) => {
    const dt = toDate(d.date);
    const dow = dt.getDay();
    const isSecond = isSecondSunday(d.date);

    if (isSecond) {
      secondSunday += 1;
      if (d.date >= today) secondSundayRem += 1;
    } else if (dow === 0) {
      sunday += 1;
      if (d.date >= today) sundayRem += 1;
    } else {
      weekday += 1;
      if (d.date >= today) weekdayRem += 1;
    }
  });

  return { weekday, sunday, secondSunday, weekdayRem, sundayRem, secondSundayRem };
};
