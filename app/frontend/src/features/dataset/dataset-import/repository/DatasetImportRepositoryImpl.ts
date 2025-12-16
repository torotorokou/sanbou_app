/**
 * データセットインポート Repository 実装
 * 
 * 責務:
 * - HTTPリクエストの送信とレスポンス処理
 * - エラーはrethrowして呼び出し元で処理
 * - 通知は呼び出し元（useSubmitVM）で一元管理
 */

import type { DatasetImportRepository } from './DatasetImportRepository';
import { DatasetImportClient } from '../infrastructure/client';
import { buildFormData } from '../../shared/upload/buildFormData';
import { DEFAULT_UPLOAD_TIMEOUT } from '../../shared/types/constants';
import type { UploadResponseShape } from '../../shared/types/common';

export class DatasetImportRepositoryImpl implements DatasetImportRepository {
  async upload(filesByType: Record<string, File>, uploadPath: string, signal?: AbortSignal): Promise<UploadResponseShape> {
    const form = buildFormData(filesByType);

    const result: UploadResponseShape = await DatasetImportClient.post(
      uploadPath,
      form,
      { timeout: DEFAULT_UPLOAD_TIMEOUT, signal }
    );

    // レスポンスのバリデーション
    if (result.status !== 'success') {
      const error = new Error(result?.detail ?? 'アップロード中にエラーが発生しました。');
      error.name = 'UploadResponseError';
      throw error;
    }

    // 成功時はレスポンスを返す（upload_file_idsを含む可能性がある）
    return result;
  }
}
