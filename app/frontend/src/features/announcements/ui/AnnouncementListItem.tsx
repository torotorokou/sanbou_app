/**
 * AnnouncementListItem - お知らせアイテムUI（カード型）
 * 
 * プロフェッショナルな見た目のカード型アイテム。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Card, Tag, Space } from 'antd';
import { RightOutlined, PaperClipOutlined } from '@ant-design/icons';
import type { AnnouncementDisplayItem } from '../model/useAnnouncementsListViewModel';

interface AnnouncementListItemProps {
  /** 表示用に整形されたアイテム */
  item: AnnouncementDisplayItem;
  /** クリックコールバック */
  onOpen: (id: string) => void;
  /** モバイルモード（スニペットを短くする） */
  isMobile?: boolean;
}

export const AnnouncementListItem: React.FC<AnnouncementListItemProps> = ({
  item,
  onOpen,
  isMobile = false,
}) => {
  // 重要度に応じた色を取得
  const getSeverityColors = () => {
    switch (item.severity) {
      case 'critical':
        return {
          bgColor: item.isUnread ? '#fff1f0' : '#fafafa', // 薄赤
          borderColor: '#ff4d4f', // 赤
          dotColor: '#ff4d4f',
        };
      case 'warn':
        return {
          bgColor: item.isUnread ? '#fff7e6' : '#fafafa', // 薄オレンジ
          borderColor: '#fa8c16', // オレンジ
          dotColor: '#fa8c16',
        };
      case 'info':
      default:
        return {
          bgColor: item.isUnread ? '#e6f7ff' : '#fafafa', // 薄青
          borderColor: '#1890ff', // 青
          dotColor: '#1890ff',
        };
    }
  };

  const colors = getSeverityColors();
  
  return (
    <Card
      onClick={() => onOpen(item.id)}
      style={{
        marginBottom: 8,
        borderRadius: 8,
        cursor: 'pointer',
        backgroundColor: colors.bgColor,
        borderLeft: item.isUnread ? `4px solid ${colors.borderColor}` : '4px solid transparent',
        transition: 'all 0.2s',
      }}
      styles={{
        body: {
          padding: isMobile ? '12px 16px' : '16px 20px',
          backgroundColor: colors.bgColor,
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
                backgroundColor: colors.dotColor,
              }}
            />
          )}
        </div>

        {/* 中央：コンテンツ */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {isMobile ? (
            // モバイル：タイトルと日付を2行に分ける
            <>
              <h4
                style={{
                  margin: 0,
                  marginBottom: 6,
                  fontSize: 14,
                  fontWeight: item.isUnread ? 700 : 600,
                  color: item.isUnread ? '#262626' : '#404040',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  letterSpacing: '0.2px',
                }}
              >
                {item.title}
              </h4>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontSize: 11,
                    color: '#8c8c8c',
                  }}
                >
                  {item.publishedLabel}
                </span>
                {item.hasAttachments && (
                  <PaperClipOutlined style={{ fontSize: 12, color: '#8c8c8c' }} />
                )}
              </div>
            </>
          ) : (
            // デスクトップ：既存のレイアウト（タイトル + バッジ + タグ + 添付 + 公開日を1行）
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
                    fontSize: 17,
                    fontWeight: item.isUnread ? 700 : 600,
                    color: item.isUnread ? '#262626' : '#404040',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    flex: '0 1 auto',
                    letterSpacing: '0.3px',
                  }}
                >
                  {item.title}
                </h4>
                {/* 重要度バッジ */}
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
                {/* タグ（最大3個） */}
                {item.tags.length > 0 && (
                  <Space size={4} style={{ flexShrink: 0 }}>
                    {item.tags.map((tag, index) => (
                      <Tag
                        key={`tag-${index}`}
                        style={{ margin: 0, fontSize: 10, backgroundColor: '#f0f0f0', borderColor: '#d9d9d9' }}
                      >
                        {tag}
                      </Tag>
                    ))}
                  </Space>
                )}
                {/* 添付ありバッジ */}
                {item.hasAttachments && (
                  <Tag
                    icon={<PaperClipOutlined />}
                    style={{ margin: 0, fontSize: 10, backgroundColor: '#e6f7ff', borderColor: '#91d5ff' }}
                  >
                    添付
                  </Tag>
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
          )}

          {/* 2行目：本文スニペット */}
          <p
            style={{
              margin: 0,
              fontSize: isMobile ? 13 : 14,
              color: item.isUnread ? '#595959' : '#8c8c8c',
              lineHeight: '1.5',
              display: '-webkit-box',
              WebkitLineClamp: isMobile ? 1 : 2,
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
