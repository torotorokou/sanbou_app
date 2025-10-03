import React, { useEffect, useState } from 'react';
import { Typography, Alert } from 'antd';
import { useWindowSize } from '@shared/hooks/ui';
import { ensurePdfJsWorkerLoaded } from '@shared/utils/pdfWorkerLoader';

type PDFViewerProps = {
    pdfUrl?: string | null;
    height?: string;
};

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, height }) => {
    const { isMobile } = useWindowSize();
    const [hasError, setHasError] = useState(false);

    useEffect(() => {
        if (!pdfUrl) return;
        ensurePdfJsWorkerLoaded().catch(() => void 0);
    }, [pdfUrl]);

    if (!pdfUrl) {
        return (
            <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: isMobile ? '300px' : '400px',
                padding: isMobile ? '12px' : '16px',
            }}>
                <Typography.Text
                    type='secondary'
                    style={{
                        textAlign: 'center',
                        fontSize: isMobile ? '14px' : '16px',
                    }}
                >
                    レポートを生成するとここにPDFが表示されます。
                </Typography.Text>
            </div>
        );
    }

    if (hasError) {
        return (
            <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: isMobile ? '300px' : '400px',
                padding: isMobile ? '12px' : '16px',
            }}>
                <Alert
                    message="PDFの表示エラー"
                    description="PDFの表示に失敗しました。ブラウザを更新するか、印刷ボタンから直接印刷してください。"
                    type="warning"
                    showIcon
                />
            </div>
        );
    }

    const minHeightToUse = height ?? '0px';

    return (
        <iframe
            title='PDFプレビュー'
            src={`${pdfUrl}#toolbar=1&navpanes=0&scrollbar=1`}
            style={{ width: '100%', height: '100%', minHeight: minHeightToUse, border: 'none', borderRadius: 4 }}
            allowFullScreen
            onError={() => setHasError(true)}
        />
    );
};

export default PDFViewer;
