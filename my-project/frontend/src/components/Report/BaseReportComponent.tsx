import React, { useEffect } from 'react';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap, modalStepsMap, getReportType } from '../../constants/reportConfig/managementReportConfig';
import { useReportBaseBusiness } from '../../hooks/report';
import type { ReportBaseProps } from '../../types/reportBase';
import type { ZipProcessResult } from './services/CsvUploadService';

export interface ReportGenerationCallbacks {
    onStart: () => void;
    onComplete: () => void;
    onSuccess: () => void;
}

export interface BaseReportComponentProps extends ReportBaseProps {
    /**
     * ReportFactory統合処理ハンドラー
     * ZIP処理・ステップ制御が統合された新しい処理方式
     * auto・interactiveタイプ両方で使用
     */
    customHandleGenerate?: (
        business: ReturnType<typeof useReportBaseBusiness>,
        callbacks: ReportGenerationCallbacks,
        reportKey: string
    ) => void;

    /**
     * カスタムモーダルコンテンツレンダラー
     * 主にinteractiveタイプのワークフローUIで使用
     */
    customContentRenderer?: (stepIndex: number, stepConfig: unknown) => React.ReactNode;

    /**
     * カスタムモーダル閉じる処理
     */
    onModalClose?: () => void;

    /**
     * グローバルバリデーション結果取得関数（オプション）
     */
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';

    /**
     * ZIP処理結果（Excel・PDF連携用）
     * ReportFactory統合処理で生成される
     */
    zipResult?: ZipProcessResult | null;

    /**
     * ステップ進行制御コールバック
     * StepControllerのリセット処理で使用
     */
    onStepAdvance?: () => void;
}

/**
 * レポートベースコンポーネント（共通処理統合）
 * SimpleとInteractiveの共通ロジックを統合
 */
const BaseReportComponent: React.FC<BaseReportComponentProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    reportKey,
    customHandleGenerate,
    customContentRenderer,
    onModalClose,
    getValidationResult,
    zipResult,
    onStepAdvance
}) => {
    // ビジネスロジックをフックに委譲
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey,
        getValidationResult // グローバルバリデーション関数を渡す
    );

    // ZIP処理結果に基づくカスタム関数を定義
    const customDownloadExcel = () => {
        if (zipResult?.excelBlob && zipResult?.excelFileName) {
            const url = URL.createObjectURL(zipResult.excelBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = zipResult.excelFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            console.log(`[BaseReportComponent] Downloaded Excel: ${zipResult.excelFileName}`);
        } else {
            console.log('[BaseReportComponent] Excel not available for download');
        }
    };

    const customPrintPdf = () => {
        if (zipResult?.pdfBlob) {
            const url = zipResult.pdfPreviewUrl || URL.createObjectURL(zipResult.pdfBlob);
            const printWindow = window.open(url, '_blank');

            if (printWindow) {
                printWindow.focus();
                setTimeout(() => {
                    printWindow.print();
                }, 500);
                console.log('[BaseReportComponent] Opened PDF for printing');
            }

            if (!zipResult.pdfPreviewUrl) {
                setTimeout(() => URL.revokeObjectURL(url), 15000);
            }
        } else {
            console.log('[BaseReportComponent] PDF not available for printing');
        }
    };

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (business.pdfPreviewUrl && business.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(business.pdfPreviewUrl);
        }
    }, [business.pdfPreviewUrl, preview]);

    // レポート生成コールバック定義
    const callbacks: ReportGenerationCallbacks = {
        onStart: () => {
            console.log(`[BaseReportComponent:${reportKey}] handleGenerateReport: onStart`);
        },
        onComplete: () => {
            console.log(`[BaseReportComponent:${reportKey}] handleGenerateReport: onComplete`);
            loading.setLoading(false);

            // ReportFactory統合処理使用時はステップ制御を委譲
            // 直接呼び出し（レガシー）の場合のみ自動ステップ制御
            if (!customHandleGenerate) {
                const stepConfigs = modalStepsMap[reportKey];
                const currentConfig = stepConfigs?.[step.currentStep];
                if (currentConfig && !currentConfig.showNext && !currentConfig.showClose) {
                    setTimeout(() => {
                        console.log(`[BaseReportComponent:${reportKey}] modal auto close`);
                        modal.setModalOpen(false);
                    }, 1000);
                }
            }
        },
        onSuccess: () => {
            console.log(`[BaseReportComponent:${reportKey}] handleGenerateReport: onSuccess`);
            finalized.setFinalized(true);
        }
    };

    // レポート生成処理
    const handleGenerate = () => {
        console.log(`[BaseReportComponent:${reportKey}] handleGenerate called`);

        // モーダルを開く前にステップを必ず0にリセット
        step.setCurrentStep(0);
        modal.setModalOpen(true);
        loading.setLoading(true);

        console.log(`[BaseReportComponent:${reportKey}] Modal opened at step 0`);

        if (customHandleGenerate) {
            // ReportFactory経由の統合処理（auto・interactive両方）
            // ZIP処理とステップ制御が統一されている
            customHandleGenerate(business, callbacks, reportKey);
        } else {
            // 直接呼び出し（レガシー・現在は非推奨）
            // ※将来的に削除予定
            business.handleGenerateReport(
                callbacks.onStart,
                callbacks.onComplete,
                callbacks.onSuccess
            );
        }
    };

    // ステップ構成
    const steps = modalStepsMap[reportKey]?.map(stepConfig => stepConfig.label) || [];
    const stepConfigs = modalStepsMap[reportKey] || [];

    // レポートタイプの判定
    const reportType = getReportType(reportKey);
    const isInteractive = reportType === 'interactive';

    // モーダルコンテンツ生成
    const renderModalContent = (stepIndex: number) => {
        const stepConfig = stepConfigs[stepIndex];

        if (customContentRenderer) {
            // カスタムレンダラーを使用（Interactive用）
            return customContentRenderer(stepIndex, stepConfig);
        } else {
            // デフォルトレンダラーを使用（Simple用）
            return stepConfig?.content || <div>読み込み中...</div>;
        }
    };

    // モーダル閉じる処理
    const handleModalClose = () => {
        console.log(`[BaseReportComponent:${reportKey}] Modal closed`);
        modal.setModalOpen(false);
        step.setCurrentStep(0);
        loading.setLoading(false);

        // onStepAdvanceコールバックがあれば実行（ステップコントローラーリセット用）
        if (onStepAdvance) {
            onStepAdvance();
        }

        if (onModalClose) {
            onModalClose();
        }
    };

    return (
        <>
            <ReportStepperModal
                open={modal.modalOpen}
                steps={steps}
                currentStep={step.currentStep}
                onNext={() => {
                    if (step.currentStep < steps.length - 1) {
                        step.setCurrentStep(step.currentStep + 1);
                    } else {
                        handleModalClose();
                    }
                }}
                onPrev={() => {
                    if (step.currentStep > 0) {
                        step.setCurrentStep(step.currentStep - 1);
                    }
                }}
                stepConfigs={stepConfigs}
                onClose={handleModalClose}
                isInteractive={isInteractive}
                allowEarlyClose={true} // 閉じるボタンは表示するが、×ボタンやESCは制限
            >
                {renderModalContent(step.currentStep)}
            </ReportStepperModal>

            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={zipResult?.hasExcel ? customDownloadExcel : business.downloadExcel}
                onPrintPdf={zipResult?.hasPdf ? customPrintPdf : business.printPdf}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={zipResult?.pdfPreviewUrl || preview.previewUrl}
                excelReady={zipResult?.hasExcel || business.hasExcel}
                pdfReady={zipResult?.hasPdf || business.hasPdf}
            >
                <PDFViewer pdfUrl={zipResult?.pdfPreviewUrl || preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default BaseReportComponent;
