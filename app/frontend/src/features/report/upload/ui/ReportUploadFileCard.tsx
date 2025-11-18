/**
 * ReportUploadFileCard - レポート用のCSVファイルアップロードカード
 * dataset-import/UploadFileCard のデザインをベースに、スキップ機能を除外
 */

import React from 'react';
import { Typography, Button, Upload } from 'antd';
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Text } = Typography;

export interface ReportUploadFileCardProps {
  label: string;
  file: File | null;
  required: boolean;
  validationResult?: 'ok' | 'ng' | 'unknown';
  onRemove: () => void;
  uploadProps: UploadProps;
  /** カードの高さモード: 'compact' | 'normal' */
  size?: 'compact' | 'normal';
  /** バリデーションエラーメッセージ（オプション） */
  errorMessage?: string;
}

/**
 * ValidationBadge - バリデーション状態を表示
 */
const ValidationBadge: React.FC<{ status: 'ok' | 'ng' | 'unknown'; size?: 'small' | 'default' }> = ({ 
  status, 
  size = 'default' 
}) => {
  const smallStyle = { fontSize: 13, padding: '0 6px', lineHeight: '20px', display: 'inline-block' };
  const defaultStyle = { fontSize: 14, padding: '0 8px', lineHeight: '22px', display: 'inline-block' };
  const style = size === 'small' ? smallStyle : defaultStyle;

  if (status === 'ok') {
    return <span style={{ ...style, backgroundColor: '#f6ffed', color: '#52c41a', border: '1px solid #b7eb8f', borderRadius: 4 }}>OK</span>;
  }
  if (status === 'ng') {
    return <span style={{ ...style, backgroundColor: '#fff2f0', color: '#ff4d4f', border: '1px solid #ffccc7', borderRadius: 4 }}>NG</span>;
  }
  return <span style={{ ...style, backgroundColor: '#fafafa', color: '#666', border: '1px solid #d9d9d9', borderRadius: 4 }}>未検証</span>;
};

export const ReportUploadFileCard: React.FC<ReportUploadFileCardProps> = ({
  label,
  file,
  required,
  validationResult = 'unknown',
  onRemove,
  uploadProps,
  size = 'compact',
  errorMessage,
}) => {
  const isCompact = size === 'compact';

  // ステータスに応じたカードの背景色・ボーダー色
  const statusStyles = {
    ok: { background: '#f6ffed', border: '1px solid #b7eb8f' },
    ng: { background: '#fff2f0', border: '1px solid #ffccc7' },
    unknown: { background: '#fafafa', border: '1px solid #f0f0f0' },
  } as const;
  const currentStatus = validationResult === 'ok' ? 'ok' : validationResult === 'ng' ? 'ng' : 'unknown';
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Text strong style={{ fontSize: isCompact ? 14 : 16 }}>
            {label}
          </Text>
          {required && (
            <Text type="danger" style={{ fontSize: isCompact ? 13 : 14 }}>
              *
            </Text>
          )}
        </div>
        <ValidationBadge status={currentStatus} size={isCompact ? 'small' : 'default'} />
      </div>

      {/* バリデーションエラーメッセージ */}
      {validationResult === 'ng' && errorMessage && (
        <div style={{ marginBottom: isCompact ? 6 : 8 }}>
          <Text type="danger" style={{ fontSize: isCompact ? 11 : 12 }}>
            ⚠️ {errorMessage}
          </Text>
        </div>
      )}

      {/* ファイル選択ボタン（ファイルがアップロードされていない場合のみ表示） */}
      {!file && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: isCompact ? '8px 0' : '12px 0' }}>
          <Upload {...uploadProps}>
            <Button
              icon={<UploadOutlined />}
              size={isCompact ? 'small' : 'middle'}
              style={{
                height: isCompact ? 32 : 40,
                minWidth: isCompact ? 150 : 180,
              }}
            >
              CSVファイルを選択
            </Button>
          </Upload>
        </div>
      )}

      {/* ファイル情報 + 削除ボタン */}
      {file && (
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
            title={file.name}
          >
            📄 {file.name}
          </Text>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={onRemove}
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
