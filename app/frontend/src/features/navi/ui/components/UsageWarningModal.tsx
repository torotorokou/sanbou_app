import React from 'react';
import { Modal, Button } from 'antd';

interface UsageWarningModalProps {
  open: boolean;
  onAgree: () => void;
  onCancel: () => void;
}

export const UsageWarningModal: React.FC<UsageWarningModalProps> = ({
  open,
  onAgree,
  onCancel,
}) => {
  return (
    <Modal
      title="ご利用上の注意"
      open={open}
      onCancel={onCancel}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button key="back" onClick={onCancel}>
            戻る
          </Button>
          <Button key="submit" type="primary" onClick={onAgree}>
            同意して進む
          </Button>
        </div>
      }
      closable={false}
      maskClosable={false}
      centered
    >
      <p>この機能はAIモデルを使用するため、従量課金が発生します。</p>
      <p>業務目的以外での使用は控え、必要な場合のみご利用ください。</p>
      <p>よろしければ「同意して進む」を押してください。</p>
    </Modal>
  );
};
