/**
 * 受入ダッシュボード - HTTP Repository
 * 実API経由のRepository実装（未実装）
 */

import type { IInboundForecastRepository } from "../../domain/repository";
import type { IsoMonth, MonthPayloadDTO } from "../../domain/types";

export class HttpInboundForecastRepository implements IInboundForecastRepository {
  constructor(private readonly baseUrl: string) {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async fetchMonthPayload(_month: IsoMonth): Promise<MonthPayloadDTO> {
    // TODO: 実装
    // const response = await fetch(`${this.baseUrl}/api/inbound-forecast/${month}`);
    // return await response.json();
    throw new Error("HttpInboundForecastRepository is not implemented yet.");
  }
}
