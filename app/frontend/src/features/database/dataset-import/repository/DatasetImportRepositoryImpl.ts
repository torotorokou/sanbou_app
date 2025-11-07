/**
 * データセットインポート Repository 実装
 */

import type { DatasetImportRepository } from './DatasetImportRepository';
import { DatasetImportClient } from '../api/client';
import { buildFormData } from '../../shared/upload/buildFormData';
import { DEFAULT_UPLOAD_TIMEOUT } from '../../shared/constants';
import type { UploadResponseShape } from '../../shared/types/common';
import {
  notifySuccess,
  notifyError,
  notifyInfo,
  notifyWarning,
} from '@features/notification';

export class DatasetImportRepositoryImpl implements DatasetImportRepository {
  async upload(filesByType: Record<string, File>, signal?: AbortSignal): Promise<void> {
    const form = buildFormData(filesByType);

    try {
      const result: UploadResponseShape = await DatasetImportClient.post(
        '/core_api/database/upload/syogun_csv',
        form,
        { timeout: DEFAULT_UPLOAD_TIMEOUT, signal }
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
