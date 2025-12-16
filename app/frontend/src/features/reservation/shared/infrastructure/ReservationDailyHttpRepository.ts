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
   * エンドポイント: GET /reservation/forecast/{year}/{month}
   * from/toから年月を抽出して取得
   */
  async getForecastDaily(from: string, to: string): Promise<ReservationForecastDaily[]> {
    // from の年月を抽出（YYYY-MM-DD形式想定）
    const [year, month] = from.split('-');
    
    return await coreApi.get<ReservationForecastDaily[]>(
      `/reservation/forecast/${year}/${month}`
    );
  }

  /**
   * 手入力データを保存/更新
   * 
   * エンドポイント: POST /reservation/manual
   */
  async upsertManual(payload: ReservationManualInput): Promise<void> {
    await coreApi.post('/reservation/manual', payload);
  }

  /**
   * 手入力データを削除
   * 
   * エンドポイント: DELETE /reservation/manual/{date}
   */
  async deleteManual(date: string): Promise<void> {
    await coreApi.delete(`/reservation/manual/${date}`);
  }
}

// シングルトンインスタンス
export const reservationDailyRepository = new ReservationDailyHttpRepository();
