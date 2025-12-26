import React from "react";
import { useNotificationStore } from "@features/notification/domain/services/notificationStore";
import { useResponsive } from "@shared/hooks/ui/useResponsive";

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
        top: undefined,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column-reverse" as const,
        gap: 6,
        width: "auto",
      },
      card: {
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        boxShadow: "0 -4px 12px rgba(0,0,0,.12)",
        padding: "10px 12px",
        fontSize: 13,
      },
      title: {
        fontWeight: 600,
        marginBottom: 2,
        fontSize: 13,
      },
      message: {
        color: "#444",
        marginBottom: 6,
        fontSize: 12,
        lineHeight: 1.4,
      },
      button: {
        border: "1px solid #ddd",
        background: "#fafafa",
        borderRadius: 4,
        padding: "4px 10px",
        cursor: "pointer",
        fontSize: 12,
      },
    };
  }

  if (isTablet) {
    return {
      container: {
        position: "fixed" as const,
        top: 12,
        right: 12,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column" as const,
        gap: 6,
        width: 300,
      },
      card: {
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        boxShadow: "0 6px 16px rgba(0,0,0,.08)",
        padding: 10,
      },
      title: {
        fontWeight: 600,
        marginBottom: 4,
        fontSize: 14,
      },
      message: {
        color: "#444",
        marginBottom: 8,
        fontSize: 13,
      },
      button: {
        border: "1px solid #ddd",
        background: "#fafafa",
        borderRadius: 6,
        padding: "4px 10px",
        cursor: "pointer",
        fontSize: 13,
      },
    };
  }

  // Desktop
  return {
    container: {
      position: "fixed" as const,
      top: 16,
      right: 16,
      zIndex: 9999,
      display: "flex",
      flexDirection: "column" as const,
      gap: 8,
      width: 360,
    },
    card: {
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      boxShadow: "0 8px 20px rgba(0,0,0,.08)",
      padding: 12,
    },
    title: {
      fontWeight: 600,
      marginBottom: 4,
    },
    message: {
      color: "#444",
      marginBottom: 8,
    },
    button: {
      border: "1px solid #ddd",
      background: "#fafafa",
      borderRadius: 6,
      padding: "4px 10px",
      cursor: "pointer",
    },
  };
};

export const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();
  const { isMobile, isTablet } = useResponsive();

  if (notifications.length === 0) return null;

  const styles = getResponsiveStyles(isMobile, isTablet);

  return (
    <div style={styles.container}>
      {notifications.map((n) => (
        <div key={n.id} style={styles.card}>
          <div style={styles.title}>
            {n.title}{" "}
            <small style={{ color: "#999", fontWeight: 400 }}>({n.type})</small>
          </div>
          {n.message && (
            <div style={styles.message}>
              {isMobile && n.message.length > 60
                ? `${n.message.slice(0, 60)}...`
                : n.message}
            </div>
          )}
          <div style={{ textAlign: "right" }}>
            <button
              onClick={() => removeNotification(n.id)}
              style={styles.button}
            >
              閉じる
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationCenter;
