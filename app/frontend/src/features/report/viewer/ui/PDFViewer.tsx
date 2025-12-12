import React, { useEffect, useState } from 'react';
import { Typography, Alert, Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { useResponsive, ensurePdfJsWorkerLoaded } from '@/shared';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// PDFステータスの型定義
type PdfStatus = "idle" | "pending" | "ready" | "error";

type PDFViewerProps = {
    pdfUrl?: string | null;
    pdfStatus?: PdfStatus;  // 🔄 PDF非同期生成ステータス
    height?: string;
};

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, pdfStatus = "idle", height }) => {
    const { isMobile } = useResponsive();
    const [hasError, setHasError] = useState(false);

    useEffect(() => {
        if (!pdfUrl) return;
        ensurePdfJsWorkerLoaded().catch(() => void 0);
    }, [pdfUrl]);

    // PDF生成中（pending）の場合はスピナー表示
    if (pdfStatus === "pending") {
        return (
            <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: isMobile ? '300px' : '400px',
                padding: isMobile ? '12px' : '16px',
                gap: '16px',
            }}>
                <Spin
                    indicator={<LoadingOutlined style={{ fontSize: isMobile ? 32 : 48 }} spin />}
                    size="large"
                />
                <Typography.Text
                    type='secondary'
                    style={{
                        textAlign: 'center',
                        fontSize: isMobile ? '14px' : '16px',
                    }}
                >
                    PDFプレビュー生成中...
                    <br />
                    （エクセルのダウンロードは可能です）
                </Typography.Text>
            </div>
        );
    }

    // PDF生成エラーの場合
    if (pdfStatus === "error") {
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
                    message="PDF生成エラー"
                    description="PDFの生成に失敗しましたがエクセルのダウンロードは可能です。"
                    type="error"
                    showIcon
                />
            </div>
        );
    }

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
