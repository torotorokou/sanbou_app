/**
 * ValidationBadge - バリデーション状態を表示する純UI部品
 */

import React from 'react';
import { Tag } from 'antd';
import type { ValidationStatus } from '../model/types';

export interface ValidationBadgeProps {
  status: ValidationStatus;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ status }) => {
  if (status === 'valid') {
    return <Tag color="green">OK</Tag>;
  }
  if (status === 'invalid') {
    return <Tag color="red">NG</Tag>;
  }
  return <Tag>未検証</Tag>;
};
