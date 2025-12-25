/**
 * DatasetFinalWarningModal - 将軍最終版データアップロード時の注意モーダル
 *
 * 全体会議で確定したCSVをアップロードする旨を確認するモーダル
 */

import React from 'react';
import { Modal, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

interface DatasetFinalWarningModalProps {
  open: boolean;
  onClose: () => void;
}

export const DatasetFinalWarningModal: React.FC<DatasetFinalWarningModalProps> = ({
  open,
  onClose,
}) => {
  return (
    <Modal
      open={open}
      onOk={onClose}
      onCancel={onClose}
      centered
      width={600}
      okText="確認しました"
      cancelButtonProps={{ style: { display: 'none' } }}
    >
      <div style={{ padding: '16px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <InfoCircleOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 12 }} />
          <Typography.Title level={5} style={{ margin: 0 }}>
            将軍最終版データのアップロードについて
          </Typography.Title>
        </div>
        <div style={{ lineHeight: 1.8 }}>
          <p style={{ marginBottom: 12 }}>
            ・全体会議で数字が確定した後、CSVファイルをアップロードしてください。
          </p>
          <p style={{ marginBottom: 0 }}>・月1回程度の更新を想定しています。</p>
        </div>
      </div>
    </Modal>
  );
};
