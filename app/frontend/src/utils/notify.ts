// src/utils/notify.ts
import { useNotificationStore } from '../stores/notificationStore';

/**
 * 成功通知を表示する
 * @param title 通知のタイトル
 * @param message 通知の詳細メッセージ（省略可能）
 * @param duration 自動削除までの時間（ミリ秒、省略時は3秒）
 */
export const notifySuccess = (
    title: string,
    message?: string,
    duration?: number
) => {
    useNotificationStore.getState().addNotification({
        type: 'success',
        title,
        message,
        duration: duration !== undefined ? duration : 4000, // デフォルト4秒
    });
};

/**
 * エラー通知を表示する
 * @param title 通知のタイトル
 * @param message 通知の詳細メッセージ（省略可能）
 * @param duration 自動削除までの時間（ミリ秒、省略時は6秒）
 */
export const notifyError = (
    title: string,
    message?: string,
    duration?: number
) => {
    useNotificationStore.getState().addNotification({
        type: 'error',
        title,
        message,
        duration: duration !== undefined ? duration : 6000, // デフォルト6秒
    });
};

/**
 * 情報通知を表示する
 * @param title 通知のタイトル
 * @param message 通知の詳細メッセージ（省略可能）
 * @param duration 自動削除までの時間（ミリ秒、省略時は5秒）
 */
export const notifyInfo = (
    title: string,
    message?: string,
    duration?: number
) => {
    useNotificationStore.getState().addNotification({
        type: 'info',
        title,
        message,
        duration: duration !== undefined ? duration : 5000, // デフォルト5秒
    });
};

/**
 * 警告通知を表示する
 * @param title 通知のタイトル
 * @param message 通知の詳細メッセージ（省略可能）
 * @param duration 自動削除までの時間（ミリ秒、省略時は5秒）
 */
export const notifyWarning = (
    title: string,
    message?: string,
    duration?: number
) => {
    useNotificationStore.getState().addNotification({
        type: 'warning',
        title,
        message,
        duration: duration !== undefined ? duration : 5000, // デフォルト5秒
    });
};

/**
 * 手動削除のみの通知を表示する（自動削除されない）
 * @param type 通知の種類
 * @param title 通知のタイトル
 * @param message 通知の詳細メッセージ（省略可能）
 */
export const notifyPersistent = (
    type: 'success' | 'error' | 'warning' | 'info',
    title: string,
    message?: string
) => {
    useNotificationStore.getState().addNotification({
        type,
        title,
        message,
        duration: null, // 自動削除しない
    });
};
