import React from 'react';
import { Alert, Space } from 'antd';
import { useNotificationStore } from '@features/notification/domain/services/notificationStore';
import type { NotificationType, Notification } from '@features/notification/domain/types/notification.types';

// 通知の種類をAnt DesignのAlert typeにマッピング
const getAlertType = (type: NotificationType): 'success' | 'info' | 'warning' | 'error' => {
  switch (type) {
    case 'success':
      return 'success';
    case 'error':
      return 'error';
    case 'warning':
      return 'warning';
    case 'info':
    default:
      return 'info';
  }
};

// 前の NotificationContainer と同等の見た目（AntD版）
const NotificationCenterAntd: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();

  if (notifications.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
        maxWidth: 400,
        width: 'calc(100% - 40px)',
      }}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {notifications.map((n: Notification) => (
          <Alert
            key={n.id}
            type={getAlertType(n.type)}
            message={n.title}
            description={n.message}
            showIcon
            closable
            onClose={() => removeNotification(n.id)}
            style={{
              marginBottom: 0,
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
              border: '1px solid #d9d9d9',
            }}
          />
        ))}
      </Space>
    </div>
  );
};

export default NotificationCenterAntd;
