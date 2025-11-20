import React from 'react';
import { Modal, Spin } from 'antd';

type Props = {
    open: boolean;
};

const AnalysisProcessingModal: React.FC<Props> = ({ open }) => (
    <Modal
        open={open}
        footer={null}
        closable={false}
        maskClosable={false}
        centered
        zIndex={3000}
        styles={{ body: { textAlign: 'center', padding: '48px 24px' } }}
    >
        <Spin size='large' style={{ marginBottom: 16 }} />
        <div style={{ fontWeight: 600, fontSize: 18, marginTop: 12 }}>
            分析中です…
        </div>
        <div style={{ color: '#888', marginTop: 8 }}>
            データを比較しています。しばらくお待ちください。
        </div>
    </Modal>
);

export default AnalysisProcessingModal;
