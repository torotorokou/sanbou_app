import React from 'react';
import { Typography, Spin } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap } from '@/constants/reportManage';
import type { ReportKey } from '@/constants/reportManage';

// === 型定義グループ化 ===
type CsvConfig = {
    config: {
        label: string;
        onParse: (csvText: string) => void;
    };
    required: boolean;
};

type StepProps = {
    steps: string[];
    currentStep: number;
    setCurrentStep: (step: number) => void;
};

type FileProps = {
    csvConfigs: CsvConfig[];
    files: { [csvLabel: string]: File | null };
    onUploadFile: (label: string, file: File | null) => void;
};

type PreviewProps = {
    previewUrl: string | null;
    setPreviewUrl: (url: string | null) => void;
};

type ModalProps = {
    modalOpen: boolean;
    setModalOpen: (b: boolean) => void;
};

type FinalizedProps = {
    finalized: boolean;
    setFinalized: (b: boolean) => void;
};

type LoadingProps = {
    loading: boolean;
    setLoading: (b: boolean) => void;
};

type ReportBaseProps = {
    step: StepProps;
    file: FileProps;
    preview: PreviewProps;
    modal: ModalProps;
    finalized: FinalizedProps;
    loading: LoadingProps;
    generatePdf: () => Promise<string>;
    reportKey: ReportKey; // ✅ 追加
};

// === コンポーネント本体 ===
const ReportBase: React.FC<ReportBaseProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    generatePdf,
    reportKey, // ✅ 追加
}) => {
    const readyToCreate = file.csvConfigs
        .filter((entry) => entry.required)
        .every((entry) => file.files[entry.config.label]);

    const makeUploadProps = (
        label: string,
        parser: (csvText: string) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (fileObj) => {
            file.onUploadFile(label, fileObj);
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                parser(text);
            };
            reader.readAsText(fileObj);
            return false;
        },
    });

    const handleGenerate = async () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        try {
            const url = await generatePdf();
            preview.setPreviewUrl(url);
            finalized.setFinalized(true);
        } catch (err) {
            console.error('PDF生成エラー:', err);
        } finally {
            loading.setLoading(false);
            setTimeout(() => {
                modal.setModalOpen(false);
            }, 1000);
        }
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
                uploadFiles={file.csvConfigs.map((entry) => ({
                    label: entry.config.label,
                    file: file.files[entry.config.label] ?? null,
                    onChange: (f) => file.onUploadFile(entry.config.label, f),
                    required: entry.required, // ✅ これが重要！
                }))}
                makeUploadProps={(label) => {
                    const entry = file.csvConfigs.find(
                        (e) => e.config.label === label
                    );
                    return entry
                        ? makeUploadProps(label, entry.config.onParse)
                        : {};
                }}
                finalized={finalized.finalized}
                readyToCreate={readyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]} // ✅ プレビュー画像を帳票キーから取得
                pdfUrl={preview.previewUrl}
            >
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
