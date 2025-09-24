import React, { Suspense, useEffect } from 'react';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import BlockUnitPriceInteractiveModal from './interactive/BlockUnitPriceInteractiveModal';
const PDFViewer = React.lazy(() => import('./viewer/PDFViewer'));
import { pdfPreviewMap, modalStepsMap, isInteractiveReport } from '@/constants/reportConfig';
import { useReportBaseBusiness } from '../../hooks/report';
import { useZipProcessing } from '../../hooks/data/useZipProcessing';
import type { ReportBaseProps } from '../../types/reportBase';

/**
 * レポートベースコンポーネント - インタラクティブモーダル対応版
 * 
 * 🔄 改善内容：
 * - インタラクティブ帳簿専用モーダル分岐を追加
 * - 共通ZIP処理フックの統合
 * - 通常帳簿とインタラクティブ帳簿の統一的な体験
 * - 複雑なビジネスロジックをカスタムフックに分離
 * 
 * 📝 新機能：
 * - 帳簿タイプ別モーダル分岐
 * - インタラクティブフローサポート
 * - 統一されたZIP処理
 */
const ReportBase: React.FC<ReportBaseProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    reportKey
}) => {
    // ビジネスロジックとZIP処理フック
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey
    );
    const zipProcessing = useZipProcessing();

    // インタラクティブ帳簿かどうか判定
    const isInteractive = isInteractiveReport(reportKey);

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (business.pdfPreviewUrl && business.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(business.pdfPreviewUrl);
        }
    }, [business.pdfPreviewUrl, preview]);

    // ZIPプレビューURLが生成されたら設定（共通処理）
    useEffect(() => {
        if (zipProcessing.pdfPreviewUrl && zipProcessing.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(zipProcessing.pdfPreviewUrl);
        }
    }, [zipProcessing.pdfPreviewUrl, preview]);

    /**
     * 通常帳簿のレポート生成処理
     */
    const handleNormalGenerate = () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        business.handleGenerateReport(
            () => { }, // onStart
            () => {   // onComplete
                loading.setLoading(false);
                setTimeout(() => {
                    modal.setModalOpen(false);
                }, 1000);
            },
            () => {   // onSuccess  
                finalized.setFinalized(true);
            }
        );
    };

    /**
     * インタラクティブ帳簿のレポート生成処理
     */
    const handleInteractiveGenerate = () => {
        modal.setModalOpen(true);
    };

    /**
     * インタラクティブモーダルのZIP成功時処理（共通化）
     */
    const handleInteractiveSuccess = async (zipUrl: string, fileName: string) => {
        try {
            // ZIPファイルをBlob として取得
            const response = await fetch(zipUrl);
            const zipBlob = await response.blob();

            // 共通ZIP処理フックで処理
            const success = await zipProcessing.processZipFile(zipBlob, fileName);

            if (success) {
                finalized.setFinalized(true);
                // 少し遅延してモーダルを閉じる
                setTimeout(() => {
                    modal.setModalOpen(false);
                }, 1500);
            }
        } catch (error) {
            console.error('Interactive success handling failed:', error);
        }
    };

    // レポート生成処理を帳簿タイプに応じて選択
    const handleGenerate = isInteractive ? handleInteractiveGenerate : handleNormalGenerate;

    // モーダル設定
    const steps = modalStepsMap[reportKey].map(step => step.label);
    const contents = modalStepsMap[reportKey].map(step => step.content);
    const stepConfigs = modalStepsMap[reportKey];

    return (
        <>
            {/* 通常帳簿用モーダル */}
            {!isInteractive && (
                <ReportStepperModal
                    open={modal.modalOpen}
                    steps={steps}
                    currentStep={step.currentStep}
                    onNext={() => {
                        if (step.currentStep === step.steps.length - 1) {
                            modal.setModalOpen(false);
                            step.setCurrentStep(0);
                        }
                    }}
                    stepConfigs={stepConfigs}
                >
                    {contents[step.currentStep]}
                </ReportStepperModal>
            )}

            {/* インタラクティブ帳簿用モーダル */}
            {isInteractive && reportKey === 'block_unit_price' && (
                <BlockUnitPriceInteractiveModal
                    open={modal.modalOpen}
                    onClose={() => modal.setModalOpen(false)}
                    csvFiles={file.files}
                    reportKey={reportKey}
                    onSuccess={handleInteractiveSuccess}
                />
            )}

            {/* メインレイアウト */}
            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={zipProcessing.hasExcel ? zipProcessing.downloadExcel : business.downloadExcel}
                onPrintPdf={zipProcessing.hasPdf ? zipProcessing.printPdf : business.printPdf}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={preview.previewUrl}
                excelReady={zipProcessing.hasExcel || business.hasExcel}
                pdfReady={zipProcessing.hasPdf || business.hasPdf}
                header={undefined}
            >
                <Suspense fallback={null}>
                    <PDFViewer pdfUrl={preview.previewUrl} />
                </Suspense>
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
