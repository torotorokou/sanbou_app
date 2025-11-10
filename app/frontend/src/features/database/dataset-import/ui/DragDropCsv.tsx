/**
 * FileSelectButton - ファイル選択ボタンCSVファイル選択コンポーネント
 * 
 * Upload ボタンを使用し、beforeUpload で既存の onPickFile に合流させる。
 * 自動アップロードは無効化（return false）。
 */

import React from 'react';
import { Upload, Button } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

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
    <div style={{ display: 'flex', justifyContent: 'center', padding: compact ? '8px 0' : '12px 0' }}>
      <Upload
        disabled={disabled}
        accept=".csv"
        multiple={false}
        showUploadList={false}
        beforeUpload={(file) => {
          onPickFile(typeKey, file as File);
          return false; // AntDの自動アップロードを無効化
        }}
      >
        <Button
          icon={<UploadOutlined />}
          disabled={disabled}
          size={compact ? 'small' : 'middle'}
          style={{
            height: compact ? 32 : 40,
            minWidth: compact ? 150 : 180,
          }}
        >
          CSVファイルを選択
        </Button>
      </Upload>
    </div>
  );
};
