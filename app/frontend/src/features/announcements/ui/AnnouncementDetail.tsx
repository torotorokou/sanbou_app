/**
 * AnnouncementDetail - お知らせ詳細UI
 * 
 * お知らせの詳細を表示するコンポーネント。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Card, Tag, Typography, Divider, Space } from 'antd';
import { CalendarOutlined } from '@ant-design/icons';
import type { Announcement } from '../domain/announcement';

const { Title, Text } = Typography;

interface AnnouncementDetailProps {
  /** 表示するお知らせ */
  announcement: Announcement;
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

/**
 * 簡易的なMarkdown→HTMLレンダリング
 */
function renderMarkdownSimple(md: string): React.ReactNode {
  const lines = md.split('\n');
  return lines.map((line, index) => {
    // 見出し
    if (line.startsWith('## ')) {
      return (
        <Title level={4} key={index} style={{ marginTop: 24, marginBottom: 12 }}>
          {line.replace('## ', '')}
        </Title>
      );
    }
    if (line.startsWith('### ')) {
      return (
        <Title level={5} key={index} style={{ marginTop: 16, marginBottom: 8 }}>
          {line.replace('### ', '')}
        </Title>
      );
    }
    // 強調（**text**）
    const boldReplaced = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // リスト
    if (line.startsWith('- ')) {
      return (
        <div
          key={index}
          style={{ marginBottom: 8, paddingLeft: 16 }}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{
            __html: `• ${boldReplaced.replace('- ', '')}`,
          }}
        />
      );
    }
    if (line.match(/^\d+\. /)) {
      return (
        <div
          key={index}
          style={{ marginBottom: 8, paddingLeft: 16 }}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: boldReplaced }}
        />
      );
    }
    // 空行
    if (line.trim() === '') {
      return <div key={index} style={{ height: 12 }} />;
    }
    // 通常行
    return (
      <div
        key={index}
        style={{ marginBottom: 8, lineHeight: '1.6' }}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: boldReplaced }}
      />
    );
  });
}

export const AnnouncementDetail: React.FC<AnnouncementDetailProps> = ({
  announcement,
}) => {
  return (
    <Card style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* ヘッダー */}
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <Title level={2} style={{ margin: 0, flex: 1 }}>
            {announcement.title}
          </Title>
          <Space>
            <Tag color={getSeverityTagColor(announcement.severity)} style={{ fontSize: 13 }}>
              {getSeverityLabel(announcement.severity)}
            </Tag>
            {announcement.pinned && (
              <Tag color="purple" style={{ fontSize: 13 }}>
                ピン留め
              </Tag>
            )}
          </Space>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CalendarOutlined style={{ color: '#8c8c8c' }} />
          <Text type="secondary" style={{ fontSize: 13 }}>
            公開日: {formatDate(announcement.publishFrom)}
            {announcement.publishTo && (
              <> 〜 {formatDate(announcement.publishTo)}</>
            )}
          </Text>
        </div>
      </Space>

      <Divider style={{ margin: '20px 0' }} />

      {/* 本文 */}
      <div style={{ fontSize: 15, color: '#262626' }}>
        {renderMarkdownSimple(announcement.bodyMd)}
      </div>
    </Card>
  );
};
