/**
 * AnnouncementListItem - お知らせアイテムUI（カード型）
 * 
 * プロフェッショナルな見た目のカード型アイテム。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Card, Tag, Space } from 'antd';
import { RightOutlined } from '@ant-design/icons';
import type { AnnouncementDisplayItem } from '../model/useAnnouncementsListViewModel';

interface AnnouncementListItemProps {
  /** 表示用に整形されたアイテム */
  item: AnnouncementDisplayItem;
  /** クリックコールバック */
  onOpen: (id: string) => void;
}

export const AnnouncementListItem: React.FC<AnnouncementListItemProps> = ({
  item,
  onOpen,
}) => {
  return (
    <Card
      onClick={() => onOpen(item.id)}
      style={{
        marginBottom: 8,
        borderRadius: 8,
        cursor: 'pointer',
        backgroundColor: '#fafafa',
        borderLeft: item.isUnread ? '4px solid #1890ff' : '4px solid transparent',
        transition: 'all 0.2s',
      }}
      styles={{
        body: {
          padding: '16px 20px',
          backgroundColor: '#fafafa',
        },
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        {/* 左側：未読ドット */}
        <div style={{ paddingTop: 4 }}>
          {item.isUnread && (
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#1890ff',
              }}
            />
          )}
        </div>

        {/* 中央：コンテンツ */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 1行目：タイトル + バッジ + 公開日 */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 6,
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 0 }}>
              <h4
                style={{
                  margin: 0,
                  fontSize: 16,
                  fontWeight: item.isUnread ? 600 : 400,
                  color: item.isUnread ? '#262626' : '#595959',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  flex: '0 1 auto',
                }}
              >
                {item.title}
              </h4>
              {item.badges.length > 0 && (
                <Space size={4} style={{ flexShrink: 0 }}>
                  {item.badges.slice(0, 2).map((badge, index) => (
                    <Tag
                      key={index}
                      color={badge.color}
                      style={{ margin: 0, fontSize: 11 }}
                    >
                      {badge.label}
                    </Tag>
                  ))}
                </Space>
              )}
            </div>
            <span
              style={{
                fontSize: 12,
                color: '#8c8c8c',
                whiteSpace: 'nowrap',
                flexShrink: 0,
              }}
            >
              {item.publishedLabel}
            </span>
          </div>

          {/* 2行目：本文スニペット（2行表示） */}
          <p
            style={{
              margin: 0,
              fontSize: 14,
              color: item.isUnread ? '#595959' : '#8c8c8c',
              lineHeight: '1.5',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {item.snippet}
          </p>
        </div>

        {/* 右側：誘導記号 */}
        <div style={{ paddingTop: 4 }}>
          <RightOutlined style={{ fontSize: 14, color: '#bfbfbf' }} />
        </div>
      </div>
    </Card>
  );
};
