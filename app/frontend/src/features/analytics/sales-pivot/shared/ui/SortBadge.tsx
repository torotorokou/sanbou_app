/**
 * shared/ui/SortBadge.tsx
 * ソートバッジコンポーネント
 */

import React from 'react';
import { Badge, Tag } from 'antd';
import { ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons';
import type { SortKey, SortOrder } from '../model/types';

export interface SortBadgeProps {
  label: string;
  keyName: SortKey;
  order: SortOrder;
}

/**
 * ソート状態を表示するバッジ
 */
export const SortBadge: React.FC<SortBadgeProps> = ({ label, keyName, order }) => (
  <Badge
    count={order === 'desc' ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
    style={{ backgroundColor: '#237804' }}
  >
    <Tag style={{ marginRight: 8 }}>
      {label}: {keyName}
    </Tag>
  </Badge>
);
