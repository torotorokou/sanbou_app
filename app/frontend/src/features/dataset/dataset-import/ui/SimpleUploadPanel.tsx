/**
 * SimpleUploadPanel - シンプルなCSVアップロードパネル
 *
 * PanelFileItemを受け取り、ファイル選択UIを提供する純UI部品
 * 保守性向上のため UploadFileCard にカードロジックを分離
 */

import React from 'react';
import { Card, Button, Tooltip } from 'antd';
import { ClearOutlined } from '@ant-design/icons';
import type { PanelFileItem } from '../model/types';
import { UploadFileCard } from './UploadFileCard';

export interface SimpleUploadPanelProps {
  items: PanelFileItem[];
  onPickFile: (typeKey: string, file: File) => void;
  onRemoveFile: (typeKey: string) => void;
  onToggleSkip?: (typeKey: string) => void;
  onResetAll?: () => void;
  /** カードサイズ: 'compact' | 'normal'。既定は 'compact' */
  size?: 'compact' | 'normal';
  /** タイトルを表示するか（既定: false） */
  showTitle?: boolean;
}

export const SimpleUploadPanel: React.FC<SimpleUploadPanelProps> = ({
  items,
  onPickFile,
  onRemoveFile,
  onToggleSkip,
  onResetAll,
  size = 'compact',
  showTitle = false,
}) => {
  const isCompact = size === 'compact';
  const hasFiles = items.some((item) => item.file !== null);

  return (
    <Card
      size="small"
      title={showTitle ? '📂 CSVアップロード' : undefined}
      extra={
        onResetAll && hasFiles ? (
          <Tooltip title="すべてのCSVを削除">
            <Button
              type="text"
              size="small"
              icon={<ClearOutlined />}
              onClick={onResetAll}
              danger
              style={{ fontSize: 16 }}
            />
          </Tooltip>
        ) : null
      }
      styles={{
        header: showTitle
          ? {
              padding: isCompact ? '4px 8px' : '8px 12px',
              minHeight: isCompact ? 32 : 40,
              fontSize: isCompact ? 13 : 14,
            }
          : undefined,
        body: {
          padding: isCompact ? 8 : 12,
        },
      }}
      style={{
        borderRadius: isCompact ? 8 : 12,
        width: '100%',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: isCompact ? 6 : 12,
        }}
      >
        {items.map((item) => (
          <UploadFileCard
            key={item.typeKey}
            item={item}
            onPickFile={onPickFile}
            onRemoveFile={onRemoveFile}
            onToggleSkip={onToggleSkip}
            size={size}
          />
        ))}
      </div>
    </Card>
  );
};
