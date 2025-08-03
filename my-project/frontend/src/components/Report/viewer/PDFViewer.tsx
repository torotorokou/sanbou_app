import React from 'react';
import { Typography } from 'antd';

type PDFViewerProps = {
    pdfUrl?: string | null;
    height?: string;
};

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, height = '100%' }) => {
    if (!pdfUrl) {
        return (
            <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '400px'
            }}>
                <Typography.Text type='secondary'>
                    帳簿を作成するとここにPDFが表示されます。
                </Typography.Text>
            </div>
        );
    }

    return (
        <iframe
            title='PDFプレビュー'
            src={pdfUrl}
            style={{
                width: '100%',
                height: '100%',
                minHeight: '500px',
                border: 'none',
                borderRadius: 4,
            }}
            allowFullScreen
        />
    );
};

export default PDFViewer;
