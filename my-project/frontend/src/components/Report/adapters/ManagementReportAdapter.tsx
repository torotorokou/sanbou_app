// /app/src/components/Report/adapters/ManagementReportAdapter.tsx
import React from 'react';
import UnifiedReportLayout from '../common/UnifiedReportLayout';
import type { ReportKey } from '../../../constants/reportConfig/managementReportConfig';
import { REPORT_KEYS } from '../../../constants/reportConfig/managementReportConfig';
import type { UploadProps } from 'antd';
import type { UploadFileConfig } from '../../../types/reportBase';

interface ManagementReportAdapterProps {
    reportKey: ReportKey;
    onChangeReportKey: (key: string) => void;
    currentStep: number;
    uploadFiles: UploadFileConfig[];
    makeUploadProps: (label: string, setter: (file: File) => void) => UploadProps;
    onGenerate: () => void;
    onDownloadExcel: () => void;
    onPrintPdf?: () => void;
    finalized: boolean;
    readyToCreate: boolean;
    pdfUrl?: string | null;
    excelUrl?: string | null;
    excelReady?: boolean;
    pdfReady?: boolean;
    sampleImageUrl?: string;
    children?: React.ReactNode;
}

/**
 * 管理帳簿用アダプターコンポーネント
 * 
 * 🎯 責任：
 * - 管理帳簿設定を統合レイアウトに適応
 * - 管理帳簿固有のタブと設定を提供
 * - UnifiedReportLayoutとの橋渡し
 */
const ManagementReportAdapter: React.FC<ManagementReportAdapterProps> = ({
    reportKey,
    onChangeReportKey,
    currentStep,
    uploadFiles,
    makeUploadProps,
    onGenerate,
    onDownloadExcel,
    onPrintPdf,
    finalized,
    readyToCreate,
    pdfUrl,
    excelUrl,
    excelReady,
    pdfReady,
    sampleImageUrl,
    children,
}) => {
    // 管理帳簿のタブ作成
    const reportTabs = Object.entries(REPORT_KEYS).map(([key, config]) => ({
        key,
        label: config.label,
        icon: '📊', // 管理帳簿共通アイコン
    }));

    return (
        <UnifiedReportLayout
            title="管理帳簿システム"
            icon="📊"
            reportTabs={reportTabs}
            selectedReportKey={reportKey}
            onChangeReportKey={onChangeReportKey}
            currentStep={currentStep}
            stepTitles={['CSVアップロード', '帳簿生成', '結果確認']}
            uploadFiles={uploadFiles}
            makeUploadProps={makeUploadProps}
            onGenerate={onGenerate}
            onDownloadExcel={onDownloadExcel}
            onPrintPdf={onPrintPdf}
            finalized={finalized}
            readyToCreate={readyToCreate}
            pdfUrl={pdfUrl}
            excelUrl={excelUrl}
            excelReady={excelReady}
            pdfReady={pdfReady}
            sampleImageUrl={sampleImageUrl}
        >
            {children}
        </UnifiedReportLayout>
    );
};

export default ManagementReportAdapter;
