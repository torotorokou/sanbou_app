/**
 * ReservationDailyHttpRepository - HTTP実装
 *
 * Infrastructure (外部システムとの通信実装)
 * 規約: Repository抽象の実装、共通HTTPクライアント(coreApi)を使用
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
   * エンドポイント: GET /core_api/reservation/forecast/{year}/{month}
   * from/toから年月を抽出して取得
   */
  async getForecastDaily(from: string): Promise<ReservationForecastDaily[]> {
    // from の年月を抽出（YYYY-MM-DD形式想定）
    // Note: to パラメータは現在未使用（APIが月単位で返却するため）
    const [year, month] = from.split('-');

    return await coreApi.get<ReservationForecastDaily[]>(
      `/core_api/reservation/forecast/${year}/${month}`
    );
  }

  /**
   * 手入力データを保存/更新
   *
   * エンドポイント: POST /core_api/reservation/manual
   */
  async upsertManual(payload: ReservationManualInput): Promise<void> {
    await coreApi.post('/core_api/reservation/manual', payload);
  }

  /**
   * 手入力データを削除
   *
   * エンドポイント: DELETE /core_api/reservation/manual/{date}
   */
  async deleteManual(date: string): Promise<void> {
    await coreApi.delete(`/core_api/reservation/manual/${date}`);
  }
}

// シングルトンインスタンス
export const reservationDailyRepository = new ReservationDailyHttpRepository();
