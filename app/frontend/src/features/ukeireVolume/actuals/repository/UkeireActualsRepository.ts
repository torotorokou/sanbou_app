/**
 * Ukeire Actuals Repository Interface
 * 実績データ取得用のRepository抽象
 */

import type { IsoMonth, DailyCurveDTO, CalendarDay } from "../../model/types";

export interface UkeireActualsRepository {
  /**
   * 指定月の日次実績データを取得
   */
  fetchDailyActuals(month: IsoMonth): Promise<{
    days: DailyCurveDTO[];
    calendar: CalendarDay[];
  }>;
}
