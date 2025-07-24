import React, { useState } from 'react';
import { Typography, Spin } from 'antd';
import type { UploadProps } from 'antd/es/upload';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap } from '@/constants/reportConfig/managementReportConfig';
import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';
import type { ReportKey } from '@/constants/reportConfig/managementReportConfig';

// =============================
// 帳簿PDF生成画面のベースコンポーネント
// =============================

// === 型定義グループ化 ===
// CSVファイルの設定情報
type CsvConfig = {
    config: {
        label: string; // CSVのラベル名
        onParse: (csvText: string) => void; // CSVパース時のコールバック
    };
    required: boolean; // 必須かどうか
};

// ステップバーの状態管理
type StepProps = {
    steps: string[]; // ステップ名一覧
    currentStep: number; // 現在のステップ番号
    setCurrentStep: (step: number) => void; // ステップ変更関数
};

// ファイルアップロード関連の状態管理
type FileProps = {
    csvConfigs: CsvConfig[]; // CSV設定一覧
    files: { [csvLabel: string]: File | null }; // ラベルごとのファイル
    onUploadFile: (label: string, file: File | null) => void; // ファイルアップロード時のコールバック
};

// PDFプレビュー関連の状態管理
type PreviewProps = {
    previewUrl: string | null; // プレビュー用PDFのURL
    setPreviewUrl: (url: string | null) => void; // プレビューURL更新関数
};

// モーダル表示状態管理
type ModalProps = {
    modalOpen: boolean;
    setModalOpen: (b: boolean) => void;
};

// 帳簿生成完了状態管理
type FinalizedProps = {
    finalized: boolean;
    setFinalized: (b: boolean) => void;
};

// ローディング状態管理
type LoadingProps = {
    loading: boolean;
    setLoading: (b: boolean) => void;
};

// ReportBaseコンポーネントのprops型
type ReportBaseProps = {
    step: StepProps;
    file: FileProps;
    preview: PreviewProps;
    modal: ModalProps;
    finalized: FinalizedProps;
    loading: LoadingProps;
    generatePdf: () => Promise<string>; // PDF生成関数
    reportKey: ReportKey; // 帳簿種別キー
};

const ReportBase: React.FC<ReportBaseProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    generatePdf,
    reportKey,
}) => {
    // 各CSVファイルのバリデーション結果を管理
    const [validationResults, setValidationResults] = useState<{
        [label: string]: 'valid' | 'invalid' | 'unknown';
    }>({});

    // 帳簿生成ボタンの活性判定（全CSVが条件を満たしているか）
    const readyToCreate = file.csvConfigs.every((entry) => {
        const label = entry.config.label;
        const fileObj = file.files[label];
        const validation = validationResults[label];

        if (fileObj) {
            // ファイルがアップロードされていればバリデーション必須
            return validation === 'valid';
        } else {
            // 未アップロードなら、必須CSVのみNG
            return !entry.required;
        }
    });

    // ファイル削除時の処理
    const handleRemoveFile = (label: string) => {
        file.onUploadFile(label, null);
        setValidationResults((prev) => ({
            ...prev,
            [label]: 'unknown',
        }));
    };

    // アップロード用props生成（バリデーション・パース処理含む）
    const makeUploadProps = (
        label: string,
        parser: (csvText: string) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (fileObj) => {
            // ファイル選択時の処理
            file.onUploadFile(label, fileObj);

            if (!fileObj) {
                // ファイル未選択時はバリデーション結果をunknownに
                setValidationResults((prev) => ({
                    ...prev,
                    [label]: 'unknown',
                }));
                return false;
            }

            // CSV内容を読み込んでバリデーション
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const result = identifyCsvType(text); // CSV種別判定

                const isCorrect = isCsvMatch(result, label); // ラベルと一致するか

                setValidationResults((prev) => ({
                    ...prev,
                    [label]: isCorrect ? 'valid' : 'invalid',
                }));

                if (isCorrect) {
                    // 正しいCSVならパース処理実行
                    parser(text);
                }
            };
            reader.readAsText(fileObj);
            return false;
        },
    });

    // 帳簿PDF生成処理
    const handleGenerate = async () => {
        modal.setModalOpen(true); // モーダル表示
        loading.setLoading(true); // ローディング開始

        try {
            const url = await generatePdf(); // PDF生成
            preview.setPreviewUrl(url); // プレビューURLセット
            finalized.setFinalized(true); // 完了状態セット
        } catch (err) {
            // エラー時はコンソール出力
            console.error('PDF生成エラー:', err);
        } finally {
            loading.setLoading(false); // ローディング終了
            setTimeout(() => {
                modal.setModalOpen(false); // モーダル自動クローズ
            }, 1000);
        }
    };

    // 画面描画
    return (
        <>
            {/* ステップバー付きモーダル */}
            <ReportStepperModal
                open={modal.modalOpen}
                steps={step.steps}
                currentStep={step.currentStep}
                onNext={() => {
                    // 最終ステップでモーダル閉じてステップ初期化
                    if (step.currentStep === step.steps.length - 1) {
                        modal.setModalOpen(false);
                        step.setCurrentStep(0);
                    }
                }}
            >
                {/* ステップごとの表示内容 */}
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

            {/* 帳簿管理ページレイアウト */}
            <ReportManagePageLayout
                onGenerate={handleGenerate} // 帳簿生成ボタン
                uploadFiles={file.csvConfigs.map((entry) => {
                    const label = entry.config.label;
                    return {
                        label,
                        file: file.files[label] ?? null,
                        onChange: (f) => {
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
                makeUploadProps={(label) => {
                    // ラベルに対応するUploadProps生成
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
            >
                {/* PDFプレビュー表示 */}
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
