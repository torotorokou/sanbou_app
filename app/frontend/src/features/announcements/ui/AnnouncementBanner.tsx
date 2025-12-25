/**
 * AnnouncementBanner - 重要通知バナーUI
 *
 * トップページに表示する重要通知。
 * 状態レス：propsのみで動作。
 */

import React from "react";
import { Alert, Button, Space } from "antd";
import {
  CloseOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useResponsive } from "@/shared";
import type { Announcement } from "../domain/announcement";
import { stripMarkdownForSnippet } from "../domain/stripMarkdownForSnippet";

interface AnnouncementBannerProps {
  /** 表示するお知らせ */
  announcement: Announcement;
  /** 閉じる（既読にする）コールバック */
  onClose: () => void;
  /** 詳細ページへの遷移コールバック（既読にして遷移） */
  onNavigateToDetail?: (navigateFn: () => void) => void;
  /** 実際の遷移処理 */
  navigateFn?: () => void;
}

/**
 * 重要度に応じたアラートタイプを返す
 */
function getSeverityType(
  severity: Announcement["severity"],
): "warning" | "error" | "info" {
  switch (severity) {
    case "critical":
      return "error";
    case "warn":
      return "warning";
    case "info":
    default:
      return "info";
  }
}

/**
 * 重要度に応じたアイコンを返す
 */
function getSeverityIcon(severity: Announcement["severity"]): React.ReactNode {
  switch (severity) {
    case "critical":
      return <ExclamationCircleOutlined />;
    case "warn":
      return <WarningOutlined />;
    case "info":
    default:
      return null;
  }
}

export const AnnouncementBanner: React.FC<AnnouncementBannerProps> = ({
  announcement,
  onClose,
  onNavigateToDetail,
  navigateFn,
}) => {
  const { isMobile } = useResponsive();
  const alertType = getSeverityType(announcement.severity);
  const icon = getSeverityIcon(announcement.severity);

  const handleClick = () => {
    if (onNavigateToDetail && navigateFn) {
      // 既読にしてから遷移
      onNavigateToDetail(navigateFn);
    } else if (navigateFn) {
      // フォールバック
      navigateFn();
    }
  };

  return (
    <Alert
      type={alertType}
      icon={icon}
      showIcon
      message={
        isMobile ? (
          <span
            style={{
              fontSize: "13px",
              fontWeight: 600,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {announcement.title}
          </span>
        ) : (
          <span style={{ fontSize: "15px" }}>{announcement.title}</span>
        )
      }
      description={
        !isMobile ? (
          <span style={{ fontSize: "14px" }}>
            {stripMarkdownForSnippet(announcement.bodyMd, 100)}
          </span>
        ) : undefined
      }
      action={
        onNavigateToDetail && navigateFn ? (
          <Button
            type="primary"
            size="small"
            onClick={handleClick}
            style={
              isMobile
                ? { fontSize: "12px", height: "24px", padding: "0 8px" }
                : undefined
            }
          >
            {isMobile ? "詳細" : "詳細を見る"}
          </Button>
        ) : undefined
      }
      closable
      closeIcon={<CloseOutlined />}
      onClose={onClose}
      style={{ marginBottom: isMobile ? 4 : 16 }}
    />
  );
};
