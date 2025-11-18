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
import { ApiError } from '@shared/types';

export class DatasetImportRepositoryImpl implements DatasetImportRepository {
  async upload(filesByType: Record<string, File>, uploadPath: string, signal?: AbortSignal): Promise<void> {
    const form = buildFormData(filesByType);

    try {
      const result: UploadResponseShape = await DatasetImportClient.post(
        uploadPath,
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
      // 409 Conflict (重複エラー) の特別処理
      if (error instanceof ApiError && error.httpStatus === 409 && error.code === 'DUPLICATE_FILE') {
        notifyError(
          '重複エラー',
          '同じファイルが既にアップロード済みです。'
        );
        notifyInfo(
          '対処方法',
          '「×」ボタンでファイルを削除し、別のファイルを選択してください。または、DB内の既存データを削除してから再度お試しください。'
        );
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          notifyWarning('キャンセル', 'アップロードがキャンセルされました。');
        } else if (error instanceof ApiError) {
          // ApiError の場合はより詳細な情報を表示
          notifyError(
            'アップロードエラー',
            error.userMessage || error.message
          );
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
