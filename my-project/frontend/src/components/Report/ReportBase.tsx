import React, { useState } from 'react';
import { Typography, Spin } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap } from '@/constants/reportConfig/managementReportConfig';
import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';
import type { ReportKey } from '@/constants/reportConfig/managementReportConfig';
import { downloadExcelFile } from './common/downloadExcel';
// 必要なら import type { CsvFileType } from './types';

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
    reportKey: ReportKey;
};

// ここでUploadFileConfig型を定義（もしくは既存型CsvFileTypeをimportして使う）
type UploadFileConfig = {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean;
    validationResult: 'valid' | 'invalid' | 'unknown';
    onRemove: () => void;
};


const ReportBase: React.FC<ReportBaseProps> = ({
    step, file, preview, modal, finalized, loading, generatePdf, reportKey
}) => {
    const [excelUrl, setExcelUrl] = useState<string | null>(null); // ←ここでOK
    const [validationResults, setValidationResults] = useState<{
        [label: string]: 'valid' | 'invalid' | 'unknown';
    }>({});
    // アップロード済みかつバリデーションOKなファイルのみ帳簿生成可
    const readyToCreate = file.csvConfigs.every((entry) => {
        const label = entry.config.label;
        const fileObj = file.files[label];
        const validation = validationResults[label];

        if (fileObj) {
            return validation === 'valid';
        } else {
            return !entry.required;
        }
    });

    const handleRemoveFile = (label: string) => {
        file.onUploadFile(label, null);
        setValidationResults((prev) => ({
            ...prev,
            [label]: 'unknown',
        }));
    };

    const handleDownloadExcel = () => {
        if (excelUrl) {
            window.open(excelUrl, '_blank');
        } else {
            // 必要に応じて警告
            alert('Excelファイルがありません。');
        }
    };

    // CSVアップロードprops生成
    const makeUploadProps = (
        label: string,
        parser: (csvText: string) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (fileObj) => {
            file.onUploadFile(label, fileObj);

            if (!fileObj) {
                setValidationResults((prev) => ({
                    ...prev,
                    [label]: 'unknown',
                }));
                return false;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const result = identifyCsvType(text);
                const isCorrect = isCsvMatch(result, label);

                setValidationResults((prev) => ({
                    ...prev,
                    [label]: isCorrect ? 'valid' : 'invalid',
                }));

                if (isCorrect) {
                    parser(text);
                }
            };
            reader.readAsText(fileObj);
            return false;
        },
    });

    // 帳簿生成処理（PDFプレビュー）
    // ...必要なimportは省略（あなたの既存ファイル構成に合わせて下さい）...

    const handleGenerate = async () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        try {
            const formData = new FormData();
            Object.entries(file.files).forEach(([label, fileObj]) => {
                if (fileObj) formData.append(label, fileObj);
            });
            formData.append('report_key', reportKey);

            console.log('帳簿作成API呼び出し:', { report_key: reportKey, files: file.files });

            const response = await fetch('/ledger_api/report/manage', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) throw new Error('帳簿作成失敗');

            const data = await response.json();
            const pdfUrl = data.result?.pdf_url;
            const excelUrl = data.result?.excel_url;

            preview.setPreviewUrl(pdfUrl);
            setExcelUrl(excelUrl); // Excel用URLをセット

            finalized.setFinalized(true);
        } catch (err) {
            console.error('帳簿作成失敗エラー:', err);
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
                onDownloadExcel={handleDownloadExcel}
                uploadFiles={file.csvConfigs.map((entry): UploadFileConfig => {
                    const label = entry.config.label;
                    return {
                        label,
                        file: file.files[label] ?? null,
                        onChange: (f: File | null) => {
                            file.onUploadFile(label, f);
                            if (f === null) {
                                setValidationResults((prev) => ({
                                    ...prev,
                                    [label]: 'unknown',
                                }));
                            }
                        },
                        required: entry.required,
                        validationResult: validationResults[label] ?? 'unknown',
                        onRemove: () => handleRemoveFile(label),
                    };
                })}
                makeUploadProps={(label: string): UploadProps => {
                    const entry = file.csvConfigs.find(
                        (e) => e.config.label === label
                    );
                    return entry
                        ? makeUploadProps(label, entry.config.onParse)
                        : {};
                }}
                finalized={finalized.finalized}
                readyToCreate={readyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={preview.previewUrl}
                excelUrl={excelUrl}  // ←ここを追加
            >
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
