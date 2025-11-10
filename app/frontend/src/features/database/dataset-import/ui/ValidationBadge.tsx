/**
 * ValidationBadge - バリデーション状態を表示する純UI部品
 */

import React from 'react';
import { Tag } from 'antd';
import type { ValidationStatus } from '../../shared/types/common';

export interface ValidationBadgeProps {
  status: ValidationStatus;
  /** サイズ: 'small' | 'default' */
  size?: 'small' | 'default';
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ status, size = 'default' }) => {
  const style = size === 'small' ? { fontSize: 11, padding: '0 4px', lineHeight: '18px' } : undefined;

  if (status === 'valid') {
    return <Tag color="green" style={style}>OK</Tag>;
  }
  if (status === 'invalid') {
    return <Tag color="red" style={style}>NG</Tag>;
  }
  return <Tag style={style}>未検証</Tag>;
};
