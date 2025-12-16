/**
 * ReservationDailyHttpRepository - HTTP実装
 * 
 * Infrastructure (外部システムとの通信実装)
 */

import type {
  ReservationDailyRepository,
  ReservationForecastDaily,
  ReservationManualInput,
} from '../ports/ReservationDailyRepository';

// 既存のAPIクライアントを参照（coreApi統一クライアント）
import { coreApi } from '@/shared';

export class ReservationDailyHttpRepository implements ReservationDailyRepository {
  /**
   * 予測用日次予約データを取得
   * 
   * 仮エンドポイント: GET /core_api/reservations/forecast-daily?from=...&to=...
   * ※ バックエンド実装後に調整
   */
  async getForecastDaily(from: string, to: string): Promise<ReservationForecastDaily[]> {
    return await coreApi.get<ReservationForecastDaily[]>(
      '/core_api/reservations/forecast-daily',
      {
        params: { from, to },
      }
    );
  }

  /**
   * 手入力データを保存/更新
   * 
   * 仮エンドポイント: POST /core_api/reservations/daily-manual
   * ※ バックエンド実装後に調整
   */
  async upsertManual(payload: ReservationManualInput): Promise<void> {
    await coreApi.post('/core_api/reservations/daily-manual', payload);
  }

  /**
   * 手入力データを削除
   * 
   * 仮エンドポイント: DELETE /core_api/reservations/daily-manual?date=...
   * ※ バックエンド実装後に調整
   */
  async deleteManual(date: string): Promise<void> {
    await coreApi.delete('/core_api/reservations/daily-manual', {
      params: { date },
    });
  }
}

// シングルトンインスタンス
export const reservationDailyRepository = new ReservationDailyHttpRepository();
