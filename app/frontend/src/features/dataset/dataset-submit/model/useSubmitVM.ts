/**
 * dataset-submit hooks: useSubmitVM
 * アップロード送信を管理するViewModel
 *
 * 責務:
 * - アップロード状態の管理（isUploading）
 * - Repository経由でアップロードAPI呼び出し
 * - useNotificationStoreで通知表示
 *   - 成功: 5秒autoDismiss
 *   - エラー: sticky（手動クローズのみ）
 */

import { useState, useCallback, useMemo } from 'react';
import { DatasetImportRepositoryImpl } from '../../dataset-import/repository/DatasetImportRepositoryImpl';
import { useNotificationStore } from '@features/notification/domain/services/notificationStore';
import { ApiError } from '@shared';

export interface UploadResult {
  success: boolean;
  uploadFileIds?: Record<string, number>;
}

export function useSubmitVM() {
  const repo = useMemo(() => new DatasetImportRepositoryImpl(), []);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const { success: notifySuccess, error: notifyError } = useNotificationStore();

  const doUpload = useCallback(
    async (filesByType: Record<string, File>, uploadPath: string): Promise<UploadResult> => {
      if (uploading) {
        console.warn('[doUpload] Already uploading. Ignoring.');
        return { success: false };
      }

      if (!Object.keys(filesByType).length) {
        console.warn('[doUpload] No files to upload.');
        return { success: false };
      }

      setUploading(true);
      setUploadSuccess(false);
      console.log('[doUpload] Starting upload...');

      try {
        const response = await repo.upload(filesByType, uploadPath);
        console.log('[doUpload] Upload successful.', response);
        setUploadSuccess(true);

        // upload_file_ids を取得
        let uploadFileIds: Record<string, number> | undefined;
        if (response && typeof response === 'object' && 'result' in response) {
          const result = response.result;
          if (result && typeof result === 'object' && 'upload_file_ids' in result) {
            uploadFileIds = result.upload_file_ids as Record<string, number>;
          }
        }

        // 成功通知を表示（5秒autoDismiss）
        notifySuccess(
          'アップロード受付完了',
          'CSVファイルのアップロードを受け付けました。データ処理中です...',
          5000
        );

        return { success: true, uploadFileIds };
      } catch (error) {
        console.error('[doUpload] Upload error:', error);
        setUploadSuccess(false);

        // エラーの種類に応じて適切な通知を表示（すべてsticky）
        if (error instanceof ApiError) {
          // 409 Conflict（重複エラー）
          if (error.status === 409 && error.code === 'DUPLICATE_FILE') {
            notifyError(
              '重複アップロード',
              '同じファイルが既にアップロード済みです。別のファイルを選択するか、既存データを削除してください。',
              0 // sticky（手動クローズのみ）
            );
          } else {
            // その他のAPIエラー
            notifyError(
              'アップロード失敗',
              error.userMessage || error.message,
              0 // sticky（手動クローズのみ）
            );
          }
        } else if (error instanceof Error) {
          // 一般的なエラー
          if (error.name === 'AbortError') {
            notifyError('キャンセル', 'アップロードがキャンセルされました。', 0);
          } else {
            notifyError('エラー', error.message, 0);
          }
        } else {
          // 不明なエラー
          notifyError(
            '接続エラー',
            'サーバーに接続できませんでした。ネットワークを確認してください。',
            0
          );
        }

        return { success: false };
      } finally {
        setUploading(false);
      }
    },
    [repo, uploading, notifySuccess, notifyError]
  );

  const resetUploadState = useCallback(() => {
    console.log('[resetUploadState] Resetting upload state.');
    setUploadSuccess(false);
    setUploading(false);
  }, []);

  return { uploading, uploadSuccess, doUpload, resetUploadState };
}
