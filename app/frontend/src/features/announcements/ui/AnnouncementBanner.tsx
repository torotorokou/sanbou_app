/**
 * AnnouncementBanner - 重要通知バナーUI
 * 
 * トップページに表示する重要通知。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Alert, Button, Space } from 'antd';
import { CloseOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';
import type { Announcement } from '../domain/announcement';

interface AnnouncementBannerProps {
  /** 表示するお知らせ */
  announcement: Announcement;
  /** 閉じる（確認済みにする）コールバック */
  onClose: () => void;
  /** 「理解した」ボタンのコールバック（onCloseと同じ挙動でも可） */
  onAcknowledge: () => void;
}

/**
 * 重要度に応じたアラートタイプを返す
 */
function getSeverityType(
  severity: Announcement['severity']
): 'warning' | 'error' | 'info' {
  switch (severity) {
    case 'critical':
      return 'error';
    case 'warn':
      return 'warning';
    case 'info':
    default:
      return 'info';
  }
}

/**
 * 重要度に応じたアイコンを返す
 */
function getSeverityIcon(severity: Announcement['severity']): React.ReactNode {
  switch (severity) {
    case 'critical':
      return <ExclamationCircleOutlined />;
    case 'warn':
      return <WarningOutlined />;
    case 'info':
    default:
      return null;
  }
}

export const AnnouncementBanner: React.FC<AnnouncementBannerProps> = ({
  announcement,
  onClose,
  onAcknowledge,
}) => {
  const alertType = getSeverityType(announcement.severity);
  const icon = getSeverityIcon(announcement.severity);

  return (
    <Alert
      type={alertType}
      icon={icon}
      showIcon
      message={announcement.title}
      description={
        <Space direction="vertical" style={{ width: '100%' }}>
          <span>
            {announcement.bodyMd.substring(0, 100)}
            {announcement.bodyMd.length > 100 ? '...' : ''}
          </span>
          <Button type="primary" size="small" onClick={onAcknowledge}>
            理解しました
          </Button>
        </Space>
      }
      closable
      closeIcon={<CloseOutlined />}
      onClose={onClose}
      style={{ marginBottom: 16 }}
    />
  );
};
