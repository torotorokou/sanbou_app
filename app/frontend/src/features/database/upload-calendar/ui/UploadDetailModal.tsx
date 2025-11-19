/**
 * アップロード詳細モーダル
 * 特定の日付のアップロード一覧を表示し、削除操作を提供
 */

import React, { useState } from 'react';
import { Modal, Table, Button, message, Space } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import type { UploadCalendarItem } from '../model/types';
import { getCsvUploadKindMaster } from '../model/types';

interface UploadDetailModalProps {
  date: string; // 'YYYY-MM-DD'
  uploads: UploadCalendarItem[];
  open: boolean;
  onClose: () => void;
  onDelete: (id: string) => Promise<void>;
}

export const UploadDetailModal: React.FC<UploadDetailModalProps> = ({
  date,
  uploads,
  open,
  onClose,
  onDelete,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string, fileName: string) => {
    const confirmed = window.confirm(`「${fileName}」を削除しますか？`);
    if (!confirmed) return;

    setDeletingId(id);
    try {
      await onDelete(id);
      message.success('削除しました');
      // 削除後、アップロードが0件になった場合はモーダルを閉じる
      if (uploads.length <= 1) {
        onClose();
      }
    } catch (error) {
      console.error('Failed to delete upload:', error);
      message.error('削除に失敗しました');
    } finally {
      setDeletingId(null);
    }
  };

  const columns = [
    {
      title: '種別',
      dataIndex: 'kind',
      key: 'kind',
      width: '30%',
      render: (kind: string) => {
        const master = getCsvUploadKindMaster(kind as UploadCalendarItem['kind']);
        return (
          <Space>
            <span
              style={{
                display: 'inline-block',
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: master?.color || '#d9d9d9',
              }}
            />
            <span>{master?.label || kind}</span>
          </Space>
        );
      },
    },
    {
      title: 'ファイル名',
      dataIndex: 'fileName',
      key: 'fileName',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: UploadCalendarItem) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          loading={deletingId === record.id}
          onClick={() => void handleDelete(record.id, record.fileName)}
        >
          削除
        </Button>
      ),
    },
  ];

  return (
    <Modal
      title={`${date} のアップロード一覧`}
      open={open}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      <Table
        dataSource={uploads}
        columns={columns}
        rowKey="id"
        pagination={false}
        size="small"
      />
    </Modal>
  );
};
