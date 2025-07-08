import React from 'react';
import { Typography, Spin } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';

type CsvConfig = {
    label: string;
    onParse: (csvText: string) => void;
};

type ReportBaseProps = {
    reportKey: string;
    csvConfigs: CsvConfig[];
    steps: string[];
    generatePdf: () => Promise<string>;
    currentStep: number;
    setCurrentStep: (step: number) => void;
    files: { [csvLabel: string]: File | null };
    onUploadFile: (label: string, file: File | null) => void;
    previewUrl: string | null;
    setPreviewUrl: (url: string | null) => void;
    finalized: boolean;
    setFinalized: (b: boolean) => void;
    modalOpen: boolean;
    setModalOpen: (b: boolean) => void;
    loading: boolean;
    setLoading: (b: boolean) => void;
};

const ReportBase: React.FC<ReportBaseProps> = ({
    csvConfigs,
    steps,
    generatePdf,
    currentStep,
    setCurrentStep,
    files,
    onUploadFile,
    previewUrl,
    setPreviewUrl,
    finalized,
    setFinalized,
    modalOpen,
    setModalOpen,
    loading,
    setLoading,
}) => {
    // すべてのCSVが揃っていれば帳票作成可
    const readyToCreate = csvConfigs.every((cfg) => files[cfg.label]);

    // ファイルアップロード時のUploadPropsを生成
    const makeUploadProps = (
        label: string,
        parser: (csvText: string) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file) => {
            onUploadFile(label, file);
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                parser(text);
            };
            reader.readAsText(file);
            return false;
        },
    });

    // 帳票生成処理
    const handleGenerate = async () => {
        setModalOpen(true);
        setCurrentStep(1);
        setLoading(true);
        try {
            const url = await generatePdf();
            setPreviewUrl(url);
            setFinalized(true);
            setCurrentStep(2);
        } catch (err) {
            console.error('PDF生成エラー:', err);
            setCurrentStep(0);
        } finally {
            setLoading(false);
            setTimeout(() => {
                setModalOpen(false);
                setCurrentStep(0);
            }, 1000);
        }
    };

    return (
        <>
            <ReportStepperModal
                open={modalOpen}
                steps={steps}
                currentStep={currentStep}
                onNext={() => {
                    if (currentStep === steps.length - 1) {
                        setModalOpen(false);
                        setCurrentStep(0);
                    }
                }}
            >
                {currentStep === 0 && (
                    <Typography.Text>
                        帳簿を作成する準備が整いました。
                    </Typography.Text>
                )}
                {currentStep === 1 && loading && (
                    <Spin tip='帳簿をPDFに変換中です...' />
                )}
                {currentStep === 2 && (
                    <Typography.Text type='success'>
                        ✅ 帳簿PDFが作成されました。
                    </Typography.Text>
                )}
            </ReportStepperModal>

            <ReportManagePageLayout
                onGenerate={handleGenerate}
                uploadFiles={csvConfigs.map((cfg) => ({
                    label: cfg.label,
                    file: files[cfg.label] ?? null,
                    onChange: (f) => onUploadFile(cfg.label, f),
                }))}
                makeUploadProps={(label) => {
                    const config = csvConfigs.find(
                        (cfg) => cfg.label === label
                    );
                    return config ? makeUploadProps(label, config.onParse) : {};
                }}
                finalized={finalized}
                readyToCreate={readyToCreate}
                pdfUrl={previewUrl}
            >
                <PDFViewer pdfUrl={previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
