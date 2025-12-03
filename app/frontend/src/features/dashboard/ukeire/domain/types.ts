/**
 * 受入ダッシュボード - Domain Types
 * DTO型定義（API/Repository層のコントラクト）
 * 
 * @deprecated IsoMonth, IsoDate型は @shared から使用してください
 */

import type { IsoMonth, IsoDate } from "@shared";

/**
 * @deprecated 代わりに @shared/utils/dateUtils の IsoMonth を使用してください
 */
export type { IsoMonth };

/**
 * @deprecated 代わりに @shared/utils/dateUtils の IsoDate を使用してください
 */
export type { IsoDate };

export type CalendarDay = {
  date: IsoDate;
  is_business_day: 0 | 1;
  is_holiday: 0 | 1;
  week_id: IsoDate; // 週の月曜
};

export type HeaderDTO = {
  month: IsoMonth;
  business_days: {
    total: number;
    mon_sat: number;
    sun_holiday: number;
    non_business: number;
  };
  rules: { week_def: string; week_to_month: string; alignment: string };
};

export type TargetsDTO = {
  month: number;
  weeks: { bw_idx: number; week_target: number }[];
  day_weights: { weekday: number; sat: number; sun_hol: number };
};

export type ProgressDTO = {
  mtd_actual: number;
  remaining_business_days: number;
};

export type ForecastDTO = {
  today: { p50: number; p10: number; p90: number };
  week: { p50: number; p10: number; p90: number; target: number };
  month_landing: { p50: number; p10: number; p90: number };
};

export type DailyCurveDTO = {
  date: IsoDate;
  from_7wk: number;
  from_month_share: number;
  bookings: number;
  actual?: number;
};

export type WeekRowDTO = {
  week_id: IsoDate;
  week_start: IsoDate;
  week_end: IsoDate;
  business_week_index_in_month: number;
  ton_in_month: number;
  in_month_business_days: number;
  portion_in_month: number;
  targets: { week: number };
  comparisons: {
    vs_prev_week: { delta_ton: number | null; delta_pct: number | null; align_note: string };
    vs_prev_month_same_idx: { delta_ton: number | null; delta_pct: number | null; align_note: string };
    vs_prev_year_same_idx: { delta_ton: number | null; delta_pct: number | null; align_note: string };
  };
};

export type HistoryDTO = {
  m_vs_prev_month: { delta_ton: number; delta_pct: number; align_note: string };
  m_vs_prev_year: { delta_ton: number; delta_pct: number };
  m_vs_3yr_avg: { delta_ton: number; delta_pct: number };
};

export type MonthPayloadDTO = {
  header: HeaderDTO;
  targets: TargetsDTO;
  calendar: { days: CalendarDay[] };
  progress: ProgressDTO;
  forecast: ForecastDTO;
  daily_curve: DailyCurveDTO[];
  weeks: WeekRowDTO[];
  history: HistoryDTO;
  prev_month_daily?: Record<IsoDate, number>;
  prev_year_daily?: Record<IsoDate, number>;
};
