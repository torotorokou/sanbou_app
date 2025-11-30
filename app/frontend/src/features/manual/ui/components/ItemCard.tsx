/**
 * ItemCard UI Component
 * 将軍マニュアルアイテムのカード表示（純粋UI）
 */
import React, { memo } from 'react';
import { Card, Space, Tag, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { ManualItem } from '../../domain/types/shogun.types';

const { Paragraph, Text } = Typography;

export interface ItemCardProps {
  item: ManualItem;
  onOpen: (item: ManualItem) => void;
  className?: string;
}

/* eslint-disable react/prop-types */
export const ItemCard: React.FC<ItemCardProps> = memo(({ item, onOpen, className }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    // routeプロパティがある場合は直接遷移、なければモーダルを開く
    if (item.route) {
      navigate(item.route);
    } else {
      onOpen(item);
    }
  };

  return (
    <Card
      size="small"
      className={className}
      hoverable
      onClick={handleClick}
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
  );
});
/* eslint-enable react/prop-types */

ItemCard.displayName = 'ItemCard';
