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
