import React from 'react';
import { Typography } from 'antd';
import CsvUploadPanel from '@/components/Report/common/CsvUploadPanel';
import VerticalActionButton from '@/components/ui/VerticalActionButton';
import ReportSampleThumbnail from '@/components/Report/viewer/ReportSampleThumbnail';
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { CsvFileType } from './types';

export type ReportPageLayoutProps = {
    uploadFiles: CsvFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
    onGenerate: () => void;
    finalized: boolean;
    readyToCreate: boolean;
    pdfUrl?: string | null;
    header?: React.ReactNode;
    children?: React.ReactNode;

    // ✅ 追加：帳票サンプル画像のURL
    sampleImageUrl?: string;
};

const ReportManagePageLayout: React.FC<ReportPageLayoutProps> = ({
    uploadFiles,
    makeUploadProps,
    onGenerate,
    finalized,
    readyToCreate,
    pdfUrl,
    header,
    children,
    sampleImageUrl, // ✅ 追加
}) => {
    return (
        console.log('🖼️ sampleImageUrl:', sampleImageUrl),
        (
            <div style={{ padding: 24 }}>
                {header && <div style={{ marginBottom: 8 }}>{header}</div>}

                <div
                    style={{
                        display: 'flex',
                        gap: 24,
                        alignItems: 'stretch',
                        flexGrow: 1, // ← 高さの自動伸縮
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
                        {/* ✅ 帳票サンプル画像の表示 */}
                        <Typography.Title level={5}>
                            📄 帳票サンプル
                        </Typography.Title>

                        {sampleImageUrl && (
                            <ReportSampleThumbnail
                                url={sampleImageUrl} // ✅ 変更点
                                // type='image' // ✅ 明示的に画像と指定
                                width='80%'
                                height='160px'
                            />
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

                            {/* ダウンロードボタン */}
                            {finalized && pdfUrl && (
                                <div
                                    style={{
                                        display: 'flex',
                                        flexDirection: 'column', // ✅ 縦並び
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        width: 120,
                                        gap: 8, // ボタン間の余白
                                    }}
                                >
                                    <VerticalActionButton
                                        icon={<DownloadOutlined />}
                                        text='ダウンロード'
                                        href={pdfUrl}
                                        download
                                        backgroundColor='#00b894'
                                    />
                                    <VerticalActionButton
                                        icon={<PlayCircleOutlined />}
                                        text='印刷'
                                        onClick={() => {
                                            const win = window.open(
                                                pdfUrl,
                                                '_blank'
                                            );
                                            win?.focus();
                                            win?.print();
                                        }}
                                        backgroundColor='#0984e3'
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        )
    );
};

export default ReportManagePageLayout;
