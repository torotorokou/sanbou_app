/**
 * SimpleUploadPanel - シンプルなCSVアップロードパネル
 * 
 * PanelFileItemを受け取り、ファイル選択UIを提供する純UI部品
 * 保守性向上のため UploadFileCard にカードロジックを分離
 */

import React from 'react';
import { Card } from 'antd';
import type { PanelFileItem } from '../model/types';
import { UploadFileCard } from './UploadFileCard';

export interface SimpleUploadPanelProps {
  items: PanelFileItem[];
  onPickFile: (typeKey: string, file: File) => void;
  onRemoveFile: (typeKey: string) => void;
  /** カードサイズ: 'compact' | 'normal'。既定は 'compact' */
  size?: 'compact' | 'normal';
  /** タイトルを表示するか（既定: false） */
  showTitle?: boolean;
}

export const SimpleUploadPanel: React.FC<SimpleUploadPanelProps> = ({
  items,
  onPickFile,
  onRemoveFile,
  size = 'compact',
  showTitle = false,
}) => {
  const isCompact = size === 'compact';

  return (
    <Card
      size="small"
      title={showTitle ? '📂 CSVアップロード' : undefined}
      headStyle={
        showTitle
          ? {
              padding: isCompact ? '4px 8px' : '8px 12px',
              minHeight: isCompact ? 32 : 40,
              fontSize: isCompact ? 13 : 14,
            }
          : undefined
      }
      bodyStyle={{
        padding: isCompact ? 8 : 12,
      }}
      style={{
        borderRadius: isCompact ? 8 : 12,
        width: '100%',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: isCompact ? 6 : 12 }}>
        {items.map((item) => (
          <UploadFileCard
            key={item.typeKey}
            item={item}
            onPickFile={onPickFile}
            onRemoveFile={onRemoveFile}
            size={size}
          />
        ))}
      </div>
    </Card>
  );
};
