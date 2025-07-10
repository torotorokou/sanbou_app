// src/components/chat/PdfPreviewModal.tsx
import React from 'react';
import { Modal, Empty } from 'antd';

type Props = {
    visible: boolean;
    onClose: () => void;
    pdfUrl: string;
};

const PdfPreviewModal: React.FC<Props> = ({ visible, onClose, pdfUrl }) => {
    return (
        <Modal
            open={visible}
            onCancel={onClose}
            footer={null}
            title='📄 PDFプレビュー'
            width='80%'
            styles={{
                body: {
                    height: '80vh',
                    padding: 0,
                    overflow: 'hidden',
                },
            }}
        >
            {pdfUrl ? (
                <iframe
                    key={pdfUrl}
                    src={pdfUrl}
                    title='PDF Preview'
                    width='100%'
                    height='100%'
                    style={{ border: 'none', display: 'block' }}
                />
            ) : (
                <Empty description='PDFが読み込まれていません' />
            )}
        </Modal>
    );
};

export default PdfPreviewModal;
