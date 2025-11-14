/**
 * データセットインポート Repository インターフェース
 */

export interface DatasetImportRepository {
  /**
   * ファイルをアップロードする
   * @param filesByType typeKeyをキーとしたFileマップ
   * @param uploadPath アップロード先のエンドポイントパス
   * @param signal AbortSignal for cancellation
   */
  upload(filesByType: Record<string, File>, uploadPath: string, signal?: AbortSignal): Promise<void>;
}
