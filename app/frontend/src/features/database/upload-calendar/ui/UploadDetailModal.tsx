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
  onDelete: (params: {
    uploadFileId: number;
    date: string;
    csvKind: UploadCalendarItem['kind'];
  }) => Promise<void>;
}

export const UploadDetailModal: React.FC<UploadDetailModalProps> = ({
  date,
  uploads,
  open,
  onClose,
  onDelete,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (upload: UploadCalendarItem) => {
    const confirmed = window.confirm(`データ数: ${upload.rowCount.toLocaleString()}行 を削除しますか？`);
    if (!confirmed) return;

    if (!upload.uploadFileId) {
      message.error('uploadFileIdが見つかりません');
      return;
    }

    setDeletingId(upload.id);
    try {
      await onDelete({
        uploadFileId: upload.uploadFileId,
        date: upload.date,
        csvKind: upload.kind,
      });
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
      title: 'カテゴリ',
      dataIndex: 'kind',
      key: 'category',
      width: '25%',
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
            <span>{master?.category || kind}</span>
          </Space>
        );
      },
    },
    {
      title: 'CSV種別',
      dataIndex: 'kind',
      key: 'kind',
      width: '25%',
      render: (kind: string) => {
        const master = getCsvUploadKindMaster(kind as UploadCalendarItem['kind']);
        // ラベルから「将軍速報版 」などのプレフィックスを除いた部分を表示
        const label = master?.label || kind;
        const parts = label.split(' ');
        return parts.length > 1 ? parts.slice(1).join(' ') : label;
      },
    },
    {
      title: 'データ数',
      dataIndex: 'rowCount',
      key: 'rowCount',
      width: '25%',
      render: (count: number) => `${count.toLocaleString()}行`,
    },
    {
      title: '操作',
      key: 'action',
      width: '25%',
      render: (_: unknown, record: UploadCalendarItem) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          loading={deletingId === record.id}
          onClick={() => void handleDelete(record)}
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
