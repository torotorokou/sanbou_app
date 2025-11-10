/**
 * UploadFileCard - 単一のCSVファイルアップロードカード
 * SimpleUploadPanel から分離して保守性を向上
 */

import React from 'react';
import { Typography, Button } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import type { PanelFileItem } from '../model/types';
import { ValidationBadge } from './ValidationBadge';
import { DragDropCsv } from './DragDropCsv';

const { Text } = Typography;

export interface UploadFileCardProps {
  item: PanelFileItem;
  onPickFile: (typeKey: string, file: File) => void;
  onRemoveFile: (typeKey: string) => void;
  /** カードの高さモード: 'compact' | 'normal' */
  size?: 'compact' | 'normal';
}

export const UploadFileCard: React.FC<UploadFileCardProps> = ({
  item,
  onPickFile,
  onRemoveFile,
  size = 'compact',
}) => {
  const isCompact = size === 'compact';

  // ステータスに応じたカードの背景色・ボーダー色
  const statusStyles = {
    valid: { background: '#f6ffed', border: '1px solid #b7eb8f' },
    invalid: { background: '#fff2f0', border: '1px solid #ffccc7' },
    unknown: { background: '#fafafa', border: '1px solid #f0f0f0' },
  } as const;
  const currentStatus = item.status === 'valid' ? 'valid' : item.status === 'invalid' ? 'invalid' : 'unknown';
  const cardStyle = statusStyles[currentStatus];

  return (
    <div
      style={{
        padding: isCompact ? 6 : 12,
        borderRadius: 6,
        background: cardStyle.background,
        border: cardStyle.border,
      }}
    >
      {/* ヘッダー: ラベル + バッジ */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isCompact ? 6 : 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Text strong style={{ fontSize: isCompact ? 14 : 16 }}>
            {item.label}
          </Text>
          {item.required && (
            <Text type="danger" style={{ fontSize: isCompact ? 13 : 14 }}>
              *
            </Text>
          )}
        </div>
        <ValidationBadge status={item.status} size={isCompact ? 'small' : 'default'} />
      </div>

      {/* ファイル選択ボタン（ファイルがアップロードされていない場合のみ表示） */}
      {!item.file && (
        <DragDropCsv
          typeKey={item.typeKey}
          onPickFile={onPickFile}
          disabled={false}
          compact={isCompact}
        />
      )}

      {/* ファイル情報 + 削除ボタン */}
      {item.file && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginTop: isCompact ? 6 : 8,
          }}
        >
          <Text
            style={{
              flex: 1,
              fontSize: isCompact ? 11 : 12,
              color: '#666',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={item.file.name}
          >
            📄 {item.file.name}
          </Text>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => onRemoveFile(item.typeKey)}
            style={{
              height: isCompact ? 22 : 24,
              padding: isCompact ? '0 6px' : '0 8px',
              fontSize: isCompact ? 11 : 12,
            }}
          >
            削除
          </Button>
        </div>
      )}
    </div>
  );
};
