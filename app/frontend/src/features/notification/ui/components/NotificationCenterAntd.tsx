import React from "react";
import { Alert, Space } from "antd";
import { useNotificationStore } from "@features/notification/domain/services/notificationStore";
import { useResponsive } from "@shared/hooks/ui/useResponsive";
import type {
  NotificationType,
  Notification,
} from "@features/notification/domain/types/notification.types";

// 通知の種類をAnt DesignのAlert typeにマッピング
const getAlertType = (
  type: NotificationType,
): "success" | "info" | "warning" | "error" => {
  switch (type) {
    case "success":
      return "success";
    case "error":
      return "error";
    case "warning":
      return "warning";
    case "info":
    default:
      return "info";
  }
};

/**
 * レスポンシブ対応スタイルを取得
 * - モバイル: 画面下部に表示、フル幅、コンパクト表示
 * - タブレット: 右上に表示、中サイズ
 * - デスクトップ: 右上に表示、広めの幅
 */
const getResponsiveStyles = (isMobile: boolean, isTablet: boolean) => {
  if (isMobile) {
    return {
      container: {
        position: "fixed" as const,
        bottom: 12,
        left: 8,
        right: 8,
        top: "auto" as const,
        zIndex: 9999,
        maxWidth: "100%",
        width: "calc(100% - 16px)",
      },
      alert: {
        marginBottom: 0,
        boxShadow: "0 -2px 8px rgba(0, 0, 0, 0.15)",
        border: "1px solid #d9d9d9",
        fontSize: 13,
        padding: "8px 12px",
      },
      space: {
        width: "100%",
        gap: 6,
      },
    };
  }

  if (isTablet) {
    return {
      container: {
        position: "fixed" as const,
        top: 16,
        right: 12,
        zIndex: 9999,
        maxWidth: 320,
        width: "calc(100% - 24px)",
      },
      alert: {
        marginBottom: 0,
        boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
        border: "1px solid #d9d9d9",
        fontSize: 13,
      },
      space: {
        width: "100%",
      },
    };
  }

  // Desktop
  return {
    container: {
      position: "fixed" as const,
      top: 20,
      right: 20,
      zIndex: 9999,
      maxWidth: 400,
      width: "calc(100% - 40px)",
    },
    alert: {
      marginBottom: 0,
      boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
      border: "1px solid #d9d9d9",
    },
    space: {
      width: "100%",
    },
  };
};

// 前の NotificationContainer と同等の見た目（AntD版）
const NotificationCenterAntd: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();
  const { isMobile, isTablet } = useResponsive();

  if (notifications.length === 0) return null;

  const styles = getResponsiveStyles(isMobile, isTablet);

  return (
    <div style={styles.container}>
      <Space
        direction="vertical"
        size={isMobile ? 6 : "small"}
        style={styles.space}
      >
        {notifications.map((n: Notification) => (
          <Alert
            key={n.id}
            type={getAlertType(n.type)}
            message={n.title}
            description={
              isMobile && n.message && n.message.length > 50
                ? `${n.message.slice(0, 50)}...`
                : n.message
            }
            showIcon
            closable
            onClose={() => removeNotification(n.id)}
            style={styles.alert}
          />
        ))}
      </Space>
    </div>
  );
};

export default NotificationCenterAntd;
