/**
 * ReportUploadFileCard - レポート用のCSVファイルアップロードカード（カード全体クリック対応）
 * dataset-import/UploadFileCard のデザインをベースに、スキップ機能を除外
 * ファイル未選択時はカード全体がクリック可能エリアとなり、キーボード操作にも対応
 */

import React, { useRef } from 'react';
import { Typography, Button } from 'antd';
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { RcFile } from 'antd/es/upload';
import { CsvValidationBadge, mapLegacyToCsvStatus } from '@features/csv-validation';

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
  const fileInputRef = useRef<HTMLInputElement>(null);

  // レガシーステータスをCSVバリデーションステータスに変換
  const csvStatus = mapLegacyToCsvStatus(validationResult);

  // ステータスに応じたカードの背景色・ボーダー色
  const statusStyles = {
    valid: { background: '#f6ffed', border: '1px solid #b7eb8f' },
    invalid: { background: '#fff2f0', border: '1px solid #ffccc7' },
    unknown: { background: '#fafafa', border: '1px solid #f0f0f0' },
  } as const;
  const cardStyle = statusStyles[csvStatus];

  const handleClick = () => {
    if (!file) {
      fileInputRef.current?.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!file && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && uploadProps.beforeUpload) {
      // beforeUpload に File オブジェクトをそのまま渡す
      // antd の Upload コンポーネントは内部的に File を RcFile として扱える
      // RcFile に必要なプロパティを追加（読み取り専用プロパティを避けて新しいオブジェクトを作成）
      const rcFile = new File([selectedFile], selectedFile.name, {
        type: selectedFile.type,
        lastModified: selectedFile.lastModified,
      }) as RcFile;
      rcFile.uid = selectedFile.name + Date.now();
      uploadProps.beforeUpload(rcFile, [rcFile]);
      // input をリセットして同じファイルを再選択可能に
      e.target.value = '';
    }
  };

  return (
    <div
      role={!file ? 'button' : undefined}
      tabIndex={!file ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      style={{
        padding: isCompact ? 6 : 12,
        borderRadius: 6,
        background: cardStyle.background,
        border: cardStyle.border,
        cursor: !file ? 'pointer' : 'default',
        transition: 'background-color 0.2s, border-color 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!file) {
          const current = e.currentTarget;
          if (csvStatus === 'valid') {
            current.style.backgroundColor = '#f0ffe6';
            current.style.borderColor = '#95de64';
          } else if (csvStatus === 'invalid') {
            current.style.backgroundColor = '#ffe7e6';
            current.style.borderColor = '#ff9c99';
          } else {
            current.style.backgroundColor = '#f0f0f0';
            current.style.borderColor = '#d9d9d9';
          }
        }
      }}
      onMouseLeave={(e) => {
        if (!file) {
          e.currentTarget.style.backgroundColor = cardStyle.background;
          e.currentTarget.style.borderColor = cardStyle.border.split(' ')[2];
        }
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
        <CsvValidationBadge status={csvStatus} size={isCompact ? 'small' : 'default'} />
      </div>

      {/* バリデーションエラーメッセージ */}
      {csvStatus === 'invalid' && errorMessage && (
        <div style={{ marginBottom: isCompact ? 6 : 8 }}>
          <Text type="danger" style={{ fontSize: isCompact ? 11 : 12 }}>
            ⚠️ {errorMessage}
          </Text>
        </div>
      )}

      {/* ファイル選択エリア（ファイルがアップロードされていない場合のみ表示） */}
      {!file && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            accept={uploadProps.accept || '.csv'}
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: isCompact ? '12px 8px' : '16px 12px',
              borderRadius: 4,
              border: '1px dashed #d9d9d9',
              backgroundColor: '#fafafa',
            }}
          >
            <UploadOutlined
              style={{
                fontSize: isCompact ? 20 : 24,
                color: '#1890ff',
                marginBottom: 4,
              }}
            />
            <div
              style={{
                fontSize: isCompact ? 12 : 13,
                color: '#666',
                textAlign: 'center',
              }}
            >
              ここをクリックして CSV をアップロード
            </div>
          </div>
        </>
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
