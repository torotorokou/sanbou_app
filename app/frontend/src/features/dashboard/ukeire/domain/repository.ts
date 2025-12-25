/**
 * 受入ダッシュボード - Repository Interface
 * データ取得層の抽象
 */

import type { IsoMonth, MonthPayloadDTO } from './types';

type MonthISO = string; // "YYYY-MM"

interface CalendarPayload {
  month: MonthISO;
  days: Array<{
    date: string;
    status?: string;
    label?: string | null;
    color?: string | null;
  }>;
  legend?: Array<{
    key: string;
    label: string;
    color?: string | null;
  }>;
}

export interface IInboundForecastRepository {
  /**
   * 指定月の受入予測データを取得
   * @param month YYYY-MM形式の月
   */
  fetchMonthPayload(month: IsoMonth): Promise<MonthPayloadDTO>;
}

/**
 * 営業カレンダー Repository Interface（SQL起点・API駆動）
 */
export interface ICalendarRepository {
  /**
   * 指定月の営業カレンダーデータを取得
   * @param month YYYY-MM形式の月
   */
  fetchMonthCalendar(month: MonthISO): Promise<CalendarPayload>;
}
