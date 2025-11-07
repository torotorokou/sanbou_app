/**
 * データセットインポート Repository インターフェース
 */

export interface DatasetImportRepository {
  /**
   * ファイルをアップロードする
   * @param filesByType typeKeyをキーとしたFileマップ
   * @param signal AbortSignal for cancellation
   */
  upload(filesByType: Record<string, File>, signal?: AbortSignal): Promise<void>;
}
