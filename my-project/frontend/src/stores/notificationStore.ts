import { create } from 'zustand';
import type {
    Notification,
    CreateNotificationData,
} from '../types/notification';

/**
 * 通知ストアの状態の型定義
 */
interface NotificationState {
    /** 現在表示中の通知一覧 */
    notifications: Notification[];

    /** 通知を追加する */
    addNotification: (data: CreateNotificationData) => void;

    /** 指定したIDの通知を削除する */
    removeNotification: (id: string) => void;

    /** すべての通知を削除する */
    clearAllNotifications: () => void;
}

/**
 * 通知管理のグローバルストア
 *
 * 使用例:
 * ```tsx
 * const { addNotification, removeNotification, notifications } = useNotificationStore();
 *
 * // 成功通知を追加
 * addNotification({
 *   type: 'success',
 *   title: '保存完了',
 *   message: 'データが正常に保存されました'
 * });
 * ```
 */
export const useNotificationStore = create<NotificationState>((set, get) => ({
    notifications: [],

    addNotification: (data: CreateNotificationData) => {
        // 一意のIDを生成（現在の時刻 + ランダム値）
        const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // デフォルトの自動削除時間（3秒）
        const defaultDuration = 3000;

        const newNotification: Notification = {
            id,
            type: data.type,
            title: data.title,
            message: data.message,
            createdAt: new Date(),
            duration:
                data.duration !== undefined ? data.duration : defaultDuration,
        };

        // 通知を一覧の先頭に追加
        set((state) => ({
            notifications: [newNotification, ...state.notifications],
        }));

        // 自動削除の設定（durationがnullでない場合）
        if (newNotification.duration && newNotification.duration > 0) {
            setTimeout(() => {
                get().removeNotification(id);
            }, newNotification.duration);
        }
    },

    removeNotification: (id: string) => {
        set((state) => ({
            notifications: state.notifications.filter(
                (notification) => notification.id !== id
            ),
        }));
    },

    clearAllNotifications: () => {
        set({ notifications: [] });
    },
}));
