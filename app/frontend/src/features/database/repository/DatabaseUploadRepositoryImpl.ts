/**
 * データベースアップロード Repository 実装
 */

import type { DatabaseUploadRepository } from './DatabaseUploadRepository';
import { DatabaseUploadClient } from '../api/client';
import type { UploadResponseShape } from '../model/types';
import {
  notifySuccess,
  notifyError,
  notifyInfo,
  notifyWarning,
} from '@features/notification';

export class DatabaseUploadRepositoryImpl implements DatabaseUploadRepository {
  async upload(filesByType: Record<string, File>, signal?: AbortSignal): Promise<void> {
    const form = new FormData();
    for (const [key, file] of Object.entries(filesByType)) {
      form.append(key, file);
    }

    try {
      const result: UploadResponseShape = await DatabaseUploadClient.postFormData(
        '/core_api/database/upload/syogun_csv',
        form,
        { timeout: 60000, signal }
      );

      if (result.status === 'success') {
        notifySuccess('アップロード成功', result.detail ?? 'CSVを受け付けました。');
        if (result.hint) {
          notifyInfo('ヒント', result.hint);
        }
      } else {
        notifyError(
          'アップロード失敗',
          result?.detail ?? 'アップロード中にエラーが発生しました。'
        );

        if (result?.hint) {
          notifyInfo('ヒント', result.hint);
        }

        const issues = result?.result;
        if (issues) {
          Object.entries(issues).forEach(([key, val]) => {
            if (val?.status === 'error') {
              notifyWarning(
                `[${val.filename ?? key}] のエラー`,
                val.detail ?? '詳細不明のエラーが発生しました。'
              );
            }
          });
        }
      }
    } catch (error) {
      // エラーハンドリング
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          notifyWarning('キャンセル', 'アップロードがキャンセルされました。');
        } else {
          notifyError('アップロードエラー', error.message);
        }
      } else {
        notifyError(
          '接続エラー',
          'サーバーに接続できませんでした。ネットワークを確認してください。'
        );
      }
      throw error;
    }
  }
}
