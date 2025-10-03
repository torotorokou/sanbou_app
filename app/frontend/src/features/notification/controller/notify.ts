import { useNotificationStore } from '../model/notification.store';
import { NOTIFY_DEFAULTS } from '../config';

// 既存プロジェクトに ApiError / ProblemDetails がある場合は import に置き換え
type ProblemDetails = {
  type?: string; title?: string; status?: number; code?: string;
  userMessage?: string; traceId?: string;
};
class ApiError extends Error {
  code: string; status: number; userMessage: string; traceId?: string;
  constructor(code: string, status: number, userMessage: string, traceId?: string) {
    super(userMessage); this.code = code; this.status = status; this.userMessage = userMessage; this.traceId = traceId;
  }
}

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
  notify('success', title, message, duration ?? NOTIFY_DEFAULTS.successMs);

export const notifyError = (title: string, message?: string, duration?: number) =>
  notify('error', title, message, duration ?? NOTIFY_DEFAULTS.errorMs);

export const notifyInfo = (title: string, message?: string, duration?: number) =>
  notify('info', title, message, duration ?? NOTIFY_DEFAULTS.infoMs);

export const notifyWarning = (title: string, message?: string, duration?: number) =>
  notify('warning', title, message, duration ?? NOTIFY_DEFAULTS.warningMs);

export const notifyPersistent = (
  type: NotificationType,
  title: string,
  message?: string
): string => notify(type, title, message, NOTIFY_DEFAULTS.persistent);

/** RFC7807 / ApiError を通知に変換（共通の catch で使う） */
export const notifyApiError = (err: unknown, title = 'エラーが発生しました'): string => {
  if (err instanceof ApiError) {
    const msg = err.userMessage || err.message || '処理に失敗しました';
    return notifyError(title, msg);
  }
  const pd = err as ProblemDetails | undefined;
  if (pd?.userMessage || pd?.title) {
    const msg = pd.userMessage ?? pd.title ?? '処理に失敗しました';
    return notifyError(title, msg);
  }
  let msg: string;
  if (typeof err === 'string') {
    msg = err;
  } else if (err && typeof err === 'object' && 'message' in err) {
    const maybeMsg = (err as { message?: unknown }).message;
    msg = typeof maybeMsg === 'string' ? maybeMsg : '不明なエラーが発生しました';
  } else {
    msg = '不明なエラーが発生しました';
  }
  return notifyError(title, msg);
};
