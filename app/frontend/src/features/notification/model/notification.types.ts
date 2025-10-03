export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  createdAt: Date;
  duration?: number | null;
}

export interface CreateNotificationData {
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number | null;
}
