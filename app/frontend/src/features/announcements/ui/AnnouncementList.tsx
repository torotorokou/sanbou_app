/**
 * AnnouncementList - お知らせ一覧UI
 * 
 * お知らせ一覧を表示するコンポーネント。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { List, Tag, Typography, Badge } from 'antd';
import {
  InfoCircleOutlined,
  WarningOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import type { Announcement } from '../domain/announcement';

const { Text } = Typography;

interface AnnouncementListProps {
  /** お知らせ一覧 */
  items: Announcement[];
  /** 詳細を開くコールバック */
  onOpen: (id: string) => void;
  /** 指定IDが未読かどうかを判定する関数 */
  isUnread: (id: string) => boolean;
}

/**
 * 重要度に応じたタグ色を返す
 */
function getSeverityTagColor(severity: Announcement['severity']): string {
  switch (severity) {
    case 'critical':
      return 'red';
    case 'warn':
      return 'orange';
    case 'info':
    default:
      return 'blue';
  }
}

/**
 * 重要度に応じたラベルを返す
 */
function getSeverityLabel(severity: Announcement['severity']): string {
  switch (severity) {
    case 'critical':
      return '重要';
    case 'warn':
      return '注意';
    case 'info':
    default:
      return '情報';
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
      return <InfoCircleOutlined />;
  }
}

/**
 * 日付をフォーマット
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export const AnnouncementList: React.FC<AnnouncementListProps> = ({
  items,
  onOpen,
  isUnread,
}) => {
  return (
    <List
      itemLayout="horizontal"
      dataSource={items}
      renderItem={(item) => {
        const unread = isUnread(item.id);

        return (
          <List.Item
            onClick={() => onOpen(item.id)}
            style={{
              cursor: 'pointer',
              backgroundColor: unread ? '#f6ffed' : 'transparent',
              borderLeft: unread ? '3px solid #52c41a' : '3px solid transparent',
              paddingLeft: 12,
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#fafafa';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = unread
                ? '#f6ffed'
                : 'transparent';
            }}
          >
            <List.Item.Meta
              avatar={
                <Badge dot={unread} offset={[-2, 2]}>
                  <span style={{ fontSize: 20 }}>
                    {getSeverityIcon(item.severity)}
                  </span>
                </Badge>
              }
              title={
                <span
                  style={{
                    fontWeight: unread ? 600 : 400,
                  }}
                >
                  {item.title}
                  <Tag
                    color={getSeverityTagColor(item.severity)}
                    style={{ marginLeft: 8 }}
                  >
                    {getSeverityLabel(item.severity)}
                  </Tag>
                  {item.pinned && (
                    <Tag color="purple" style={{ marginLeft: 4 }}>
                      ピン留め
                    </Tag>
                  )}
                </span>
              }
              description={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  公開日: {formatDate(item.publishFrom)}
                </Text>
              }
            />
          </List.Item>
        );
      }}
    />
  );
};
