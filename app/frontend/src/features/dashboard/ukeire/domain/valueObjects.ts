/**
 * 受入ダッシュボード - Value Objects
 * 日付操作・純粋関数群
 */

import dayjs from "dayjs";
import type { IsoMonth, IsoDate } from "./types";

/** ISO Date文字列からDateオブジェクトを生成 */
export const toDate = (s: string): Date => new Date(s + "T00:00:00");

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
