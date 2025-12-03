/**
 * components/CategorySelector.tsx
 * 種別選択コンポーネント（廃棄物/有価物）
 * 
 * 責務:
 * - 廃棄物/有価物の切り替えUIを提供
 * - レスポンシブ対応のボタンスタイル
 */

import React from 'react';
import { Space, Typography, Radio } from 'antd';
import type { CategoryKind } from '../../../shared/model/types';
import styles from './CategorySelector.module.css';

interface CategorySelectorProps {
  value: CategoryKind;
  onChange: (kind: CategoryKind) => void;
}

/**
 * 種別選択コンポーネント
 */
export const CategorySelector: React.FC<CategorySelectorProps> = ({
  value,
  onChange,
}) => (
  <Space direction="vertical" size={2} className={styles.container}>
    <Typography.Text type="secondary">種別</Typography.Text>
    <Radio.Group
      value={value}
      onChange={(e) => onChange(e.target.value as CategoryKind)}
      buttonStyle="solid"
      className={styles.radioGroup}
    >
      <Radio.Button value="waste">廃棄物</Radio.Button>
      <Radio.Button value="valuable">有価物</Radio.Button>
    </Radio.Group>
  </Space>
);
