import React from 'react';
import { Typography } from 'antd';

type PDFViewerProps = {
    pdfUrl?: string | null;
    height?: string; // オプションで高さを調整できる
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
            src={pdfUrl}
            style={{
                width: '100%',
                height,
                border: '1px solid #ccc',
                borderRadius: 4,
            }}
        />
    );
};

export default PDFViewer;
