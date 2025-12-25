/**
 * 受入ダッシュボード - Target Service
 * 目標関連の計算ロジック
 */

import dayjs from "dayjs";
import type { CalendarDay, TargetsDTO, DailyCurveDTO } from "../types";
import { toDate, mondayOf, addDays, sum } from "../valueObjects";

/**
 * 1営業日あたりの目標トン数を計算
 */
export const calculateOneBusinessDayTarget = (
  targets: TargetsDTO,
  calendarDays: CalendarDay[],
): number => {
  const dayWeight = targets.day_weights;

  const weekdayCount = calendarDays.filter(
    (d) =>
      d.is_business_day &&
      toDate(d.date).getDay() >= 1 &&
      toDate(d.date).getDay() <= 5,
  ).length;
  const satCount = calendarDays.filter(
    (d) => d.is_business_day && toDate(d.date).getDay() === 6,
  ).length;
  const sunHolCount = calendarDays.filter(
    (d) => d.is_business_day && toDate(d.date).getDay() === 0,
  ).length;

  const businessDayCount = weekdayCount + satCount;
  const businessWeight = dayWeight.weekday + dayWeight.sat;

  const totalW =
    businessDayCount * businessWeight + sunHolCount * dayWeight.sun_hol || 1;
  return Math.round(targets.month * (businessWeight / totalW) || 0);
};

/**
 * 今週の目標・実績を計算
 */
export const calculateWeekStats = (
  targets: TargetsDTO,
  calendarDays: CalendarDay[],
  daily_curve?: DailyCurveDTO[],
): { target: number; actual: number } => {
  const todayStr = dayjs().format("YYYY-MM-DD");
  const dayEntry =
    calendarDays.find((d) => d.date === todayStr) || calendarDays[0];
  const todayWeekId = dayEntry.week_id;

  const weekIds = Array.from(
    new Set(calendarDays.map((d) => d.week_id)),
  ).sort();
  let idx = 0;
  let currentIdx = 1;
  for (const wid of weekIds) {
    const inMonthBiz = calendarDays.filter(
      (d) => d.week_id === wid && d.is_business_day,
    ).length;
    if (inMonthBiz > 0) idx += 1;
    if (wid === todayWeekId) {
      currentIdx = idx;
      break;
    }
  }

  const curWeek =
    targets.weeks.find((w) => w.bw_idx === currentIdx) ??
    targets.weeks[targets.weeks.length - 1];
  const weekTarget = curWeek ? curWeek.week_target : 0;

  const thisWeekActual = daily_curve
    ? sum(
        daily_curve
          .filter((d) => {
            const wstart = mondayOf(toDate(todayStr));
            return (
              toDate(d.date) >= wstart && toDate(d.date) <= addDays(wstart, 6)
            );
          })
          .map((d) => d.actual ?? 0),
      )
    : 0;

  return { target: weekTarget, actual: thisWeekActual };
};

/**
 * 今日の実績を取得
 */
export const getTodayActual = (daily_curve?: DailyCurveDTO[]): number => {
  const todayStr = dayjs().format("YYYY-MM-DD");
  return daily_curve
    ? (daily_curve.find((d) => d.date === todayStr)?.actual ?? 0)
    : 0;
};

/**
 * 達成率を計算
 */
export const calculateAchievementRate = (
  actual: number,
  target: number,
): number => {
  return target ? Math.round((actual / target) * 100) : 0;
};

/**
 * 達成率に基づく色を取得
 */
export const getAchievementColor = (actual: number, target: number): string => {
  const C = {
    ok: "#389e0d",
    warn: "#fa8c16",
    danger: "#cf1322",
  };

  const ratio = target ? actual / target : 0;
  if (ratio >= 1) return C.ok;
  if (ratio >= 0.9) return C.warn;
  return C.danger;
};
