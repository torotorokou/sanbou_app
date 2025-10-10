/**
 * 通知コントローラー
 * 
 * 通知の表示・管理機能を提供
 */

import { useNotificationStore } from '@features/notification/model/notification.store';
import { NOTIFY_DEFAULTS, getNotificationConfig } from '@features/notification/config';
import type { ProblemDetails } from '@features/notification/model/contract';
import { ApiError } from '@shared/types';

type NotificationType = 'success' | 'error' | 'warning' | 'info';

const notify = (
  type: NotificationType,
  title: string,
  message?: string,
  duration?: number | null
): string => {
  return useNotificationStore.getState().addNotification({
    type, title, message, duration: duration ?? undefined,
  });
};

export const notifySuccess = (title: string, message?: string, duration?: number) =>
  notify('success', title, message, duration ?? NOTIFY_DEFAULTS.success);

export const notifyError = (title: string, message?: string, duration?: number) =>
  notify('error', title, message, duration ?? NOTIFY_DEFAULTS.error);

export const notifyInfo = (title: string, message?: string, duration?: number) =>
  notify('info', title, message, duration ?? NOTIFY_DEFAULTS.info);

export const notifyWarning = (title: string, message?: string, duration?: number) =>
  notify('warning', title, message, duration ?? NOTIFY_DEFAULTS.warning);

export const notifyPersistent = (
  type: NotificationType,
  title: string,
  message?: string
): string => notify(type, title, message, NOTIFY_DEFAULTS.persistent);

/**
 * API エラーを通知に変換（統一エラーハンドリング）
 * 
 * 使用例:
 * ```typescript
 * try {
 *   await apiPost('/api/upload', formData);
 * } catch (error) {
 *   notifyApiError(error, 'アップロードに失敗しました');
 * }
 * ```
 * 
 * @param err エラーオブジェクト（ApiError | ProblemDetails | Error | unknown）
 * @param fallbackTitle デフォルトのタイトル
 * @returns 通知ID
 */
export function notifyApiError(err: unknown, fallbackTitle = 'エラーが発生しました'): string {
  // ApiError の場合
  if (err instanceof ApiError) {
    const config = getNotificationConfig(err.code);
    const msg = err.userMessage || err.message || '処理に失敗しました';
    const duration = NOTIFY_DEFAULTS[config.severity];
    
    return notify(config.severity, config.title, msg, duration);
  }

  // ProblemDetails の場合
  const pd = err as Partial<ProblemDetails> & { message?: string };
  if (pd?.code && pd?.userMessage) {
    const config = getNotificationConfig(pd.code);
    const msg = pd.userMessage ?? pd.title ?? '処理に失敗しました';
    const duration = NOTIFY_DEFAULTS[config.severity];
    
    return notify(config.severity, config.title, msg, duration);
  }

  // 一般的な Error の場合
  if (err instanceof Error) {
    const msg = err.message || '不明なエラーが発生しました';
    return notifyError(fallbackTitle, msg);
  }

  // 文字列の場合
  if (typeof err === 'string') {
    return notifyError(fallbackTitle, err);
  }

  // オブジェクトの場合
  if (err && typeof err === 'object' && 'message' in err) {
    const maybeMsg = (err as { message?: unknown }).message;
    const msg = typeof maybeMsg === 'string' ? maybeMsg : '不明なエラーが発生しました';
    return notifyError(fallbackTitle, msg);
  }

  // その他
  return notifyError(fallbackTitle, '不明なエラーが発生しました');
}
