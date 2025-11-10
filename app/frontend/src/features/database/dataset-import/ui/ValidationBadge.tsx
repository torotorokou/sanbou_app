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
  // バッジを見やすくするためにサイズ別のスタイルを明示的に指定
  const smallStyle = { fontSize: 13, padding: '0 6px', lineHeight: '20px' };
  const defaultStyle = { fontSize: 14, padding: '0 8px', lineHeight: '22px' };
  const style = size === 'small' ? smallStyle : defaultStyle;

  if (status === 'valid') {
    return <Tag color="green" style={style}>OK</Tag>;
  }
  if (status === 'invalid') {
    return <Tag color="red" style={style}>NG</Tag>;
  }
  return <Tag style={style}>未検証</Tag>;
};
