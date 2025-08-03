import React from 'react';
import { Typography } from 'antd';
import { useDeviceType } from '../../../hooks/ui';

type PDFViewerProps = {
    pdfUrl?: string | null;
    height?: string;
};

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl }) => {
    const { isMobile, isTablet } = useDeviceType();

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
                minHeight: isMobile ? '400px' : isTablet ? '450px' : '500px',
                border: 'none',
                borderRadius: 4,
            }}
            allowFullScreen
        />
    );
};

export default PDFViewer;
