// /app/src/types/notification.ts

/**
 * 通知の種類を定義
 * - success: 成功通知（緑色）
 * - error: エラー通知（赤色）
 * - warning: 警告通知（黄色）
 * - info: 情報通知（青色）
 */
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

/**
 * 通知のデータ構造
 */
export interface Notification {
  /** 通知の一意のID */
  id: string;
  /** 通知の種類 */
  type: NotificationType;
  /** 通知のタイトル */
  title: string;
  /** 通知のメッセージ */
  message?: string;
  /** 通知の作成日時 */
  createdAt: Date;
  /** 自動で削除するまでの時間（ミリ秒）。nullの場合は手動削除のみ */
  duration?: number | null;
}

/**
 * 新しい通知を作成するためのデータ（IDと作成日時は自動生成）
 */
export interface CreateNotificationData {
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number | null;
}
