// /app/src/components/Report/adapters/FactoryReportAdapter.tsx
import React from 'react';
import UnifiedReportLayout from '../common/UnifiedReportLayout';
import type { FactoryReportKey } from '../../../constants/reportConfig/factoryReportConfig';
import { FACTORY_REPORT_KEYS } from '../../../constants/reportConfig/factoryReportConfig';
import type { UploadProps } from 'antd';
import type { UploadFileConfig } from '../../../types/reportBase';

interface FactoryReportAdapterProps {
    reportKey: FactoryReportKey;
    onChangeReportKey: (key: FactoryReportKey) => void;
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
 * 工場帳簿用アダプターコンポーネント
 * 
 * 🎯 責任：
 * - 工場帳簿設定を統合レイアウトに適応
 * - 工場帳簿固有のタブと設定を提供
 * - UnifiedReportLayoutとの橋渡し
 */
const FactoryReportAdapter: React.FC<FactoryReportAdapterProps> = ({
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
    // 工場帳簿のタブ作成
    const reportTabs = Object.entries(FACTORY_REPORT_KEYS).map(([key, config]) => ({
        key,
        label: config.label,
        icon: '🏭', // 工場帳簿共通アイコン
    }));

    // 型安全なキー変更ハンドラー
    const handleChangeReportKey = (key: string) => {
        onChangeReportKey(key as FactoryReportKey);
    };

    return (
        <UnifiedReportLayout
            title="工場帳簿システム"
            icon="🏭"
            reportTabs={reportTabs}
            selectedReportKey={reportKey}
            onChangeReportKey={handleChangeReportKey}
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

export default FactoryReportAdapter;
