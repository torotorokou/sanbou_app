/**
 * データセットインポート API クライアント
 */

import { coreApi } from '@/shared';
import type { UploadResponseShape } from '../../shared/types/common';

export interface UploadStatusResponse {
  status: 'success' | 'error';
  code: string;
  detail: string;
  result?: {
    id: number;
    csv_type: string;
    file_name: string;
    file_type: string;
    processing_status: 'pending' | 'processing' | 'success' | 'failed';
    uploaded_at: string;
    uploaded_by?: string;
    row_count?: number;
    error_message?: string;
  };
}

export const DatasetImportClient = {
  /**
   * FormDataをPOSTする
   */
  async post(
    path: string,
    body: FormData,
    options?: {
      timeout?: number;
      signal?: AbortSignal;
      onProgress?: (pct?: number) => void;
    }
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

  /**
   * アップロード処理のステータスを照会
   */
  async checkStatus(uploadFileId: number): Promise<UploadStatusResponse> {
    return await coreApi.get<UploadStatusResponse>(
      `/core_api/database/upload/status/${uploadFileId}`
    );
  },
};
