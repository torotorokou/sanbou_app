import React from 'react';
import { Alert, Space } from 'antd';
import { useNotificationStore } from '../../stores/notificationStore';
import type { NotificationType, Notification } from '../../types/notification';

/**
 * 通知の種類をAnt DesignのAlert typeにマッピング
 */
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

/**
 * グローバル通知を表示するコンポーネント
 * 
 * 特徴:
 * - 画面右上に固定表示
 * - 複数の通知を縦に並べて表示
 * - 自動削除または手動削除が可能
 * - 最新の通知が上に表示される
 */
const NotificationContainer: React.FC = () => {
    const { notifications, removeNotification } = useNotificationStore();

    // 通知がない場合は何も表示しない
    if (notifications.length === 0) {
        return null;
    }

    return (
        <div
            style={{
                position: 'fixed',
                top: 20,
                right: 20,
                zIndex: 9999,
                maxWidth: 400,
                width: '100%',
            }}
        >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {notifications.map((notification: Notification) => (
                    <Alert
                        key={notification.id}
                        type={getAlertType(notification.type)}
                        message={notification.title}
                        description={notification.message}
                        showIcon
                        closable
                        onClose={() => removeNotification(notification.id)}
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

export default NotificationContainer;
