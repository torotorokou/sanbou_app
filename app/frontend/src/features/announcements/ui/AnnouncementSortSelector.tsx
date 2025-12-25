/**
 * AnnouncementSortSelector - お知らせソート選択UI
 *
 * ソート順を選択するセレクター。
 * 状態レス：propsのみで動作。
 */

import React from 'react';
import { Select, Space } from 'antd';
import { SortAscendingOutlined } from '@ant-design/icons';
import type { AnnouncementSortType } from '../model/useAnnouncementsListViewModel';

interface AnnouncementSortSelectorProps {
  /** 選択中のソート種類 */
  selected: AnnouncementSortType;
  /** ソート変更コールバック */
  onChange: (sort: AnnouncementSortType) => void;
  /** モバイルモード */
  isMobile?: boolean;
}

export const AnnouncementSortSelector: React.FC<AnnouncementSortSelectorProps> = ({
  selected,
  onChange,
  isMobile = false,
}) => {
  return (
    <Space size={8} style={{ marginBottom: 16 }}>
      <SortAscendingOutlined style={{ color: '#8c8c8c', fontSize: isMobile ? 14 : 16 }} />
      <Select
        value={selected}
        onChange={onChange}
        size={isMobile ? 'small' : 'middle'}
        style={{ width: isMobile ? 140 : 160 }}
        options={[
          { label: '新しい順', value: 'date-desc' },
          { label: '古い順', value: 'date-asc' },
          { label: '重要度順', value: 'severity' },
        ]}
      />
    </Space>
  );
};
