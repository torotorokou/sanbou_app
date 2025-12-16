/**
 * UploadFileCard - 単一のCSVファイルアップロードカード
 * SimpleUploadPanel から分離して保守性を向上
 */

import React from 'react';
import { Typography, Button, Checkbox } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import type { PanelFileItem } from '../model/types';
import { CsvValidationBadge } from '@features/csv-validation';
import { DragDropCsv } from './DragDropCsv';

const { Text } = Typography;

export interface UploadFileCardProps {
  item: PanelFileItem;
  onPickFile: (typeKey: string, file: File) => void;
  onRemoveFile: (typeKey: string) => void;
  onToggleSkip?: (typeKey: string) => void;
  /** カードの高さモード: 'compact' | 'normal' */
  size?: 'compact' | 'normal';
}

export const UploadFileCard: React.FC<UploadFileCardProps> = ({
  item,
  onPickFile,
  onRemoveFile,
  onToggleSkip,
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
      {/* ヘッダー: チェックボックス + ラベル + バッジ */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isCompact ? 6 : 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {onToggleSkip && (
            <Checkbox
              checked={item.skipped}
              onChange={() => onToggleSkip(item.typeKey)}
              style={{ marginTop: 2 }}
            >
              スキップ
            </Checkbox>
          )}
          <Text strong style={{ fontSize: isCompact ? 14 : 16, textDecoration: item.skipped ? 'line-through' : 'none', opacity: item.skipped ? 0.5 : 1 }}>
            {item.label}
          </Text>
          {item.required && (
            <Text type="danger" style={{ fontSize: isCompact ? 13 : 14 }}>
              *
            </Text>
          )}
        </div>
        <CsvValidationBadge status={item.status} size={isCompact ? 'small' : 'default'} />
      </div>

      {/* ファイル選択ボタン（ファイルがアップロードされていない場合かつスキップされていない場合のみ表示） */}
      {!item.file && !item.skipped && (
        <DragDropCsv
          typeKey={item.typeKey}
          onPickFile={onPickFile}
          disabled={false}
          compact={isCompact}
        />
      )}
      
      {/* スキップ中の表示 */}
      {item.skipped && !item.file && (
        <div style={{ padding: '8px 12px', textAlign: 'center', color: '#999', fontSize: isCompact ? 12 : 13 }}>
          ⏭️ このCSVはアップロードしません
        </div>
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
