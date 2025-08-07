import React, { useEffect } from 'react';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap, modalStepsMap } from '../../constants/reportConfig';
import { useReportBaseBusiness } from '../../hooks/report';
import type { ReportBaseProps } from '../../types/reportBase';

/**
 * レポートベースコンポーネント - リファクタリング版
 * 
 * 🔄 改善内容：
 * - 複雑なビジネスロジックをカスタムフックに分離
 * - 型定義を別ファイルに移動
 * - 関心の分離により保守性を大幅向上
 * - コンポーネントはUIレンダリングのみに集中
 * 
 * 📝 従来のコード行数：~300行 → 現在：~100行（66%削減）
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
    // ビジネスロジックをフックに委譲
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey
    );

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (business.pdfPreviewUrl && business.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(business.pdfPreviewUrl);
        }
    }, [business.pdfPreviewUrl, preview]);    // レポート生成処理
    const handleGenerate = () => {
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

    const steps = modalStepsMap[reportKey].map(step => step.label);
    const contents = modalStepsMap[reportKey].map(step => step.content);
    const stepConfigs = modalStepsMap[reportKey];

    return (
        <>
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

            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={business.downloadExcel}
                onPrintPdf={business.printPdf}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={preview.previewUrl}
                excelReady={business.hasExcel}
                pdfReady={business.hasPdf}
            >
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
