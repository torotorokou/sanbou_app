/**
 * 受入量 - Series Service
 * データ系列の変換・計算ロジック（純粋関数）
 */

import dayjs from "dayjs";
import type { IsoMonth, IsoDate, TargetsDTO, CalendarDay, DailyCurveDTO } from "../model/types";

/** DateをYYYY-MM-DD形式に変換 */
export const ymd = (d: Date): string =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;

/** 指定日が属する週の月曜日を取得（ISO 8601） */
export const mondayOf = (d: Date): Date => {
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  const m = new Date(d);
  m.setDate(d.getDate() + diff);
  m.setHours(0, 0, 0, 0);
  return m;
};

/** n日後のDateを取得 */
export const addDays = (d: Date, n: number): Date => {
  const x = new Date(d);
  x.setDate(d.getDate() + n);
  return x;
};

/** 配列の合計 */
export const sum = (a: number[]): number => a.reduce((p, c) => p + c, 0);

/** 値を範囲内にクランプ */
export const clamp = (v: number, lo: number, hi: number): number =>
  Math.max(lo, Math.min(hi, v));

/** YYYY-MM形式を「YYYY年MM月」に変換 */
export const monthNameJP = (m: IsoMonth): string => {
  const [y, mm] = m.split("-").map(Number);
  return `${y}年${mm}月`;
};

/** 現在月を取得 */
export const curMonth = (): IsoMonth => dayjs().format("YYYY-MM");

/** 翌月を取得 */
export const nextMonth = (m: IsoMonth): IsoMonth =>
  dayjs(m + "-01")
    .add(1, "month")
    .format("YYYY-MM");

/**
 * 指定月における「今日」を取得
 * - 現在月なら今日、過去月なら20日(or月末)、未来月なら初日
 */
export const todayInMonth = (m: IsoMonth): IsoDate => {
  const nowM = curMonth();
  if (m === nowM) return dayjs().format("YYYY-MM-DD");
  const last = dayjs(m + "-01")
    .endOf("month")
    .date();
  const d = Math.min(20, last);
  return `${m}-${String(d).padStart(2, "0")}`;
};

/**
 * 実績カットオフ日を取得（昨日まで表示）
 */
export const getActualCutoffIso = (m: IsoMonth): IsoDate => {
  const now = dayjs();
  const monthStart = dayjs(m + "-01");
  if (monthStart.isSame(now, "month"))
    return now.subtract(1, "day").format("YYYY-MM-DD");
  if (monthStart.isBefore(now, "month"))
    return monthStart.endOf("month").format("YYYY-MM-DD");
  return monthStart.startOf("month").subtract(1, "day").format("YYYY-MM-DD");
};

/**
 * 達成率を計算
 */
export const calculateAchievementRate = (actual: number, target: number): number => {
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

/**
 * 1営業日あたりの目標トン数を計算
 */
export const calculateOneBusinessDayTarget = (
  targets: TargetsDTO,
  calendarDays: CalendarDay[]
): number => {
  const dayWeight = targets.day_weights;
  const toDate = (s: string): Date => new Date(s + "T00:00:00");

  const weekdayCount = calendarDays.filter(
    (d) => d.is_business_day && toDate(d.date).getDay() >= 1 && toDate(d.date).getDay() <= 5
  ).length;
  const satCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 6).length;
  const sunHolCount = calendarDays.filter((d) => d.is_business_day && toDate(d.date).getDay() === 0).length;

  const businessDayCount = weekdayCount + satCount;
  const businessWeight = dayWeight.weekday + dayWeight.sat;

  const totalW = businessDayCount * businessWeight + sunHolCount * dayWeight.sun_hol || 1;
  return Math.round((targets.month * (businessWeight / totalW)) || 0);
};

/**
 * 今週の目標・実績を計算
 */
export const calculateWeekStats = (
  targets: TargetsDTO,
  calendarDays: CalendarDay[],
  daily_curve?: DailyCurveDTO[]
): { target: number; actual: number } => {
  const toDate = (s: string): Date => new Date(s + "T00:00:00");
  const todayStr = dayjs().format("YYYY-MM-DD");
  const dayEntry = calendarDays.find((d) => d.date === todayStr) || calendarDays[0];
  const todayWeekId = dayEntry.week_id;

  const weekIds = Array.from(new Set(calendarDays.map((d) => d.week_id))).sort();
  let idx = 0;
  let currentIdx = 1;
  for (const wid of weekIds) {
    const inMonthBiz = calendarDays.filter((d) => d.week_id === wid && d.is_business_day).length;
    if (inMonthBiz > 0) idx += 1;
    if (wid === todayWeekId) {
      currentIdx = idx;
      break;
    }
  }

  const curWeek = targets.weeks.find((w) => w.bw_idx === currentIdx) ?? targets.weeks[targets.weeks.length - 1];
  const weekTarget = curWeek ? curWeek.week_target : 0;

  const thisWeekActual = daily_curve
    ? sum(
        daily_curve
          .filter((d) => {
            const wstart = mondayOf(toDate(todayStr));
            return toDate(d.date) >= wstart && toDate(d.date) <= addDays(wstart, 6);
          })
          .map((d) => d.actual ?? 0)
      )
    : 0;

  return { target: weekTarget, actual: thisWeekActual };
};

/**
 * 今日の実績を取得
 */
export const getTodayActual = (daily_curve?: DailyCurveDTO[]): number => {
  const todayStr = dayjs().format("YYYY-MM-DD");
  return daily_curve ? daily_curve.find((d) => d.date === todayStr)?.actual ?? 0 : 0;
};


