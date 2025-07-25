import React from 'react';
import { Typography } from 'antd';

type PDFViewerProps = {
    pdfUrl?: string | null;
    height?: string;
};

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, height = '80vh' }) => {
    if (!pdfUrl) {
        return (
            <Typography.Text type='secondary'>
                帳簿を作成するとここにPDFが表示されます。
            </Typography.Text>
        );
    }

    return (
        <iframe
            title='PDFプレビュー'
            src={pdfUrl}
            style={{
                width: '100%',
                height: '100%',
                border: '1px solid #ccc',
                borderRadius: 4,
            }}
            allowFullScreen
        />
    );
};

export default PDFViewer;
