/**
 * SimpleUploadPanel - シンプルなCSVアップロードパネル
 * 
 * PanelFileItemを受け取り、ファイル選択UIを提供する純UI部品
 */

import React from 'react';
import { Card, Typography, Upload, Button } from 'antd';
import { UploadOutlined, DeleteOutlined } from '@ant-design/icons';
import type { PanelFileItem } from '../model/types';
import { ValidationBadge } from './ValidationBadge';

export interface SimpleUploadPanelProps {
  items: PanelFileItem[];
  onPickFile: (typeKey: string, file: File) => void;
  onRemoveFile: (typeKey: string) => void;
}

export const SimpleUploadPanel: React.FC<SimpleUploadPanelProps> = ({
  items,
  onPickFile,
  onRemoveFile,
}) => {
  return (
    <Card
      size="small"
      title={
        <Typography.Title level={5} style={{ margin: 0 }}>
          📂 CSVアップロード
        </Typography.Title>
      }
      style={{ borderRadius: 12, width: '100%' }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {items.map((item) => (
          <div
            key={item.typeKey}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto auto auto',
              alignItems: 'center',
              gap: 8,
              padding: '8px 0',
              borderBottom: '1px solid #f0f0f0',
            }}
          >
            <div>
              <Typography.Text strong>{item.label}</Typography.Text>
              {item.required && (
                <Typography.Text type="danger" style={{ marginLeft: 4 }}>
                  *
                </Typography.Text>
              )}
              {item.file && (
                <div style={{ fontSize: 12, color: '#888' }}>
                  {item.file.name}
                </div>
              )}
            </div>

            <ValidationBadge status={item.status} />

            <Upload
              accept=".csv"
              showUploadList={false}
              beforeUpload={(file) => {
                onPickFile(item.typeKey, file);
                return false;
              }}
            >
              <Button icon={<UploadOutlined />} size="small">
                選択
              </Button>
            </Upload>

            {item.file && (
              <Button
                icon={<DeleteOutlined />}
                size="small"
                danger
                onClick={() => onRemoveFile(item.typeKey)}
              >
                削除
              </Button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};
