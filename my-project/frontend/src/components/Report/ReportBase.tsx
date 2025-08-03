import React, { useState } from 'react';
import { Typography, Spin } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap } from '@/constants/reportConfig/managementReportConfig';
import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';
import type { ReportKey } from '@/constants/reportConfig/managementReportConfig';

// 通知ユーティリティをインポート
import { notifySuccess, notifyError, notifyInfo, notifyWarning } from '@/utils/notify';

type CsvConfig = {
    config: {
        label: string;
        onParse: (csvText: string) => void;
    };
    required: boolean;
};

type CsvConfigEntry = CsvConfig;

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
    const [excelUrl, setExcelUrl] = useState<string | null>(null);
    const [excelFileName, setExcelFileName] = useState<string>('output.xlsx');
    const [validationResults, setValidationResults] = useState<{
        [label: string]: 'valid' | 'invalid' | 'unknown';
    }>({});

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
            const a = document.createElement('a');
            a.href = excelUrl;
            a.download = excelFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(excelUrl);
            setExcelUrl(null);
        } else {
            notifyInfo('ダウンロード不可', 'Excelファイルがありません。');
        }
    };

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
                } else {
                    notifyWarning(
                        'CSVファイル形式エラー',
                        `「${label}」のファイル形式が正しくありません。`
                    );
                }
            };
            reader.readAsText(fileObj);
            return false;
        },
    });

    const handleGenerate = async () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        try {
            // 日本語ラベルを英語キーにマッピング
            const labelToEnglishKey: Record<string, string> = {
                '出荷一覧': 'shipment',
                '受入一覧': 'receive',
                'ヤード一覧': 'yard',
            };

            const formData = new FormData();
            Object.keys(file.files).forEach((label) => {
                const fileObj = file.files[label];
                if (fileObj) {
                    const englishKey = labelToEnglishKey[label] || label;
                    formData.append(englishKey, fileObj);
                }
            });
            formData.append('report_key', reportKey);

            // FormDataの中身を全部ログに出す
            console.log('FormData contents:');
            Object.keys(file.files).forEach((label) => {
                const fileObj = file.files[label];
                if (fileObj) {
                    const englishKey = labelToEnglishKey[label] || label;
                    console.log(`FormData key: ${englishKey}, file name: ${fileObj.name}`);
                }
            });
            console.log(`FormData key: report_key, value: ${reportKey}`);

            const response = await fetch('/ledger_api/report/manage', {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                // サーバーから422などが返ってきた場合、詳細を取得して通知
                let errorMsg = '帳簿作成失敗';
                try {
                    const errorJson = await response.json();
                    errorMsg = errorJson?.detail || errorMsg;
                    if (errorJson?.hint) {
                        notifyInfo('ヒント', errorJson.hint);
                    }
                } catch {
                    // JSONでなければスルー
                }
                throw new Error(errorMsg);
            }

            const blob = await response.blob();

            // ヘッダーからファイル名を取得
            const disposition = response.headers.get('Content-Disposition');
            let fileName = 'output.xlsx';
            if (disposition) {
                const matchStar = disposition.match(/filename\*=UTF-8''([^;]+)/);
                if (matchStar) {
                    fileName = decodeURIComponent(matchStar[1]);
                } else {
                    const match = disposition.match(/filename="?([^"]+)"?/);
                    if (match && match[1]) {
                        fileName = decodeURIComponent(match[1]);
                    }
                }
            }

            const excelObjectUrl = window.URL.createObjectURL(blob);
            setExcelUrl(excelObjectUrl);
            setExcelFileName(fileName);

            finalized.setFinalized(true);

            // ★成功通知
            notifySuccess('帳簿作成成功', `${fileName} をダウンロードできます。`);
        } catch (err) {
            console.error('帳簿作成失敗エラー:', err);
            notifyError('帳簿作成失敗', err instanceof Error ? err.message : String(err));
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
                uploadFiles={file.csvConfigs.map((entry: CsvConfigEntry): UploadFileConfig => {
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
                        (e: CsvConfigEntry) => e.config.label === label
                    );
                    return entry
                        ? makeUploadProps(label, entry.config.onParse)
                        : {};
                }}
                finalized={finalized.finalized}
                readyToCreate={readyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={preview.previewUrl}
                excelUrl={excelUrl}
            >
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
