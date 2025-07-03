import React from 'react';
import { Typography, Button } from 'antd';
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
import CalendarSelector from '@/components/Report/common/CalendarSelector';
import CsvUploadPanel from '@/components/Report/common/CsvUploadPanel';
import { customTokens } from '@/theme/tokens';
import type { Dayjs } from 'dayjs';
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
    calendarDate: Dayjs | null;
    onDateChange: (date: Dayjs) => void;
    uploadFiles: CsvFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
    finalized: boolean;
    children?: React.ReactNode; // ← 帳票一式（出勤・有価・出荷…）
};

const ReportManagePageLayout: React.FC<ReportPageLayoutProps> = ({
    title,
    onGenerate,
    calendarDate,
    onDateChange,
    uploadFiles,
    makeUploadProps,
    finalized,
    children,
}) => {
    const readyToCreate =
        calendarDate || uploadFiles.some((f) => f.file !== null);

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
                {/* 左パネル：カレンダー・CSV */}
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 16,
                        width: 320,
                    }}
                >
                    <Typography.Title level={5}>
                        📂 データセットの準備
                    </Typography.Title>
                    <CalendarSelector
                        selectedDate={calendarDate}
                        onSelect={onDateChange}
                    />
                    <Typography.Paragraph
                        style={{
                            margin: 0,
                            padding: '0 8px',
                            fontSize: 12,
                            color: '#666',
                        }}
                    >
                        📅 カレンダーまたは 📂 CSV を選択してください
                    </Typography.Paragraph>
                    <CsvUploadPanel
                        files={uploadFiles}
                        makeUploadProps={makeUploadProps}
                    />
                </div>

                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center', // ✅ 縦方向の中央寄せ
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

                {/* 右側：帳簿の表示 */}
                <div style={{ flex: 1, overflowY: 'auto' }}>
                    <Typography.Title level={4}>
                        📄 {calendarDate?.format('YYYY年M月D日')} の帳簿
                    </Typography.Title>
                    {finalized ? (
                        <div
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 24,
                            }}
                        >
                            {children}
                        </div>
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
                    {finalized && (
                        <Button
                            icon={<DownloadOutlined />}
                            type='primary'
                            size='large'
                            shape='round'
                            style={{
                                writingMode: 'vertical-rl',
                                textOrientation: 'mixed',
                                height: 160,
                                fontSize: '1.2rem',
                                backgroundColor:
                                    customTokens.colorDownloadButton,
                                color: '#fff',
                                border: 'none',
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
