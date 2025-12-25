/**
 * グローバルアップロードポーリングマネージャー
 *
 * 責務:
 * - ページ遷移しても継続するバックグラウンドポーリング
 * - 複数のアップロードを同時に追跡
 * - 処理完了/失敗時にグローバル通知を表示
 *   - 成功: 5秒autoDismiss
 *   - エラー/タイムアウト: sticky（手動クローズのみ）
 */

import { DatasetImportClient } from '../infrastructure/client';
import { useNotificationStore } from '@features/notification/domain/services/notificationStore';

interface PollingJob {
  csvType: string;
  fileId: number;
  fileName?: string;
  attemptCount: number;
  timerId?: ReturnType<typeof setTimeout>;
}

type CompletionCallback = (fileIds: number[], allSuccess: boolean) => void;

const DEFAULT_INTERVAL = 3000; // 3秒
const DEFAULT_MAX_ATTEMPTS = 40; // 最大120秒
const INITIAL_DELAY = 3000; // 初回チェックまでの遅延

class GlobalUploadPollingManager {
  private jobs = new Map<number, PollingJob>();
  private isRunning = false;
  private completionCallbacks = new Set<CompletionCallback>();
  private currentBatchFileIds: number[] = []; // 現在のバッチのfileId群

  /**
   * 完了コールバックを登録
   */
  onCompletion(callback: CompletionCallback): () => void {
    this.completionCallbacks.add(callback);
    // アンサブスクライブ関数を返す
    return () => {
      this.completionCallbacks.delete(callback);
    };
  }

  /**
   * 新しいアップロードジョブを追加
   */
  addJobs(uploadFileIds: Record<string, number>): void {
    console.log('[GlobalPollingManager] Adding jobs:', uploadFileIds);

    const newFileIds: number[] = [];
    Object.entries(uploadFileIds).forEach(([csvType, fileId]) => {
      if (!this.jobs.has(fileId)) {
        this.jobs.set(fileId, {
          csvType,
          fileId,
          attemptCount: 0,
        });
        newFileIds.push(fileId);
      }
    });

    // 新しいバッチとして記録
    this.currentBatchFileIds = newFileIds;

    if (!this.isRunning) {
      this.start();
    }
  }

  /**
   * ポーリング開始
   */
  private start(): void {
    if (this.isRunning) return;

    this.isRunning = true;
    console.log('[GlobalPollingManager] Starting polling...');

    // 初回は遅延させる
    setTimeout(() => this.checkAll(), INITIAL_DELAY);
  }

  /**
   * すべてのジョブをチェック
   */
  private async checkAll(): Promise<void> {
    if (this.jobs.size === 0) {
      this.stop();
      return;
    }

    const jobArray = Array.from(this.jobs.values());
    console.log(`[GlobalPollingManager] Checking ${jobArray.length} jobs...`);

    const results = await Promise.all(jobArray.map((job) => this.checkJob(job)));

    // 完了したジョブを削除し、成功/失敗を記録
    const completedFileIds: number[] = [];
    let hasFailures = false;

    results.forEach(({ fileId, completed, success }) => {
      if (completed) {
        completedFileIds.push(fileId);
        this.jobs.delete(fileId);
        if (!success) {
          hasFailures = true;
        }
      }
    });

    // 現在のバッチがすべて完了したかチェック
    if (completedFileIds.length > 0) {
      const batchCompleted = this.currentBatchFileIds.every((id) => !this.jobs.has(id));

      if (batchCompleted && this.currentBatchFileIds.length > 0) {
        // バッチ全体が完了した場合、コールバックを呼ぶ
        const allSuccess = !hasFailures;
        console.log('[GlobalPollingManager] Batch completed. All success:', allSuccess);

        this.completionCallbacks.forEach((callback) => {
          callback(this.currentBatchFileIds, allSuccess);
        });

        this.currentBatchFileIds = [];
      }
    }

    // まだジョブが残っている場合は次回のチェックをスケジュール
    if (this.jobs.size > 0) {
      setTimeout(() => this.checkAll(), DEFAULT_INTERVAL);
    } else {
      this.stop();
    }
  }

  /**
   * 個別ジョブをチェック
   */
  private async checkJob(
    job: PollingJob
  ): Promise<{ fileId: number; completed: boolean; success: boolean }> {
    job.attemptCount += 1;

    try {
      const response = await DatasetImportClient.checkStatus(job.fileId);
      const status = response.result?.processing_status;
      const errorMessage = response.result?.error_message;
      const rowCount = response.result?.row_count;
      const fileName = response.result?.file_name || job.fileName || job.csvType;

      console.log(
        `[GlobalPollingManager] Job ${job.fileId} (${job.csvType}): ${status} (attempt ${job.attemptCount}/${DEFAULT_MAX_ATTEMPTS})`
      );

      // 処理中の場合は継続
      if (status === 'pending' || status === 'processing') {
        // タイムアウトチェック
        if (job.attemptCount >= DEFAULT_MAX_ATTEMPTS) {
          // sticky通知（手動クローズのみ）
          useNotificationStore.getState().warning(
            '処理タイムアウト',
            `${fileName} の処理が時間内に完了しませんでした。履歴画面で確認してください。`,
            0 // sticky
          );
          return { fileId: job.fileId, completed: true, success: false };
        }
        return { fileId: job.fileId, completed: false, success: false };
      }

      // 失敗
      if (status === 'failed') {
        // sticky通知（手動クローズのみ）
        useNotificationStore.getState().error(
          '処理失敗',
          `【${fileName}】${errorMessage || '処理エラー'}`,
          0 // sticky
        );
        return { fileId: job.fileId, completed: true, success: false };
      }

      // 成功
      if (status === 'success') {
        const rowInfo = rowCount ? `（${rowCount.toLocaleString()}行）` : '';
        // 5秒autoDismiss
        useNotificationStore
          .getState()
          .success('処理完了', `${fileName} の処理が完了しました。${rowInfo}`, 5000);
        return { fileId: job.fileId, completed: true, success: true };
      }

      // 不明なステータスは完了扱い（失敗として）
      return { fileId: job.fileId, completed: true, success: false };
    } catch (error) {
      console.warn(`[GlobalPollingManager] API error for job ${job.fileId}, will retry:`, error);

      // API エラーはタイムアウトまで継続
      if (job.attemptCount >= DEFAULT_MAX_ATTEMPTS) {
        // sticky通知（手動クローズのみ）
        useNotificationStore.getState().error(
          'ステータス確認エラー',
          `${job.fileName || job.csvType} の処理状況を確認できませんでした。履歴画面で確認してください。`,
          0 // sticky
        );
        return { fileId: job.fileId, completed: true, success: false };
      }

      return { fileId: job.fileId, completed: false, success: false };
    }
  }

  /**
   * ポーリング停止
   */
  private stop(): void {
    this.isRunning = false;
    console.log('[GlobalPollingManager] Stopped polling.');
  }

  /**
   * すべてのジョブをキャンセル（デバッグ用）
   */
  clearAll(): void {
    this.jobs.clear();
    this.stop();
    console.log('[GlobalPollingManager] All jobs cleared.');
  }

  /**
   * 現在のジョブ数を取得（デバッグ用）
   */
  getJobCount(): number {
    return this.jobs.size;
  }
}

// シングルトンインスタンス
export const globalUploadPollingManager = new GlobalUploadPollingManager();
