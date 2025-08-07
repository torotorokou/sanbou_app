import React from 'react';
import BaseReportComponent, { type BaseReportComponentProps, type ReportGenerationCallbacks } from '../BaseReportComponent';
import { useWorkflow } from '../context/WorkflowContext';
import CsvUploadService from '../services/CsvUploadService';
import { useReportBaseBusiness } from '../../../hooks/report';
import type { ReportKey } from '../../../constants/reportConfig/managementReportConfig';

/**
 * インタラクティブレポート専用ベースコンポーネント
 * 
 * 🎯 責任:
 * - WorkflowContextとの統合
 * - 段階的なユーザー入力の管理
 * - バックエンド通信の制御
 * - エラーハンドリングと復旧処理
 * 
 * 🛡️ 安全性:
 * - モーダルの途中閉じを禁止
 * - ステップ間の状態整合性を保証
 * - エラー時の適切な復旧処理
 */
export interface InteractiveReportBaseProps extends Omit<BaseReportComponentProps, 'customHandleGenerate' | 'customContentRenderer'> {
    /** インタラクティブワークフローコンポーネント */
    WorkflowComponent: React.ComponentType<{ currentStep: number; reportKey: ReportKey }>;

    /** カスタム初期化処理（オプション） */
    onInitialize?: () => void;

    /** カスタム完了処理（オプション） */
    onComplete?: (result: unknown) => void;

    /** デバッグモード */
    debugMode?: boolean;
}

const InteractiveReportBase: React.FC<InteractiveReportBaseProps> = ({
    WorkflowComponent,
    onInitialize,
    onComplete,
    debugMode = false,
    ...baseProps
}) => {
    const { state, actions } = useWorkflow();
    const { reportKey } = baseProps;

    // デバッグログ出力
    const debugLog = React.useCallback((message: string, data?: unknown) => {
        if (debugMode) {
            console.log(`[InteractiveReportBase:${reportKey}] ${message}`, data);
        }
    }, [debugMode, reportKey]);

    // 初期化処理
    React.useEffect(() => {
        if (onInitialize) {
            debugLog('Initializing interactive report');
            onInitialize();
        }
    }, [onInitialize, debugLog]);

    // カスタムレポート生成処理
    const customHandleGenerate = React.useCallback((
        business: unknown,
        callbacks: ReportGenerationCallbacks,
        reportKey: string
    ) => {
        debugLog('Starting interactive report generation');

        // 初期化
        actions.setLoading(true);
        actions.setError(null);
        actions.setCurrentStep(0);
        callbacks.onStart();

        // nullファイルを除外してRecord<string, File>形式に変換
        const validFiles = Object.entries(baseProps.file.files)
            .filter(([, file]) => file !== null)
            .reduce((acc, [key, file]) => {
                acc[key] = file as File;
                return acc;
            }, {} as Record<string, File>);

        // バックエンドにCSVをアップロードして初期データを取得
        CsvUploadService.uploadAndStart(
            reportKey,
            validFiles,
            {
                onStart: () => {
                    debugLog('Backend CSV processing started');
                },
                onSuccess: (data) => {
                    debugLog('Backend CSV processing completed', data);
                    actions.setBackendData(data as Record<string, unknown>);
                    actions.setLoading(false);
                    callbacks.onSuccess();
                },
                onError: (error) => {
                    debugLog('Backend CSV processing failed', error);
                    actions.setError(error);
                    actions.setLoading(false);
                },
                onComplete: () => {
                    debugLog('Backend CSV processing completed');
                    callbacks.onComplete();
                }
            }
        );
    }, [actions, baseProps.file.files, debugLog]);

    // カスタムコンテンツレンダラー
    const customContentRenderer = React.useCallback((stepIndex: number) => {
        debugLog(`Rendering step ${stepIndex}`);
        return (
            <WorkflowComponent
                currentStep={stepIndex}
                reportKey={reportKey}
            />
        );
    }, [WorkflowComponent, reportKey, debugLog]);

    // ワークフロー完了時の処理
    React.useEffect(() => {
        if (state.currentStep === baseProps.step.currentStep && onComplete && !state.loading && !state.error) {
            const isLastStep = baseProps.step.currentStep >= (baseProps.modal.modalOpen ? 4 : 0); // 5ステップ想定
            if (isLastStep) {
                debugLog('Workflow completed');
                onComplete(state.backendData);
            }
        }
    }, [state.currentStep, state.loading, state.error, state.backendData, baseProps.step.currentStep, baseProps.modal.modalOpen, onComplete, debugLog]);

    // エラー発生時の処理
    React.useEffect(() => {
        if (state.error) {
            debugLog('Error occurred in workflow', state.error);
        }
    }, [state.error, debugLog]);

    return (
        <BaseReportComponent
            {...baseProps}
            customHandleGenerate={customHandleGenerate}
            customContentRenderer={customContentRenderer}
            onModalClose={() => {
                debugLog('Modal closed, resetting workflow state');
                // ワークフロー状態をリセット
                actions.setCurrentStep(0);
                actions.setError(null);
                actions.setLoading(false);
                actions.setBackendData(null);
                baseProps.onModalClose?.();
            }}
        />
    );
};

export default InteractiveReportBase;
