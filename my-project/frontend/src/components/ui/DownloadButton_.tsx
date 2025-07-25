// /components/ui/DownloadButton.tsx
import React from 'react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

type DownloadButtonProps = {
    pdfUrl: string;
};

const DownloadButton: React.FC<DownloadButtonProps> = ({ pdfUrl }) => {
    return (
        <Button
            icon={<DownloadOutlined />}
            type='primary'
            size='large'
            shape='round'
            href={pdfUrl}
            download
            style={{
                writingMode: 'vertical-rl',
                textOrientation: 'mixed',
                height: 160,
                fontSize: '1.2rem',
                border: 'none',
                borderRadius: '24px',
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                transform: 'scale(1)',
                cursor: 'pointer',
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.05)';
                e.currentTarget.style.boxShadow =
                    '0 6px 16px rgba(0, 0, 0, 0.2)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.boxShadow =
                    '0 4px 10px rgba(0, 0, 0, 0.1)';
            }}
        >
            ダウンロード
        </Button>
    );
};

export default DownloadButton;
