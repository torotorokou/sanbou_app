/**
 * アップロードカレンダー Repository
 * データの取得と削除を担当
 */

import { coreApi } from "@shared";
import type { UploadCalendarItem, CsvUploadKind } from "../model/types";
import { logger } from "@/shared";

/**
 * アップロードカレンダー Repository インターフェース
 */
export interface UploadCalendarRepository {
  /**
   * 指定月のアップロード一覧を取得
   */
  fetchMonthly(params: {
    year: number;
    month: number;
  }): Promise<UploadCalendarItem[]>;

  /**
   * アップロードを削除（論理削除）
   * stgテーブルの該当日付・種別のデータをis_deleted=trueに更新
   */
  deleteUpload(params: {
    uploadFileId: number;
    date: string; // 'YYYY-MM-DD'
    csvKind: CsvUploadKind;
  }): Promise<void>;
}

/**
 * バックエンドからのレスポンス型
 */
interface MonthlyResponse {
  items: Array<{
    uploadFileId: number; // log.upload_file.id
    date: string; // 'YYYY-MM-DD'
    csvKind: string; // CSV種別（キャメルケース）
    rowCount: number; // 行数
  }>;
}

interface DeleteResponse {
  status: string;
  uploadFileId: number;
  date: string;
  csvKind: string;
  affectedRows: number;
}

/**
 * アップロードカレンダー Repository 実装
 */
export class UploadCalendarRepositoryImpl implements UploadCalendarRepository {
  // モックモードを無効化（バックエンドAPIが実装済み）
  private useMockData = false;

  async fetchMonthly(params: {
    year: number;
    month: number;
  }): Promise<UploadCalendarItem[]> {
    // モックモード：ダミーデータを返す
    if (this.useMockData) {
      return this.generateMockData(params.year, params.month);
    }

    // バックエンドAPIからデータ取得
    const response = await coreApi.get<MonthlyResponse>(
      `/core_api/database/upload-calendar`,
      {
        params: {
          year: params.year,
          month: params.month,
        },
      },
    );

    // バックエンドのレスポンスをフロントエンド用の型に変換
    return response.items.map((item) => ({
      id: `${item.uploadFileId}`, // upload_file_id を文字列IDとして使用
      uploadFileId: item.uploadFileId,
      date: item.date,
      kind: item.csvKind as CsvUploadKind,
      rowCount: item.rowCount, // データ数
      deleted: false, // バックエンドは is_deleted=false のみを返す
    }));
  }

  /**
   * モックデータ生成（開発・デバッグ用）
   */
  private generateMockData(year: number, month: number): UploadCalendarItem[] {
    const mockData: UploadCalendarItem[] = [
      // 11月1日
      {
        id: "1",
        date: `${year}-${String(month).padStart(2, "0")}-01`,
        kind: "shogun_flash_receive",
        rowCount: 1234,
        deleted: false,
      },
      {
        id: "2",
        date: `${year}-${String(month).padStart(2, "0")}-01`,
        kind: "shogun_flash_shipment",
        rowCount: 567,
        deleted: false,
      },

      // 11月5日
      {
        id: "3",
        date: `${year}-${String(month).padStart(2, "0")}-05`,
        kind: "shogun_final_receive",
        rowCount: 2100,
        deleted: false,
      },
      {
        id: "4",
        date: `${year}-${String(month).padStart(2, "0")}-05`,
        kind: "shogun_final_shipment",
        rowCount: 890,
        deleted: false,
      },
      {
        id: "5",
        date: `${year}-${String(month).padStart(2, "0")}-05`,
        kind: "shogun_final_yard",
        rowCount: 456,
        deleted: false,
      },

      // 11月10日
      {
        id: "6",
        date: `${year}-${String(month).padStart(2, "0")}-10`,
        kind: "manifest_stage1",
        rowCount: 3200,
        deleted: false,
      },
      {
        id: "7",
        date: `${year}-${String(month).padStart(2, "0")}-10`,
        kind: "manifest_stage2",
        rowCount: 1800,
        deleted: false,
      },

      // 11月15日
      {
        id: "8",
        date: `${year}-${String(month).padStart(2, "0")}-15`,
        kind: "shogun_flash_receive",
        rowCount: 1500,
        deleted: false,
      },
      {
        id: "9",
        date: `${year}-${String(month).padStart(2, "0")}-15`,
        kind: "shogun_flash_yard",
        rowCount: 720,
        deleted: false,
      },

      // 11月18日（今日の想定）
      {
        id: "10",
        date: `${year}-${String(month).padStart(2, "0")}-18`,
        kind: "shogun_flash_receive",
        rowCount: 980,
        deleted: false,
      },
      {
        id: "11",
        date: `${year}-${String(month).padStart(2, "0")}-18`,
        kind: "shogun_flash_shipment",
        rowCount: 640,
        deleted: false,
      },
      {
        id: "12",
        date: `${year}-${String(month).padStart(2, "0")}-18`,
        kind: "shogun_final_receive",
        rowCount: 2400,
        deleted: false,
      },

      // 11月20日
      {
        id: "13",
        date: `${year}-${String(month).padStart(2, "0")}-20`,
        kind: "manifest_stage1",
        rowCount: 3500,
        deleted: false,
      },
    ];

    return mockData;
  }

  async deleteUpload(params: {
    uploadFileId: number;
    date: string;
    csvKind: CsvUploadKind;
  }): Promise<void> {
    // モックモード：即座に成功を返す
    if (this.useMockData) {
      logger.log(
        `[Mock] Deleted upload: uploadFileId=${params.uploadFileId}, date=${params.date}, kind=${params.csvKind}`,
      );
      return Promise.resolve();
    }

    // バックエンドのDELETEエンドポイントを呼び出し
    // 新しいAPI仕様: クエリパラメータでdate, csvKindを送信
    const response = await coreApi.delete<DeleteResponse>(
      `/core_api/database/upload-calendar/${params.uploadFileId}`,
      {
        params: {
          date: params.date,
          csvKind: params.csvKind,
        },
      },
    );

    logger.log(
      `Deleted stg data: uploadFileId=${params.uploadFileId}, date=${params.date}, kind=${params.csvKind}, affectedRows=${response.affectedRows}`,
    );
  }
}

/**
 * Repository のシングルトンインスタンス
 */
export const uploadCalendarRepository = new UploadCalendarRepositoryImpl();
