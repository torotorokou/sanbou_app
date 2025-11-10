/**
 * DragDropCsv - ドラッグ&ドロップ対応CSVファイル選択コンポーネント
 * 
 * Upload.Dragger を使用し、beforeUpload で既存の onPickFile に合流させる。
 * 自動アップロードは無効化（return false + customRequest 空実装）。
 */

import React from 'react';
import { Upload, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

export interface DragDropCsvProps {
  typeKey: string;
  disabled?: boolean;
  onPickFile: (typeKey: string, file: File) => void;
  /** コンパクト表示 */
  compact?: boolean;
}

export const DragDropCsv: React.FC<DragDropCsvProps> = ({
  typeKey,
  disabled,
  onPickFile,
  compact = false,
}) => {
  return (
    <Dragger
      disabled={disabled}
      accept=".csv"
      multiple={false}
      showUploadList={false}
      beforeUpload={(file) => {
        onPickFile(typeKey, file as File);
        return false; // AntDの自動アップロードを無効化
      }}
      customRequest={() => {
        /* no-op: 実際のアップロードは行わない */
      }}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      style={{
        borderRadius: compact ? 4 : 8,
        padding: compact ? '8px 8px' : '16px 12px',
        background: '#fafafa',
        border: '1px dashed #d9d9d9',
      }}
    >
      <p className="ant-upload-drag-icon" style={{ marginBottom: compact ? 4 : 8 }}>
        <InboxOutlined style={{ fontSize: compact ? 24 : 32, color: '#1890ff' }} />
      </p>
      <Typography.Text type="secondary" style={{ fontSize: compact ? 11 : 13 }}>
        ここに <strong>CSV</strong> をドラッグ&ドロップ / クリックして選択
      </Typography.Text>
    </Dragger>
  );
};
