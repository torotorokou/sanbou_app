// /app/src/components/Report/GenericBaseReportComponent.tsx
import React from 'react';
import ReportStepperModal from './common/ReportStepperModal';
import type { ReportConfigPackage } from '../../types/reportConfig';

export interface GenericZipResult {
    excelFile?: Uint8Array;
    pdfFile?: Uint8Array;
    originalResponse?: unknown;
    success: boolean;
    hasExcel: boolean;
    hasPdf: boolean;
    type: 'zip' | 'json';
}

export interface GenericBaseReportComponentProps {
    config: ReportConfigPackage;
    reportKey: string;
    currentStep: number;
    isLoading: boolean;
    zipResult?: GenericZipResult | null;
    onPrevious: () => void;
    onNext: () => void;
    onClose?: () => void;
    visible?: boolean;
}

/**
 * 汎用的なベース帳票コンポーネント
 * 
 * どの帳票設定パッケージでも使用可能な汎用ベースコンポーネント
 */
const GenericBaseReportComponent: React.FC<GenericBaseReportComponentProps> = ({
    config,
    reportKey,
    currentStep,
    isLoading,
    zipResult,
    onPrevious,
    onNext,
    onClose,
    visible = true,
}) => {
    const reportType = config.getReportType(reportKey);
    const isInteractive = reportType === 'interactive';
    const steps = config.getAllModalSteps(reportKey);
    const reportDefinition = config.reportKeys[reportKey];

    // カスタムダウンロード関数（Excel）
    const customDownloadExcel = () => {
        if (zipResult?.excelFile) {
            const blob = new Blob([zipResult.excelFile], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${reportDefinition?.label || reportKey}_report.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    };

    // カスタム印刷関数（PDF）
    const customPrintPdf = () => {
        if (zipResult?.pdfFile) {
            const blob = new Blob([zipResult.pdfFile], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const printWindow = window.open(url, '_blank');
            if (printWindow) {
                printWindow.onload = () => {
                    printWindow.print();
                };
            }
            URL.revokeObjectURL(url);
        }
    };

    // ステップコンテンツの生成
    const generateStepContent = (stepIndex: number) => {
        const stepConfig = steps[stepIndex];
        if (!stepConfig) return null;

        // デフォルトコンテンツがある場合はそれを使用
        if (stepConfig.content) {
            return stepConfig.content;
        }

        // ステップに応じてデフォルトコンテンツを生成
        switch (stepIndex) {
            case 0:
                return (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <p>{reportDefinition?.label}を処理中です...</p>
                        {isLoading && <div>しばらくお待ちください。</div>}
                    </div>
                );

            case steps.length - 1:
                return (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <p>{reportDefinition?.label}が完了しました。</p>
                        {zipResult?.hasExcel && (
                            <button onClick={customDownloadExcel} style={{ margin: '5px' }}>
                                Excelダウンロード
                            </button>
                        )}
                        {zipResult?.hasPdf && (
                            <button onClick={customPrintPdf} style={{ margin: '5px' }}>
                                PDF印刷
                            </button>
                        )}
                    </div>
                );

            default:
                return (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <p>ステップ {stepIndex + 1}: {stepConfig.label}</p>
                    </div>
                );
        }
    };

    return (
        <ReportStepperModal
            open={visible}
            steps={steps.map(step => step.label)}
            currentStep={currentStep}
            onClose={onClose}
            onPrev={onPrevious}
            onNext={onNext}
            isInteractive={isInteractive}
            allowEarlyClose={!isInteractive}
            stepConfigs={steps}
        >
            {generateStepContent(currentStep)}
        </ReportStepperModal>
    );
};

export default GenericBaseReportComponent;
