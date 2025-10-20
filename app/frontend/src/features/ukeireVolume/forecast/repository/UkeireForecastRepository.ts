/**
 * Ukeire Forecast Repository Interface
 */

import type { IsoMonth, MonthPayloadDTO } from "../../model/types";

export interface UkeireForecastRepository {
  /**
   * 指定月の受入予測データを取得
   * @param month YYYY-MM形式の月
   */
  fetchMonthPayload(month: IsoMonth): Promise<MonthPayloadDTO>;
}
