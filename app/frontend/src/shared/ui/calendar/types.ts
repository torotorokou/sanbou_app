/**
 * Calendar API Types
 * APIコントラクトに準拠した型定義（SQL起点のカレンダーデータ）
 */

export type DateISO = string; // "YYYY-MM-DD"
export type MonthISO = string; // "YYYY-MM"
export type StatusCode = "business" | "holiday" | "closed" | string;

/**
 * 1日の装飾情報（API レスポンス）
 */
export type DayDecor = {
  date: DateISO;
  status: StatusCode;
  label?: string | null;
  color?: string | null; // APIが色を固定したい場合
};

/**
 * 凡例アイテム
 */
export type LegendItem = {
  key: StatusCode;
  label: string;
  color?: string | null;
};

/**
 * Calendar API レスポンス全体
 */
export type CalendarPayload = {
  month: MonthISO;
  days: DayDecor[];
  legend?: LegendItem[];
  version?: number;
};
