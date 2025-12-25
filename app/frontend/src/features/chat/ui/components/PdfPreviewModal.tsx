// src/components/chat/PdfPreviewModal.tsx
import React from 'react';
import { Modal, Empty } from 'antd';
import { ensurePdfJsWorkerLoaded, useResponsive, ANT } from '@/shared';

type Props = {
  visible: boolean;
  onClose: () => void;
  pdfUrl: string;
};

const PdfPreviewModal: React.FC<Props> = ({ visible, onClose, pdfUrl }) => {
  const { width } = useResponsive();
  // ANT.xl 未満では高さを大きめにして、下部の余白を埋める
  const bodyHeight = width < ANT.xl ? '95vh' : '80vh';

  React.useEffect(() => {
    if (!visible) return;
    // 遅延でpdf.jsワーカーを読み込む（必要なときだけ）
    ensurePdfJsWorkerLoaded().catch(() => {
      // 失敗しても iframe 表示には影響しないため握りつぶす
    });
  }, [visible]);

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      title="📄 PDFプレビュー"
      width="80%"
      styles={{
        body: {
          height: bodyHeight,
          padding: 0,
          overflow: 'hidden',
        },
      }}
    >
      {pdfUrl ? (
        <iframe
          key={pdfUrl}
          src={pdfUrl}
          title="PDF Preview"
          width="100%"
          height="100%"
          style={{ border: 'none', display: 'block' }}
        />
      ) : (
        <Empty description="PDFが読み込まれていません" />
      )}
    </Modal>
  );
};

export default PdfPreviewModal;
