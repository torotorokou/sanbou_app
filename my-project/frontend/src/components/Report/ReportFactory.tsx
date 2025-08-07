import React from 'react';
import { getReportType } from '../../constants/reportConfig/managementReportConfig';
import type { ReportBaseProps } from '../../types/reportBase';
import BaseReportComponent from './BaseReportComponent';
import InteractiveWorkflowFactory, { registerDefaultWorkflows } from './individual_process/InteractiveWorkflowFactory';
import { WorkflowProvider, useWorkflow } from './context/WorkflowContext';
import CsvUploadService, { type ZipProcessResult } from './services/CsvUploadService';
import { createStepController, type StepController } from './controllers/StepController';

// 拡張されたprops型（getValidationResultを含む）
interface ExtendedReportBaseProps extends ReportBaseProps {
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';
}

// ワークフローラッパーコンポーネント
interface WorkflowWrapperProps extends ReportBaseProps {
    currentStep: number;
    stepConfig?: unknown;
    WorkflowComponent: React.ComponentType<ReportBaseProps & { currentStep: number; stepConfig?: unknown }>;
    backendData?: unknown;
}

const InteractiveWorkflowWrapper: React.FC<WorkflowWrapperProps> = (props) => {
    const { WorkflowComponent, backendData, ...otherProps } = props;
    const { actions } = useWorkflow();

    // バックエンドデータが設定されたらワークフローコンテキストに反映
    React.useEffect(() => {
        if (backendData) {
            actions.setBackendData(backendData as Record<string, unknown>);
        }
    }, [backendData, actions]);

    return <WorkflowComponent {...otherProps} />;
};

/**
 * レポートファクトリーコンポーネント
 * シンプルレポートとインタラクティブレポート共通のCSVアップロード処理を統合
 * レポートタイプに応じて適切な後続処理フローを選択
 * 
 * 🎯 責任：
 * - レポートタイプの自動判定
 * - 共通のCSVアップロード処理
 * - シンプル/インタラクティブフローの分岐管理
 */
const ReportFactory: React.FC<ExtendedReportBaseProps> = (props) => {
    const { reportKey } = props;
    const reportType = getReportType(reportKey);

    console.log(`[ReportFactory] reportKey: ${reportKey}, type: ${reportType}`);

    // デフォルトワークフローを登録
    React.useEffect(() => {
        registerDefaultWorkflows();
    }, []);

    // バックエンドレスポンス管理（インタラクティブレポート用）
    const [backendResponse, setBackendResponse] = React.useState<unknown>(null);

    // ZIP処理結果管理（共通）
    const [zipResult, setZipResult] = React.useState<ZipProcessResult | null>(null);

    // ステップコントローラー初期化
    const stepController = React.useMemo(() =>
        createStepController(
            reportKey,
            props.step.setCurrentStep,
            props.loading.setLoading,
            props.finalized.setFinalized
        ),
        [reportKey, props.step.setCurrentStep, props.loading.setLoading, props.finalized.setFinalized]
    );

    // ステップコントローラーリセット処理
    const handleStepControllerReset = () => {
        stepController.reset();
    };    // シンプル/インタラクティブ共通の処理ハンドラー
    const customHandleGenerate = async (business: unknown, callbacks: unknown) => {
        console.log(`[ReportFactory] Starting workflow for ${reportKey}, type: ${reportType}`);

        // callbacksの型安全性チェック
        const safeCallbacks = callbacks as {
            onStart: () => void;
            onComplete: () => void;
            onSuccess: () => void;
        };

        // CsvFilesをRecord<string, File>に変換（nullを除外）
        const validFiles: Record<string, File> = {};
        Object.entries(props.file.files).forEach(([key, file]) => {
            if (file) validFiles[key] = file;
        });

        // 共通のCSVアップロード処理
        const uploadResult = await CsvUploadService.uploadAndStart(
            reportKey,
            validFiles,
            {
                onStart: () => {
                    safeCallbacks.onStart();
                    stepController.onReportStart();
                },
                onSuccess: (data) => {
                    console.log(`[ReportFactory] Upload success for ${reportType} report:`, data);

                    // ZIP処理結果かどうかを判定
                    const zipData = data as ZipProcessResult;
                    if (zipData.type === 'zip' && zipData.success) {
                        // ZIP処理結果を保存
                        setZipResult(zipData);

                        // PDFプレビューURLが生成されていれば設定
                        if (zipData.pdfPreviewUrl) {
                            props.preview.setPreviewUrl(zipData.pdfPreviewUrl);
                        }

                        console.log(`[ReportFactory] ZIP processed - Excel: ${zipData.hasExcel}, PDF: ${zipData.hasPdf}`);

                        // ステップコントローラーでバックエンド完了処理
                        stepController.onBackendComplete(true);
                    }

                    if (reportType === 'auto') {
                        // シンプルレポート：完了
                        safeCallbacks.onSuccess();
                    } else {
                        // インタラクティブレポート：ワークフロー継続
                        if (zipData.type !== 'zip') {
                            // JSONデータの場合はワークフロー用
                            setBackendResponse(data);
                        }
                    }
                },
                onError: (error) => {
                    console.error('[ReportFactory] Upload error:', error);
                    stepController.onError(error);
                    safeCallbacks.onComplete();
                },
                onComplete: () => {
                    // シンプルレポートの処理完了
                    if (reportType === 'auto') {
                        console.log('[ReportFactory] Simple report processing completed');
                        safeCallbacks.onComplete();
                    }
                }
            }
        ); if (!uploadResult.success) {
            throw new Error(uploadResult.error || 'Upload failed');
        }
    };

    // レポートタイプに応じた処理フロー分岐
    if (reportType === 'auto') {
        // シンプルレポート：従来のBaseReportComponentをそのまま使用
        return (
            <BaseReportComponent
                {...props}
                customHandleGenerate={customHandleGenerate}
                zipResult={zipResult}
                onStepAdvance={handleStepControllerReset}
            />
        );
    }

    // インタラクティブレポート：ワークフロー処理を追加
    const WorkflowComponent = InteractiveWorkflowFactory.getWorkflowComponent(reportKey);

    if (!WorkflowComponent) {
        console.error(`Workflow component not found for report: ${reportKey}`);
        return (
            <div className="error-message">
                <h3>サポートされていないレポートタイプ</h3>
                <p>レポートタイプ「{reportKey}」のワークフローが見つかりません。</p>
            </div>
        );
    }

    // インタラクティブ処理用のカスタムコンテンツレンダラー
    const customContentRenderer = (stepIndex: number, stepConfig: unknown) => {
        return (
            <WorkflowProvider maxSteps={4}>
                <InteractiveWorkflowWrapper
                    {...props}
                    currentStep={stepIndex}
                    stepConfig={stepConfig}
                    WorkflowComponent={WorkflowComponent}
                    backendData={backendResponse}
                />
            </WorkflowProvider>
        );
    };

    return (
        <BaseReportComponent
            {...props}
            customHandleGenerate={customHandleGenerate}
            customContentRenderer={customContentRenderer}
            zipResult={zipResult}
            onStepAdvance={handleStepControllerReset}
        />
    );
};

export default ReportFactory;
