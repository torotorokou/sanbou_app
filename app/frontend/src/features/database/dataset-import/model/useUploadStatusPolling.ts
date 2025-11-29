/**
 * アップロード処理のステータスをポーリングするフック
 * 
 * 責務:
 * - バックグラウンド処理の完了/失敗を監視
 * - 処理完了時に通知を表示
 * - 最大試行回数と間隔を管理
 */

import { useEffect, useRef, useCallback } from 'react';
import { DatasetImportClient } from '../infrastructure/client';
import { notifySuccess, notifyPersistent } from '@features/notification';

export interface UploadStatusPollingOptions {
  /** ポーリング対象の upload_file_ids （csv_type -> upload_file_id） */
  uploadFileIds?: Record<string, number>;
  /** ポーリング間隔（ミリ秒） */
  interval?: number;
  /** 最大試行回数 */
  maxAttempts?: number;
  /** 完了時のコールバック */
  onComplete?: (allSuccess: boolean) => void;
}

const DEFAULT_INTERVAL = 3000; // 3秒
const DEFAULT_MAX_ATTEMPTS = 40; // 最大120秒（3秒 × 40回）
const INITIAL_DELAY = 3000; // 初回チェックまでの遅延（バックグラウンド処理の開始を待つ）

/** ステータスチェック結果 */
type StatusCheckResult = {
  csvType: string;
  fileId: number;
  status?: 'pending' | 'processing' | 'success' | 'failed';
  fileName?: string;
  errorMessage?: string;
  rowCount?: number;
  apiError: boolean;
};

/**
 * アップロードステータスをポーリング
 */
export function useUploadStatusPolling(options: UploadStatusPollingOptions = {}) {
  const {
    uploadFileIds,
    interval = DEFAULT_INTERVAL,
    maxAttempts = DEFAULT_MAX_ATTEMPTS,
    onComplete,
  } = options;

  const attemptCountRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);
  const uploadFileIdsRef = useRef(uploadFileIds);
  const onCompleteRef = useRef(onComplete);

  // refを最新の値で更新
  useEffect(() => {
    uploadFileIdsRef.current = uploadFileIds;
    onCompleteRef.current = onComplete;
  }, [uploadFileIds, onComplete]);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    isPollingRef.current = false;
    attemptCountRef.current = 0;
  }, []);

  const checkStatuses = useCallback(async () => {
    const currentUploadFileIds = uploadFileIdsRef.current;
    if (!currentUploadFileIds || Object.keys(currentUploadFileIds).length === 0) {
      stopPolling();
      return;
    }

    attemptCountRef.current += 1;

    try {
      // 全ファイルのステータスをチェック
      const statusChecks = Object.entries(currentUploadFileIds).map(async ([csvType, fileId]): Promise<StatusCheckResult> => {
        try {
          const response = await DatasetImportClient.checkStatus(fileId);
          return {
            csvType,
            fileId,
            status: response.result?.processing_status,
            fileName: response.result?.file_name,
            errorMessage: response.result?.error_message,
            rowCount: response.result?.row_count,
            apiError: false,
          };
        } catch (error) {
          // ステータス取得エラーは処理中として扱う（リトライ継続）
          console.warn(`[UploadStatusPolling] API error for ${csvType} (${fileId}), will retry:`, error);
          return {
            csvType,
            fileId,
            status: 'processing' as const,
            fileName: csvType,
            errorMessage: undefined,
            rowCount: undefined,
            apiError: true,
          };
        }
      });

      const results = await Promise.all(statusChecks);

      // ステータスを分類（API取得エラーは除外）
      const processing = results.filter(r => 
        (r.status === 'pending' || r.status === 'processing') && !r.apiError
      );
      const apiErrors = results.filter(r => r.apiError);
      const failed = results.filter(r => r.status === 'failed' && !r.apiError);
      const succeeded = results.filter(r => r.status === 'success');

      console.log(`[UploadStatusPolling] Attempt ${attemptCountRef.current}/${maxAttempts}:`, {
        processing: processing.length,
        apiErrors: apiErrors.length,
        failed: failed.length,
        succeeded: succeeded.length,
        details: results.map(r => `${r.csvType}:${r.status}${r.apiError ? '(API_ERR)' : ''}`).join(', '),
      });

      // すべて完了した場合（API取得エラーは無視）
      const stillProcessing = processing.length > 0 || apiErrors.length > 0;
      
      if (!stillProcessing) {
        stopPolling();

        if (failed.length > 0) {
          // 失敗があった場合
          const errorDetails = failed
            .map(f => `【${f.fileName || f.csvType}】${f.errorMessage || '処理エラー'}`)
            .join('\n');

          notifyPersistent(
            'error',
            '処理失敗',
            `以下のファイルの処理に失敗しました:\n${errorDetails}`,
          );

          onCompleteRef.current?.(false);
        } else {
          // すべて成功
          const totalRows = succeeded.reduce((sum, r) => sum + (r.rowCount || 0), 0);
          notifySuccess(
            '処理完了',
            `${succeeded.length}件のCSVファイルの処理が完了しました。${totalRows > 0 ? `（${totalRows.toLocaleString()}行）` : ''}`,
            5000,
          );

          onCompleteRef.current?.(true);
        }

        return;
      }

      // 最大試行回数に達した場合
      if (attemptCountRef.current >= maxAttempts) {
        stopPolling();
        const processingFiles = processing.map(f => f.fileName || f.csvType).join('、');
        
        notifyPersistent(
          'warning',
          '処理タイムアウト',
          `${processingFiles} の処理が時間内に完了しませんでした。履歴画面で確認してください。`,
        );

        onCompleteRef.current?.(false);
        return;
      }

      // 次回のポーリングをスケジュール
      timerRef.current = setTimeout(checkStatuses, interval);
    } catch (error) {
      console.error('[UploadStatusPolling] Unexpected error:', error);
      stopPolling();
      
      notifyPersistent(
        'error',
        'ステータス確認エラー',
        '処理状況の確認中にエラーが発生しました。履歴画面で確認してください。',
      );

      onCompleteRef.current?.(false);
    }
  }, [interval, maxAttempts, stopPolling]);

  // ポーリング開始
  useEffect(() => {
    if (!uploadFileIds || Object.keys(uploadFileIds).length === 0) {
      return;
    }

    if (isPollingRef.current) {
      console.warn('[UploadStatusPolling] Already polling. Ignoring.');
      return;
    }

    console.log('[UploadStatusPolling] Starting polling for:', uploadFileIds);
    console.log(`[UploadStatusPolling] Initial delay: ${INITIAL_DELAY}ms, Interval: ${interval}ms, Max attempts: ${maxAttempts}`);
    isPollingRef.current = true;
    attemptCountRef.current = 0;

    // 最初のチェックは遅延させる（バックグラウンド処理の開始を待つ）
    timerRef.current = setTimeout(checkStatuses, INITIAL_DELAY);

    return () => {
      stopPolling();
    };
  }, [uploadFileIds, interval, maxAttempts, stopPolling, checkStatuses]);

  return { stopPolling };
}
