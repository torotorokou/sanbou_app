/**
 * Ukeire History Repository - HTTP Implementation
 */

import type { UkeireHistoryRepository } from "./UkeireHistoryRepository";
import type { IsoMonth, IsoDate } from "../../model/types";
import { http } from "../../shared/api/client";

export class UkeireHistoryRepositoryImpl implements UkeireHistoryRepository {
  constructor(private readonly baseUrl: string = "/api/ukeire") {}

  async fetchHistoricalData(month: IsoMonth): Promise<{
    prev_month_daily: Record<IsoDate, number>;
    prev_year_daily: Record<IsoDate, number>;
  }> {
    // TODO: 実際のAPIエンドポイントに合わせて調整
    const url = `${this.baseUrl}/history/${month}`;
    const data = await http.get<{
      prev_month_daily: Record<IsoDate, number>;
      prev_year_daily: Record<IsoDate, number>;
    }>(url);
    return data;
  }
}
