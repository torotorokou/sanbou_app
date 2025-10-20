/**
 * Ukeire Forecast Repository - HTTP Implementation
 * API経由でデータを取得し、Domain型に変換
 */

import type { UkeireForecastRepository } from "./UkeireForecastRepository";
import type { IsoMonth, MonthPayloadDTO } from "../../model/types";
import { http } from "../../shared/api/client";

export class UkeireForecastRepositoryImpl implements UkeireForecastRepository {
  constructor(private readonly baseUrl: string = "/api/ukeire") {}

  async fetchMonthPayload(month: IsoMonth): Promise<MonthPayloadDTO> {
    // TODO: 実際のAPIエンドポイントに合わせて調整
    const url = `${this.baseUrl}/forecast/${month}`;
    const data = await http.get<MonthPayloadDTO>(url);
    
    // DTO変換が必要な場合はここで実施
    // 現状はAPIレスポンスがMonthPayloadDTO形式と仮定
    return data;
  }
}
