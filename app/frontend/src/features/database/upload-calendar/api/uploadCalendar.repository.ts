/**
 * アップロードカレンダー Repository
 * データの取得と削除を担当
 */

import { coreApi } from '@shared';
import type { UploadCalendarItem, CsvUploadKind } from '../model/types';

/**
 * アップロードカレンダー Repository インターフェース
 */
export interface UploadCalendarRepository {
  /**
   * 指定月のアップロード一覧を取得
   */
  fetchMonthly(params: { year: number; month: number }): Promise<UploadCalendarItem[]>;

  /**
   * アップロードを削除（論理削除）
   */
  deleteUpload(id: string): Promise<void>;
}

/**
 * バックエンドからのレスポンス型
 */
interface MonthlyResponse {
  items: Array<{
    date: string;      // 'YYYY-MM-DD'
    csvKind: string;   // CSV種別（キャメルケース）
    rowCount: number;  // 行数
  }>;
}

interface DeleteResponse {
  status: string;
  uploadFileId: number;
}

/**
 * アップロードカレンダー Repository 実装
 */
export class UploadCalendarRepositoryImpl implements UploadCalendarRepository {
  // モックモードを無効化（バックエンドAPIが実装済み）
  private useMockData = false;

  async fetchMonthly(params: { year: number; month: number }): Promise<UploadCalendarItem[]> {
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
        }
      }
    );

    // バックエンドのレスポンスをフロントエンド用の型に変換
    // 注意: バックエンドは集計データ（date + csvKind + rowCount）を返すため、
    // フロントエンドのUploadCalendarItem形式に変換する
    return response.items.map((item) => ({
      id: `${item.date}-${item.csvKind}`, // 一意なIDを生成
      date: item.date,
      kind: item.csvKind as CsvUploadKind,
      rowCount: item.rowCount, // データ数
      deleted: false, // バックエンドのビューは is_deleted=false のみを返す
    }));
  }

  /**
   * モックデータ生成（開発・デバッグ用）
   */
  private generateMockData(year: number, month: number): UploadCalendarItem[] {
    const mockData: UploadCalendarItem[] = [
      // 11月1日
      { id: '1', date: `${year}-${String(month).padStart(2, '0')}-01`, kind: 'shogun_flash_receive', rowCount: 1234, deleted: false },
      { id: '2', date: `${year}-${String(month).padStart(2, '0')}-01`, kind: 'shogun_flash_shipment', rowCount: 567, deleted: false },
      
      // 11月5日
      { id: '3', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_receive', rowCount: 2100, deleted: false },
      { id: '4', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_shipment', rowCount: 890, deleted: false },
      { id: '5', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_yard', rowCount: 456, deleted: false },
      
      // 11月10日
      { id: '6', date: `${year}-${String(month).padStart(2, '0')}-10`, kind: 'manifest_stage1', rowCount: 3200, deleted: false },
      { id: '7', date: `${year}-${String(month).padStart(2, '0')}-10`, kind: 'manifest_stage2', rowCount: 1800, deleted: false },
      
      // 11月15日
      { id: '8', date: `${year}-${String(month).padStart(2, '0')}-15`, kind: 'shogun_flash_receive', rowCount: 1500, deleted: false },
      { id: '9', date: `${year}-${String(month).padStart(2, '0')}-15`, kind: 'shogun_flash_yard', rowCount: 720, deleted: false },
      
      // 11月18日（今日の想定）
      { id: '10', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_flash_receive', rowCount: 980, deleted: false },
      { id: '11', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_flash_shipment', rowCount: 640, deleted: false },
      { id: '12', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_final_receive', rowCount: 2400, deleted: false },
      
      // 11月20日
      { id: '13', date: `${year}-${String(month).padStart(2, '0')}-20`, kind: 'manifest_stage1', rowCount: 3500, deleted: false },
    ];
    
    return mockData;
  }

  async deleteUpload(id: string): Promise<void> {
    // モックモード：即座に成功を返す
    if (this.useMockData) {
      console.log(`[Mock] Deleted upload: ${id}`);
      return Promise.resolve();
    }

    // id は "date-csvKind" 形式なので upload_file_id に変換する必要がある
    // 実装の簡略化のため、ここでは削除APIを呼び出すが、
    // 実際には upload_file_id を別途取得する必要がある
    // TODO: フロントエンドのデータ構造を見直して upload_file_id を保持するようにする
    
    // 暫定実装: id から upload_file_id を抽出できないため、
    // この機能は後続の実装で対応する
    console.warn('Delete functionality requires upload_file_id. Current id format:', id);
    throw new Error('削除機能は現在準備中です。upload_file_id が必要です。');
    
    // 本来の実装（upload_file_id が分かる場合）:
    // await coreApi.delete<DeleteResponse>(`/database/upload-calendar/${uploadFileId}`);
  }
}

/**
 * Repository のシングルトンインスタンス
 */
export const uploadCalendarRepository = new UploadCalendarRepositoryImpl();
