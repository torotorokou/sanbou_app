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
  status: 'success' | 'error';
  items: Array<{
    id: string;
    date: string; // 'YYYY-MM-DD'
    kind: string;
    file_name: string;
    is_deleted: boolean;
  }>;
}

interface DeleteResponse {
  status: 'success' | 'error';
  message?: string;
}

/**
 * アップロードカレンダー Repository 実装
 */
export class UploadCalendarRepositoryImpl implements UploadCalendarRepository {
  // デバッグ用：モックモードを有効化（バックエンドAPI未実装時）
  private useMockData = true;

  async fetchMonthly(params: { year: number; month: number }): Promise<UploadCalendarItem[]> {
    // モックモード：ダミーデータを返す
    if (this.useMockData) {
      return this.generateMockData(params.year, params.month);
    }

    // TODO: バックエンドAPIのパスは実装に合わせて調整
    // 想定パス: GET /core_api/database/upload-calendar?year=2025&month=11
    const response = await coreApi.get<MonthlyResponse>(
      `/core_api/database/upload-calendar?year=${params.year}&month=${params.month}`
    );

    // バックエンドのスネークケースをキャメルケースに変換
    return response.items.map(item => ({
      id: item.id,
      date: item.date,
      kind: item.kind as CsvUploadKind, // TODO: バックエンドから正しい kind が返されることを前提
      fileName: item.file_name,
      deleted: item.is_deleted,
    }));
  }

  /**
   * モックデータ生成（開発・デバッグ用）
   */
  private generateMockData(year: number, month: number): UploadCalendarItem[] {
    const mockData: UploadCalendarItem[] = [
      // 11月1日
      { id: '1', date: `${year}-${String(month).padStart(2, '0')}-01`, kind: 'shogun_flash_receive', fileName: '将軍速報_受入_20251101.csv', deleted: false },
      { id: '2', date: `${year}-${String(month).padStart(2, '0')}-01`, kind: 'shogun_flash_shipment', fileName: '将軍速報_出荷_20251101.csv', deleted: false },
      
      // 11月5日
      { id: '3', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_receive', fileName: '将軍最終_受入_20251105.csv', deleted: false },
      { id: '4', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_shipment', fileName: '将軍最終_出荷_20251105.csv', deleted: false },
      { id: '5', date: `${year}-${String(month).padStart(2, '0')}-05`, kind: 'shogun_final_yard', fileName: '将軍最終_ヤード_20251105.csv', deleted: false },
      
      // 11月10日
      { id: '6', date: `${year}-${String(month).padStart(2, '0')}-10`, kind: 'manifest_stage1', fileName: 'マニフェスト_1次_20251110.csv', deleted: false },
      { id: '7', date: `${year}-${String(month).padStart(2, '0')}-10`, kind: 'manifest_stage2', fileName: 'マニフェスト_2次_20251110.csv', deleted: false },
      
      // 11月15日
      { id: '8', date: `${year}-${String(month).padStart(2, '0')}-15`, kind: 'shogun_flash_receive', fileName: '将軍速報_受入_20251115.csv', deleted: false },
      { id: '9', date: `${year}-${String(month).padStart(2, '0')}-15`, kind: 'shogun_flash_yard', fileName: '将軍速報_ヤード_20251115.csv', deleted: false },
      
      // 11月18日（今日の想定）
      { id: '10', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_flash_receive', fileName: '将軍速報_受入_20251118.csv', deleted: false },
      { id: '11', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_flash_shipment', fileName: '将軍速報_出荷_20251118.csv', deleted: false },
      { id: '12', date: `${year}-${String(month).padStart(2, '0')}-18`, kind: 'shogun_final_receive', fileName: '将軍最終_受入_20251118.csv', deleted: false },
      
      // 11月20日
      { id: '13', date: `${year}-${String(month).padStart(2, '0')}-20`, kind: 'manifest_stage1', fileName: 'マニフェスト_1次_20251120.csv', deleted: false },
    ];
    
    return mockData;
  }

  async deleteUpload(id: string): Promise<void> {
    // モックモード：即座に成功を返す
    if (this.useMockData) {
      console.log(`[Mock] Deleted upload: ${id}`);
      return Promise.resolve();
    }

    // TODO: バックエンドAPIのパスは実装に合わせて調整
    // 想定パス: DELETE /core_api/database/upload-calendar/{id}
    // または PATCH /core_api/database/upload-calendar/{id} with { is_deleted: true }
    await coreApi.delete<DeleteResponse>(`/core_api/database/upload-calendar/${id}`);
  }
}

/**
 * Repository のシングルトンインスタンス
 */
export const uploadCalendarRepository = new UploadCalendarRepositoryImpl();
