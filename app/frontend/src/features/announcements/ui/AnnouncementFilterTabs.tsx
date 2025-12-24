/**
 * AnnouncementFilterTabs - お知らせフィルタタブUI
 * 
 * 「すべて」「未読」の切替タブ。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Segmented } from 'antd';
import type { AnnouncementFilterTab } from '../model/useAnnouncementsListViewModel';

interface AnnouncementFilterTabsProps {
  /** 選択中のタブ */
  selected: AnnouncementFilterTab;
  /** タブ変更コールバック */
  onChange: (tab: AnnouncementFilterTab) => void;
  /** 未読数（バッジ表示用） */
  unreadCount?: number;
}

export const AnnouncementFilterTabs: React.FC<AnnouncementFilterTabsProps> = ({
  selected,
  onChange,
  unreadCount = 0,
}) => {
  return (
    <Segmented
      value={selected}
      onChange={(value) => onChange(value as AnnouncementFilterTab)}
      options={[
        {
          label: 'すべて',
          value: 'all',
        },
        {
          label: `未読${unreadCount > 0 ? ` (${unreadCount})` : ''}`,
          value: 'unread',
        },
      ]}
      style={{ marginBottom: 16 }}
    />
  );
};
