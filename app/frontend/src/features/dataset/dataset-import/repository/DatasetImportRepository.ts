/**
 * データセットインポート Repository インターフェース
 */

import type { UploadResponseShape } from '../../shared/types/common';

export interface DatasetImportRepository {
  /**
   * ファイルをアップロードする
   * @param filesByType typeKeyをキーとしたFileマップ
   * @param uploadPath アップロード先のエンドポイントパス
   * @param signal AbortSignal for cancellation
   * @returns アップロードレスポンス（upload_file_idsを含む可能性がある）
   */
  upload(filesByType: Record<string, File>, uploadPath: string, signal?: AbortSignal): Promise<UploadResponseShape>;
}
