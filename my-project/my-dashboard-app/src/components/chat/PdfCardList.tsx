// src/components/chat/PdfCardList.tsx
import React from 'react';
import { Card, Typography, Empty } from 'antd';

type PdfSource = {
    pdf: string;
    section_title: string;
};

type Props = {
    sources: PdfSource[];
    onOpen: (pdfPath: string) => void;
};

const PdfCardList: React.FC<Props> = ({ sources, onOpen }) => {
    if (!sources || sources.length === 0) {
        return <Empty description='参照されたPDFはありません' />;
    }

    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 12,
                marginTop: 8,
            }}
        >
            {sources.map((src, idx) => (
                <div
                    key={idx}
                    style={{
                        width: '100%',
                        cursor: 'pointer',
                        padding: 12,
                        border: '1px solid #eee',
                        borderRadius: 8,
                        background: '#fff',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                        transition: 'transform 0.2s, box-shadow 0.2s',
                    }}
                    onClick={() => onOpen(`/pdf/${src.pdf}`)}
                    onMouseEnter={(e) => {
                        const el = e.currentTarget as HTMLDivElement;
                        el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                        el.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                        const el = e.currentTarget as HTMLDivElement;
                        el.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                        el.style.transform = 'none';
                    }}
                >
                    <div style={{ fontSize: 20, marginBottom: 6 }}>📄</div>
                    <Typography.Link style={{ fontSize: 13 }}>
                        PDFを開く
                    </Typography.Link>
                </div>
            ))}
        </div>
    );
};

export default PdfCardList;
