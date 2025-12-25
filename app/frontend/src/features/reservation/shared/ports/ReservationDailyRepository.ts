/**
 * ReservationDailyRepository - 予約表リポジトリインターフェース
 *
 * Port (インターフェース定義)
 * 規約: Repository抽象、実装詳細に依存しない
 */

export interface ReservationForecastDaily {
  date: string; // YYYY-MM-DD
  reserve_trucks: number;
  reserve_fixed_trucks: number;
  reserve_fixed_ratio: number;
  source: 'manual' | 'customer_agg';
  note?: string;
}

export interface ReservationManualInput {
  reserve_date: string; // YYYY-MM-DD
  total_trucks: number;
  fixed_trucks: number;
  note?: string;
}

export interface ReservationDailyRepository {
  /**
   * 予測用日次予約データを取得
   * @param from 開始日 (YYYY-MM-DD)
   * @param to 終了日 (YYYY-MM-DD)
   */
  getForecastDaily(from: string, to: string): Promise<ReservationForecastDaily[]>;

  /**
   * 手入力データを保存/更新
   */
  upsertManual(payload: ReservationManualInput): Promise<void>;

  /**
   * 手入力データを削除
   * @param date 削除対象日 (YYYY-MM-DD)
   */
  deleteManual(date: string): Promise<void>;
}
