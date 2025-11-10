import React from 'react';
import type { ReactNode } from 'react';
import { useReportLayoutStyles } from '@features/report-select/model/useReportLayoutStyles';
import { useResponsive } from '@/shared';
import SampleSection from '@features/report-extras/ui/SampleSection';
import CsvUploadSection from '@features/report-upload/ui/CsvUploadSection';
import ActionsSection from '@features/report-actions/ui/ActionsSection';
import PreviewSection from '@features/report-preview/ui/PreviewSection';
import type { UploadProps } from 'antd';
import type { UploadFileConfig } from '@features/report-extras/types/report.types';
import type { CsvUploadFileType as CsvFileType } from './types';

/**
 * レポート管理ページレイアウト - useResponsive(flags)統合版
 * 
 * 🔄 リファクタリング内容：
 * - isTabletOrHalf、window.innerWidth直参照を全廃
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 */

// Convert UploadFileConfig validation result to CsvFileType format
const mapValidationResult = (result?: 'valid' | 'invalid' | 'unknown'): 'ok' | 'ng' | 'unknown' | undefined => {
    if (!result) return undefined;
    if (result === 'valid') return 'ok';
    if (result === 'invalid') return 'ng';
    return 'unknown';
};

const convertToCsvFileType = (files: UploadFileConfig[]): CsvFileType[] => {
    return files.map(f => ({
        ...f,
        validationResult: mapValidationResult(f.validationResult as 'valid' | 'invalid' | 'unknown' | undefined)
    }));
};

type Props = {
    header?: ReactNode;
    sampleImageUrl?: string;
    uploadFiles?: UploadFileConfig[];
    // MakeUploadPropsFn と同等: ラベルから UploadProps を生成
    makeUploadProps?: (label: string) => UploadProps;
    onGenerate?: () => void;
    readyToCreate?: boolean;
    finalized?: boolean;
    onDownloadExcel?: () => void;
    onPrintPdf?: () => void;
    pdfUrl?: string | null;
    excelReady?: boolean;
    pdfReady?: boolean;
    children?: ReactNode;
};

const ReportManagePageLayout: React.FC<Props> = ({
    header,
    sampleImageUrl,
    uploadFiles: mappedUploadFiles,
    makeUploadProps,
    onGenerate,
    readyToCreate,
    finalized,
    onDownloadExcel,
    onPrintPdf,
    pdfUrl,
    excelReady,
    pdfReady,
    children,
}) => {
    const styles = useReportLayoutStyles();
    
    // responsive: flagsベースの段階スイッチ
    const { flags } = useResponsive();

    // responsive: 段階的な値決定（Mobile→Tablet→Laptop→Desktop）
    const pickByDevice = <T,>(mobile: T, tablet: T, laptop: T, desktop: T): T => {
        if (flags.isMobile) return mobile;
        if (flags.isTablet) return tablet;
        if (flags.isLaptop) return laptop;
        return desktop; // isDesktop
    };

    // responsive: レイアウト切り替え
    // - isXs: 1列（データセット上、プレビュー下）
    // - isSm/isTablet: 2列簡易レイアウト
    // - Laptop以上: フルレイアウト
    const isExtraSmallLayout = flags.isXs; // < 640px: 1列縦並び
    const isCompactLayout = flags.isSm || flags.isTablet; // 640-1023px: 2列横並び
    const gap = pickByDevice(8, 12, 16, 16);
    const headerJustify = pickByDevice<'center' | 'flex-start'>('center', 'center', 'flex-start', 'flex-start');

    return (
        <div style={styles.container}>
            {header && (
                <div
                    style={{
                        marginBottom: 8,
                        display: 'flex',
                        justifyContent: headerJustify,
                        width: '100%'
                    }}
                >
                    {header}
                </div>
            )}

            <div style={styles.mainLayout}>
                {/* responsive: isXs (< 640px) - 1列縦並びレイアウト */}
                {isExtraSmallLayout ? (
                    <>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%', minHeight: 0, flex: 1 }}>
                            {/* データセット（上） */}
                            <div style={{ flex: '0 0 auto', minHeight: 200 }}>
                                <CsvUploadSection
                                    uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                                    makeUploadProps={(label: string) =>
                                        (makeUploadProps ? makeUploadProps(label) : ({} as UploadProps))
                                    }
                                />
                            </div>

                            {/* プレビュー（下） */}
                            <div style={{ flex: '1 1 auto', minHeight: 300 }}>
                                <div style={styles.previewContainer}>
                                    <PreviewSection>{children}</PreviewSection>
                                </div>
                            </div>
                        </div>

                        {/* アクションボタン（最下部） */}
                        <div style={{ width: '100%', marginTop: 12 }}>
                            <ActionsSection
                                onGenerate={onGenerate ?? (() => {})}
                                readyToCreate={!!readyToCreate}
                                finalized={!!finalized}
                                onDownloadExcel={onDownloadExcel ?? (() => {})}
                                onPrintPdf={onPrintPdf}
                                pdfUrl={pdfUrl ?? null}
                                excelReady={!!excelReady}
                                pdfReady={!!pdfReady}
                                compactMode={true}
                            />
                        </div>
                    </>
                ) : isCompactLayout ? (
                    <>
                        {/* isSm/Tablet (640-1023px) - 2列横並びレイアウト */}
                        <div style={{ display: 'flex', gap, width: '100%', minHeight: 0, flex: 1 }}>
                            <div style={{ flex: '1 1 40%', display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
                                <div style={{ display: 'none' }}>
                                    <SampleSection sampleImageUrl={sampleImageUrl} />
                                </div>
                                <CsvUploadSection
                                    uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                                    makeUploadProps={(label: string) =>
                                        (makeUploadProps ? makeUploadProps(label) : ({} as UploadProps))
                                    }
                                />
                            </div>

                            <div style={{ flex: '1 1 60%', display: 'flex', minHeight: 0 }}>
                                <div style={styles.previewContainer}>
                                    <PreviewSection>{children}</PreviewSection>
                                </div>
                            </div>
                        </div>

                        <div style={{ width: '100%', marginTop: 12 }}>
                            <ActionsSection
                                onGenerate={onGenerate ?? (() => {})}
                                readyToCreate={!!readyToCreate}
                                finalized={!!finalized}
                                onDownloadExcel={onDownloadExcel ?? (() => {})}
                                onPrintPdf={onPrintPdf}
                                pdfUrl={pdfUrl ?? null}
                                excelReady={!!excelReady}
                                pdfReady={!!pdfReady}
                                compactMode={true}
                            />
                        </div>
                    </>
                ) : (
                    <>
                        {/* Laptop/Desktop (≥1024px) - フルレイアウト */}
                        <div style={styles.leftPanel}>
                            <SampleSection sampleImageUrl={sampleImageUrl} />
                            <CsvUploadSection
                                uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                                makeUploadProps={(label: string) =>
                                    (makeUploadProps ? makeUploadProps(label) : ({} as UploadProps))
                                }
                            />
                        </div>

                        <div style={styles.centerPanel as React.CSSProperties}>
                            <ActionsSection
                                onGenerate={onGenerate ?? (() => {})}
                                readyToCreate={!!readyToCreate}
                                finalized={!!finalized}
                                onDownloadExcel={onDownloadExcel ?? (() => {})}
                                onPrintPdf={onPrintPdf}
                                pdfUrl={pdfUrl ?? null}
                                excelReady={!!excelReady}
                                pdfReady={!!pdfReady}
                            />
                        </div>

                        <div style={styles.rightPanel}>
                            <div style={styles.previewContainer}>
                                <PreviewSection>{children}</PreviewSection>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default ReportManagePageLayout;
