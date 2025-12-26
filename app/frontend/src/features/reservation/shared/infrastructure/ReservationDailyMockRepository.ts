/**
 * ReservationDailyMockRepository - モック実装（開発用）
 *
 * Infrastructure (モックデータ実装)
 * 規約: バックエンドAPI未実装時の開発用モック
 *
 * TODO: バックエンドAPI実装後、ReservationDailyHttpRepositoryに切り替え
 */

import { logger } from "@/shared";
import type {
  ReservationDailyRepository,
  ReservationForecastDaily,
  ReservationManualInput,
} from "../ports/ReservationDailyRepository";

export class ReservationDailyMockRepository implements ReservationDailyRepository {
  // モックストレージ（メモリ内）
  private manualData: Map<string, ReservationManualInput> = new Map();

  /**
   * 予測用日次予約データを取得（モック）
   */
  async getForecastDaily(
    from: string,
    to: string,
  ): Promise<ReservationForecastDaily[]> {
    logger.log("[MOCK] getForecastDaily:", { from, to });

    // モックデータを生成
    const result: ReservationForecastDaily[] = [];
    const startDate = new Date(from);
    const endDate = new Date(to);

    for (
      let d = new Date(startDate);
      d <= endDate;
      d.setDate(d.getDate() + 1)
    ) {
      const dateStr = d.toISOString().split("T")[0];

      // 手入力データがあればそれを優先
      const manual = this.manualData.get(dateStr);
      if (manual) {
        result.push({
          date: dateStr,
          reserve_trucks: manual.total_trucks,
          reserve_fixed_trucks: manual.fixed_trucks,
          reserve_fixed_ratio: manual.fixed_trucks / manual.total_trucks,
          source: "manual",
        });
      } else {
        // ランダムな集計データ（開発用）
        const totalTrucks = Math.floor(Math.random() * 10) + 5;
        const fixedTrucks = Math.floor(Math.random() * totalTrucks);
        result.push({
          date: dateStr,
          reserve_trucks: totalTrucks,
          reserve_fixed_trucks: fixedTrucks,
          reserve_fixed_ratio: totalTrucks > 0 ? fixedTrucks / totalTrucks : 0,
          source: "customer_agg",
        });
      }
    }

    // 実際のAPIのように少し遅延させる
    await new Promise((resolve) => setTimeout(resolve, 300));

    return result;
  }

  /**
   * 手入力データを保存/更新（モック）
   */
  async upsertManual(payload: ReservationManualInput): Promise<void> {
    logger.log("[MOCK] upsertManual:", payload);

    this.manualData.set(payload.reserve_date, payload);

    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  /**
   * 手入力データを削除（モック）
   */
  async deleteManual(date: string): Promise<void> {
    logger.log("[MOCK] deleteManual:", date);

    this.manualData.delete(date);

    await new Promise((resolve) => setTimeout(resolve, 200));
  }
}

// シングルトンインスタンス
export const reservationDailyMockRepository =
  new ReservationDailyMockRepository();
