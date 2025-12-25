/**
 * shared/ui/EmptyStateCard.tsx
 * 空状態カードコンポーネント
 */

import React from 'react';
import { Card, Typography } from 'antd';

export interface EmptyStateCardProps {
  message: string;
  className?: string;
}

/**
 * 空状態を表示するカード
 */
export const EmptyStateCard: React.FC<EmptyStateCardProps> = ({ message, className }) => (
  <Card className={className}>
    <div style={{ padding: 12 }}>
      <Typography.Text type="secondary">{message}</Typography.Text>
    </div>
  </Card>
);
