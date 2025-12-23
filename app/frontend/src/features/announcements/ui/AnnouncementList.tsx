/**
 * AnnouncementList - お知らせ一覧UI
 * 
 * お知らせ一覧を表示するコンポーネント（カード型）。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Empty } from 'antd';
import type { AnnouncementDisplayItem } from '../model/useAnnouncementsListViewModel';
import { AnnouncementListItem } from './AnnouncementListItem';

interface AnnouncementListProps {
  /** 表示用に整形されたお知らせ一覧 */
  items: AnnouncementDisplayItem[];
  /** 詳細を開くコールバック */
  onOpen: (id: string) => void;
}

export const AnnouncementList: React.FC<AnnouncementListProps> = ({
  items,
  onOpen,
}) => {
  // 空状態
  if (items.length === 0) {
    return (
      <Empty
        description="お知らせはありません"
        style={{ padding: '40px 0' }}
      />
    );
  }

  return (
    <div>
      {items.map((item) => (
        <AnnouncementListItem key={item.id} item={item} onOpen={onOpen} />
      ))}
    </div>
  );
};

