/**
 * データセットインポート API クライアント
 */

import { coreApi } from '@/shared';
import type { UploadResponseShape } from '../../shared/types/common';

export const DatasetImportClient = {
  /**
   * FormDataをPOSTする
   */
  async post(
    path: string,
    body: FormData,
    options?: { timeout?: number; signal?: AbortSignal; onProgress?: (pct?: number) => void }
  ): Promise<UploadResponseShape> {
    try {
      // coreApiのuploadFormメソッドを使用
      return await coreApi.uploadForm<UploadResponseShape>(path, body, {
        timeout: options?.timeout,
        signal: options?.signal,
        onProgress: options?.onProgress,
      });
    } catch (error) {
      throw error;
    }
  },
};
