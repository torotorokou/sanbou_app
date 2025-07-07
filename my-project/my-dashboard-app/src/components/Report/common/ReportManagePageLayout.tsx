import React from 'react';
import { Typography, Button } from 'antd';
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
import CsvUploadPanel from '@/components/Report/common/CsvUploadPanel';
import { customTokens } from '@/theme/tokens';
import type { UploadProps } from 'antd';
import VerticalActionButton from '@/components/ui/VerticalActionButton';

export type CsvFileType = {
    label: string;
    file: File | null;
    onChange: (file: File) => void;
};

type ReportPageLayoutProps = {
    title: string;
    onGenerate: () => void;
    uploadFiles: CsvFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
    finalized: boolean;
    readyToCreate: boolean;
    pdfUrl?: string | null; // ✅ 追加
    children?: React.ReactNode;
};

const ReportManagePageLayout: React.FC<ReportPageLayoutProps> = ({
    title,
    onGenerate,
    uploadFiles,
    makeUploadProps,
    finalized,
    readyToCreate,
    pdfUrl,
    children,
}) => {
    return (
        <div style={{ padding: 24 }}>
            <Typography.Title level={3}>{title}</Typography.Title>
            <div
                style={{
                    display: 'flex',
                    gap: 24,
                    alignItems: 'stretch',
                    height: 'calc(100vh - 120px)',
                    marginTop: 16,
                }}
            >
                {/* 左パネル：CSVアップロード領域拡大 */}
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 16,
                        width: 400,
                    }}
                >
                    <Typography.Title level={5}>
                        📂 データセットの準備
                    </Typography.Title>
                    <Typography.Paragraph
                        style={{
                            margin: 0,
                            padding: '0 8px',
                            fontSize: 12,
                            color: '#666',
                        }}
                    ></Typography.Paragraph>
                    <CsvUploadPanel
                        files={uploadFiles}
                        makeUploadProps={makeUploadProps}
                    />
                </div>

                {/* 中央：帳簿作成ボタン */}
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        width: 120,
                    }}
                >
                    <VerticalActionButton
                        icon={<PlayCircleOutlined />}
                        text='帳簿作成'
                        onClick={onGenerate}
                        disabled={!readyToCreate}
                    />
                </div>

                {/* 帳票表示エリア */}
                <div style={{ flex: 1 }}>
                    <Typography.Title level={4}>
                        📄 プレビュー画面
                    </Typography.Title>

                    {finalized ? (
                        <iframe
                            src={pdfUrl}
                            style={{
                                width: '100%',
                                height: '80vh',
                                border: '1px solid #ccc',
                                borderRadius: 8,
                                boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                            }}
                        />
                    ) : (
                        <Typography.Text type='secondary'>
                            帳簿を作成するとここに表示されます。
                        </Typography.Text>
                    )}
                </div>

                {/* 右端：ダウンロードボタン */}
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        width: 120,
                    }}
                >
                    {finalized && pdfUrl && (
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
                                backgroundColor:
                                    customTokens.colorDownloadButton,
                                color: '#fff',
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
                    )}
                </div>
            </div>
        </div>
    );
};

export default ReportManagePageLayout;
