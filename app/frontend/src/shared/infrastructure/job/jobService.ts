/**
 * ジョブポーリングサービス（サンプル実装）
 * 
 * 目的:
 * - 非同期ジョブの状態をポーリング
 * - 失敗時に notifyApiError で通知
 */

import { notifyApiError, notifySuccess } from '@features/notification';
import { apiGet } from '@shared/infrastructure/http';
import type { ProblemDetails } from '@features/notification/domain/types/contract';

/**
 * ジョブステータス型
 */
export type JobStatusType = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * ジョブステータスDTO
 */
export interface JobStatus {
  id: string;
  status: JobStatusType;
  progress: number;
  message?: string;
  result?: unknown;
  error?: ProblemDetails; // 失敗時の詳細エラー情報
  createdAt: string;
  updatedAt: string;
}

/**
 * ジョブをポーリングして完了を待つ
 * 
 * @param jobId ジョブID
 * @param onProgress 進捗コールバック
 * @param intervalMs ポーリング間隔（ミリ秒）
 * @param maxAttempts 最大試行回数
 * @returns 完了したジョブのresult
 */
export async function pollJob<T = unknown>(
  jobId: string,
  onProgress?: (progress: number, message?: string) => void,
  intervalMs = 1000,
  maxAttempts = 60
): Promise<T> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const job = await apiGet<JobStatus>(`/core_api/jobs/${jobId}`);

      // 進捗コールバック
      if (onProgress) {
        onProgress(job.progress, job.message);
      }

      // 完了
      if (job.status === 'completed') {
        notifySuccess('処理が完了しました', job.message);
        return job.result as T;
      }

      // 失敗
      if (job.status === 'failed') {
        if (job.error) {
          notifyApiError(job.error, '処理に失敗しました');
        } else {
          notifyApiError(
            { code: 'JOB_FAILED', status: 500, userMessage: '処理に失敗しました' },
            '処理に失敗しました'
          );
        }
        throw new Error('JOB_FAILED');
      }

      // キャンセル
      if (job.status === 'cancelled') {
        if (job.error) {
          notifyApiError(job.error, '処理がキャンセルされました');
        } else {
          notifyApiError(
            { code: 'JOB_CANCELLED', status: 400, userMessage: '処理がキャンセルされました' },
            '処理がキャンセルされました'
          );
        }
        throw new Error('JOB_CANCELLED');
      }

      // 待機
      await new Promise(resolve => setTimeout(resolve, intervalMs));
      attempts++;
    } catch (error) {
      // エラーが JOB_FAILED/JOB_CANCELLED の場合はそのまま throw
      if (error instanceof Error && (error.message === 'JOB_FAILED' || error.message === 'JOB_CANCELLED')) {
        throw error;
      }
      // その他のエラーは notifyApiError で通知
      notifyApiError(error, 'ジョブの取得に失敗しました');
      throw error;
    }
  }

  // タイムアウト
  notifyApiError(
    { code: 'TIMEOUT', status: 408, userMessage: 'ジョブの完了待機がタイムアウトしました' },
    'タイムアウトしました'
  );
  throw new Error('POLL_TIMEOUT');
}

/**
 * ジョブを作成してポーリング
 * 
 * @param endpoint ジョブ作成エンドポイント
 * @param body リクエストボディ
 * @param onProgress 進捗コールバック
 * @returns 完了したジョブのresult
 */
export async function createAndPollJob<T = unknown>(
  endpoint: string,
  body: unknown,
  onProgress?: (progress: number, message?: string) => void
): Promise<T> {
  try {
    // ジョブを作成
    const job = await apiGet<JobStatus>(`${endpoint}`, { params: body });
    
    // ポーリング開始
    return await pollJob<T>(job.id, onProgress);
  } catch (error) {
    notifyApiError(error, 'ジョブの作成に失敗しました');
    throw error;
  }
}
