import React from 'react';
import { Typography } from 'antd';
import CsvUploadPanel from '@/components/Report/common/CsvUploadPanel';
import VerticalActionButton from '@/components/ui/VerticalActionButton';
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
        <div style={{ padding: 24 }}>
            {header && <div style={{ marginBottom: 8 }}>{header}</div>}

            <div
                style={{
                    display: 'flex',
                    gap: 24,
                    alignItems: 'stretch',
                    height: 'calc(100vh - 120px)',
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
                        <div
                            style={{
                                width: '80%',
                                height: '160px',
                                overflowY: 'auto', // ✅ 表示領域の高さ
                                overflowX: 'hidden', // ✅ はみ出た部分を隠す
                                borderRadius: 4,
                                background: '#f9f9f9',
                            }}
                        >
                            <img
                                src={sampleImageUrl}
                                alt='帳票サンプル'
                                style={{
                                    width: '100%', // ✅ 横幅いっぱいに拡大
                                    height: 'auto',
                                    objectFit: 'cover', // ✅ 高さに合わせてトリミング
                                    objectPosition: 'top', // ✅ 上部を優先的に表示
                                }}
                            />
                        </div>
                    )}
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
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    width: 120,
                                }}
                            >
                                <VerticalActionButton
                                    icon={<DownloadOutlined />}
                                    text='ダウンロード'
                                    href={pdfUrl}
                                    download
                                    backgroundColor='#00b894'
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
