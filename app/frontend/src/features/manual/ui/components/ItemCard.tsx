/**
 * ItemCard UI Component
 * 将軍マニュアルアイテムのカード表示（純粋UI）
 */
import React, { memo } from 'react';
import { Card, Space, Tag, Typography } from 'antd';
import type { ManualItem } from '../../domain/types/shogun.types';

const { Paragraph, Text } = Typography;

export interface ItemCardProps {
  item: ManualItem;
  onOpen: (item: ManualItem) => void;
  className?: string;
}

/* eslint-disable react/prop-types */
export const ItemCard: React.FC<ItemCardProps> = memo(({ item, onOpen, className }) => (
  <Card
    size="small"
    className={className}
    hoverable
    onClick={() => onOpen(item)}
    title={<Text strong>{item.title}</Text>}
  >
    <Space direction="vertical" size={8} style={{ width: '100%' }}>
      <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
        {item.description ?? '説明は未設定です。'}
      </Paragraph>
      <Space size={[4, 4]} wrap>
        {(item.tags ?? []).map((t: string) => (
          <Tag key={t}>{t}</Tag>
        ))}
      </Space>
    </Space>
  </Card>
));
/* eslint-enable react/prop-types */

ItemCard.displayName = 'ItemCard';
