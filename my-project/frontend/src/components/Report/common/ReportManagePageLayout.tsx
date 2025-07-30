import React from 'react';
import { Typography } from 'antd';
import CsvUploadPanel from '@/components/common/csv-upload/CsvUploadPanel';
import VerticalActionButton from '@/components/ui/VerticalActionButton';
import ReportSampleThumbnail from '@/components/Report/viewer/ReportSampleThumbnail';
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { CsvFileType } from './types';

// === excelUrlを追加 ===
export type ReportPageLayoutProps = {
    uploadFiles: CsvFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
    onGenerate: () => void;
    onDownloadExcel: () => void;
    finalized: boolean;
    readyToCreate: boolean;
    pdfUrl?: string | null;
    excelUrl?: string | null; // ★追加
    header?: React.ReactNode;
    children?: React.ReactNode;
    sampleImageUrl?: string;
};

const ReportManagePageLayout: React.FC<ReportPageLayoutProps> = (props: ReportPageLayoutProps) => {
    const {
        uploadFiles,
        onDownloadExcel,
        makeUploadProps,
        onGenerate,
        finalized,
        readyToCreate,
        pdfUrl,
        excelUrl, // ★追加
        header,
        children,
        sampleImageUrl,
    } = props;
    return (
        <div style={{ padding: 24 }}>
            {header && <div style={{ marginBottom: 8 }}>{header}</div>}

            <div
                style={{
                    display: 'flex',
                    gap: 24,
                    alignItems: 'stretch',
                    flexGrow: 1,
                    marginTop: 16,
                }}
            >
                {/* 左：CSVアップロード */}
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 16,
                        width: 400,
                    }}
                >
                    {/* 帳票サンプル画像 */}
                    <Typography.Title level={5}>
                        📄 帳票サンプル
                    </Typography.Title>

                    {sampleImageUrl && (
                        <div className='sample-thumbnail'>
                            <ReportSampleThumbnail
                                url={sampleImageUrl}
                                width='100%'
                                height='160px'
                            />
                        </div>
                    )}

                    {/* CSVアップロードパネル */}
                    <Typography.Title level={5}>
                        📂 データセットの準備
                    </Typography.Title>

                    <CsvUploadPanel
                        upload={{ files: uploadFiles, makeUploadProps }}
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

                {/* 右：プレビュー + ダウンロード */}
                <div
                    style={{
                        flex: 1,
                        height: '80vh',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 16,
                    }}
                >
                    <Typography.Title level={4} style={{ marginBottom: 0 }}>
                        📄 プレビュー画面
                    </Typography.Title>

                    <div
                        style={{
                            display: 'flex',
                            flex: 1,
                            gap: 16,
                            alignItems: 'center',
                        }}
                    >
                        {/* プレビュー領域 */}
                        <div
                            style={{
                                flex: 1,
                                height: '100%',
                                border: '1px solid #ccc',
                                borderRadius: 8,
                                boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                background: '#fafafa',
                                overflow: 'hidden',
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                            }}
                        >
                            {children ? (
                                children
                            ) : (
                                <Typography.Text type='secondary'>
                                    帳簿を作成するとここに表示されます。
                                </Typography.Text>
                            )}
                        </div>

                        {/* ダウンロードボタン（Excel） */}
                        {finalized && (
                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    width: 120,
                                    gap: 8,
                                }}
                            >
                                <VerticalActionButton
                                    icon={<DownloadOutlined />}
                                    text='エクセルDL'
                                    onClick={onDownloadExcel}
                                    disabled={!excelUrl}
                                    backgroundColor='#fdcb6e'
                                />
                                {/* 印刷ボタンはpdfUrl必須 */}
                                <VerticalActionButton
                                    icon={<PlayCircleOutlined />}
                                    text='印刷'
                                    onClick={() => {
                                        if (pdfUrl) {
                                            const win = window.open(
                                                pdfUrl,
                                                '_blank'
                                            );
                                            win?.focus();
                                            win?.print();
                                        }
                                    }}
                                    backgroundColor='#0984e3'
                                    disabled={!pdfUrl}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ReportManagePageLayout;
