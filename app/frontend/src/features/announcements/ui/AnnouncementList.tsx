/**
 * AnnouncementList - お知らせ一覧UI
 * 
 * お知らせ一覧を表示するコンポーネント（カード型）。
 * ピン留めセクションと通常セクションに分けて表示。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Empty, Typography } from 'antd';
import type { AnnouncementDisplayItem } from '../model/useAnnouncementsListViewModel';
import { AnnouncementListItem } from './AnnouncementListItem';

const { Title } = Typography;

interface AnnouncementListProps {
  /** ピン留めアイテム */
  pinnedItems: AnnouncementDisplayItem[];
  /** 通常アイテム */
  normalItems: AnnouncementDisplayItem[];
  /** 詳細を開くコールバック */
  onOpen: (id: string) => void;
}

export const AnnouncementList: React.FC<AnnouncementListProps> = ({
  pinnedItems,
  normalItems,
  onOpen,
}) => {
  // 空状態
  if (pinnedItems.length === 0 && normalItems.length === 0) {
    return (
      <Empty
        description="お知らせはありません"
        style={{ padding: '40px 0' }}
      />
    );
  }

  return (
    <div>
      {/* ピン留めセクション */}
      {pinnedItems.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <Title level={5} style={{ marginBottom: 12, color: '#8c8c8c' }}>
            ピン留め
          </Title>
          {pinnedItems.map((item) => (
            <AnnouncementListItem key={item.id} item={item} onOpen={onOpen} />
          ))}
        </div>
      )}

      {/* すべてセクション */}
      {normalItems.length > 0 && (
        <div>
          <Title level={5} style={{ marginBottom: 12, color: '#8c8c8c' }}>
            すべて
          </Title>
          {normalItems.map((item) => (
            <AnnouncementListItem key={item.id} item={item} onOpen={onOpen} />
          ))}
        </div>
      )}
    </div>
  );
};

