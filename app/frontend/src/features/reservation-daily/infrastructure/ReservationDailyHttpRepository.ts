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

// 既存のAPIクライアントを参照
import { apiClient } from '@/shared/api/client';

export class ReservationDailyHttpRepository implements ReservationDailyRepository {
  /**
   * 予測用日次予約データを取得
   * 
   * 仮エンドポイント: GET /api/reservations/forecast-daily?from=...&to=...
   * ※ バックエンド実装後に調整
   */
  async getForecastDaily(from: string, to: string): Promise<ReservationForecastDaily[]> {
    const response = await apiClient.get<ReservationForecastDaily[]>(
      '/reservations/forecast-daily',
      {
        params: { from, to },
      }
    );
    return response.data;
  }

  /**
   * 手入力データを保存/更新
   * 
   * 仮エンドポイント: POST /api/reservations/daily-manual
   * ※ バックエンド実装後に調整
   */
  async upsertManual(payload: ReservationManualInput): Promise<void> {
    await apiClient.post('/reservations/daily-manual', payload);
  }

  /**
   * 手入力データを削除
   * 
   * 仮エンドポイント: DELETE /api/reservations/daily-manual?date=...
   * ※ バックエンド実装後に調整
   */
  async deleteManual(date: string): Promise<void> {
    await apiClient.delete('/reservations/daily-manual', {
      params: { date },
    });
  }
}

// シングルトンインスタンス
export const reservationDailyRepository = new ReservationDailyHttpRepository();
