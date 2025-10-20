/**
 * Ukeire History Repository Interface
 * 過去データ比較用のRepository抽象
 */

import type { IsoMonth, IsoDate } from "../../model/types";

export interface UkeireHistoryRepository {
  /**
   * 前月・前年の日次データを取得
   */
  fetchHistoricalData(month: IsoMonth): Promise<{
    prev_month_daily: Record<IsoDate, number>;
    prev_year_daily: Record<IsoDate, number>;
  }>;
}
