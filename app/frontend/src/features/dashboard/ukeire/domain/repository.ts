/**
 * 受入ダッシュボード - Repository Interface
 * データ取得層の抽象
 */

import type { IsoMonth, MonthPayloadDTO } from "./types";
import type { MonthISO, CalendarPayload } from "@/shared/ui/calendar/types";

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
