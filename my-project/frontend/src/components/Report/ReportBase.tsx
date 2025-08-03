import React from 'react';
import { Typography, Spin } from 'antd';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap } from '../../constants/reportConfig/managementReportConfig';
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
    generatePdf,
    reportKey
}) => {
    // ビジネスロジックをフックに委譲
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey
    );

    // Excel生成処理
    const handleGenerate = () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        business.handleGenerateExcel(
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

    return (
        <>
            <ReportStepperModal
                open={modal.modalOpen}
                steps={step.steps}
                currentStep={step.currentStep}
                onNext={() => {
                    if (step.currentStep === step.steps.length - 1) {
                        modal.setModalOpen(false);
                        step.setCurrentStep(0);
                    }
                }}
            >
                {step.currentStep === 0 && (
                    <Typography.Text>
                        帳簿を作成する準備が整いました。
                    </Typography.Text>
                )}
                {step.currentStep === 1 && loading.loading && (
                    <Spin tip='帳簿をPDFに変換中です...' />
                )}
                {step.currentStep === 2 && (
                    <Typography.Text type='success'>
                        ✅ 帳簿PDFが作成されました。
                    </Typography.Text>
                )}
            </ReportStepperModal>

            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={business.downloadExcel}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={preview.previewUrl}
                excelUrl={business.excelUrl}
            >
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
