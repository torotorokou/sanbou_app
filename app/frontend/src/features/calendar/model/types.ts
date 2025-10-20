export type DayType = 'NORMAL' | 'RESERVATION' | 'CLOSED';

export interface CalendarDayDTO {
  ddate: string;
  y: number;
  m: number;
  iso_year: number;
  iso_week: number;
  iso_dow: number; // ISO: Mon=1..Sun=7
  is_holiday: boolean;
  is_second_sunday: boolean;
  is_company_closed: boolean;
  day_type: DayType;
  is_business: boolean;
}

export interface MonthCalendarDTO {
  month: string;         // 'YYYY-MM'
  days: CalendarDayDTO[];
}

/**
 * CalendarCore 用の描画セル型（汎用）
 */
export interface CalendarCell {
  date: string; // ISO "YYYY-MM-DD"
  inMonth: boolean;
  /**
   * 任意の描画プロパティをここに追加可能
   * 各ドメイン（受入量など）はこの型を extends して利用
   */
  [key: string]: unknown;
}
