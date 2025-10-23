import React from 'react';
import type { ReactNode } from 'react';
import { useReportLayoutStyles } from '@features/report/application/useReportLayoutStyles';
import { useWindowSize } from '@shared/hooks/ui';
import { isTabletOrHalf } from '@/shared/constants/breakpoints';
import SampleSection from './SampleSection';
import CsvUploadSection from './CsvUploadSection';
import ActionsSection from './ActionsSection';
import PreviewSection from './PreviewSection';
import type { UploadProps } from 'antd';
import type { UploadFileConfig } from '@features/report/domain/types/report.types';
import type { CsvFileType } from '@features/database';

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
        validationResult: mapValidationResult(f.validationResult as any)
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
    excelUrl?: string | null;
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
    excelUrl,
    pdfUrl,
    excelReady,
    pdfReady,
    children,
}) => {
    const styles = useReportLayoutStyles();
    const { width, isMobile, isTablet } = useWindowSize();

    const isHalfOrBelow = typeof width === 'number' ? isTabletOrHalf(width) : false;
    const isMobileOrTablet = isMobile || isTablet;

    return (
        <div style={styles.container}>
            {header && (
                <div
                    style={{
                        marginBottom: 8,
                        display: 'flex',
                        justifyContent: isHalfOrBelow ? 'center' : 'flex-start',
                        width: '100%'
                    }}
                >
                    {header}
                </div>
            )}

            <div style={styles.mainLayout}>
                {isHalfOrBelow ? (
                    <>
                        <div style={{ display: 'flex', gap: isMobile ? 8 : 16, width: '100%', minHeight: 0, flex: 1 }}>
                            <div style={{ flex: '1 1 40%', display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0 }}>
                                                <div style={{ display: 'none' }}>
                                                    <SampleSection sampleImageUrl={sampleImageUrl} />
                                                </div>
                                                <CsvUploadSection
                                                    uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                                                    // CsvUploadSection 側は (label, setter) を受けるため、
                                                    // setter は未使用でラップして互換にする
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
                                                excelUrl={excelUrl ?? null}
                                                pdfUrl={pdfUrl ?? null}
                                                excelReady={!!excelReady}
                                                pdfReady={!!pdfReady}
                                                compactMode={true}
                                            />
                        </div>
                    </>
                ) : (
                    <>
                        {isMobileOrTablet && (
                            <div style={styles.mobileActionsPanel}>
                                                <ActionsSection
                                                    onGenerate={onGenerate ?? (() => {})}
                                                    readyToCreate={!!readyToCreate}
                                                    finalized={!!finalized}
                                                    onDownloadExcel={onDownloadExcel ?? (() => {})}
                                                    onPrintPdf={onPrintPdf}
                                                    excelUrl={excelUrl ?? null}
                                                    pdfUrl={pdfUrl ?? null}
                                                    excelReady={!!excelReady}
                                                    pdfReady={!!pdfReady}
                                                />
                            </div>
                        )}

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
                                                excelUrl={excelUrl ?? null}
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
