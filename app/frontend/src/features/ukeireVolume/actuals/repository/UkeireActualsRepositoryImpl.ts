/**
 * Ukeire Actuals Repository - HTTP Implementation
 */

import type { UkeireActualsRepository } from "./UkeireActualsRepository";
import type { IsoMonth, DailyCurveDTO, CalendarDay } from "../../model/types";
import { http } from "../../shared/api/client";

export class UkeireActualsRepositoryImpl implements UkeireActualsRepository {
  constructor(private readonly baseUrl: string = "/api/ukeire") {}

  async fetchDailyActuals(month: IsoMonth): Promise<{
    days: DailyCurveDTO[];
    calendar: CalendarDay[];
  }> {
    // TODO: 実際のAPIエンドポイントに合わせて調整
    const url = `${this.baseUrl}/actuals/${month}`;
    const data = await http.get<{ days: DailyCurveDTO[]; calendar: CalendarDay[] }>(url);
    return data;
  }
}
