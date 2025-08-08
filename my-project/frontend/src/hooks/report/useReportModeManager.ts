// /app/src/hooks/report/useReportModeManager.ts

/**
 * モード対応レポート管理フック
 *
 * 🎯 目的：
 * - 既存のuseReportManagerを拡張し、モード分岐に対応
 * - 自動・インタラクティブモードの統合管理
 * - SOLID原則に基づく設計で拡張性を確保
 */

import { useState, useEffect, useCallback } from 'react';
import { notification } from 'antd';
import { useReportManager } from './useReportManager';
import { ReportModeService } from '../../services/reportModeService';
import { getInteractiveApiService } from '../../services/interactiveApiService';
import { INTERACTIVE_STEPS } from '../../pages/types/interactiveMode';
import type { ReportKey } from '../../constants/reportConfig';
import type {
    InteractiveProcessState,
    InteractiveStep,
    UserSelections,
    SessionData,
} from '../../pages/types/interactiveMode';
import type {
    ReportGenerationMode,
    ReportModeInfo,
} from '../../pages/types/reportMode';
import type {
    ReportProcessResult,
    ReportCallbacks,
} from '../../services/reportModeService';

// ==============================
// 🔧 型定義
// ==============================

interface UseReportModeManagerOptions {
    initialReportKey?: ReportKey;
    onModeChange?: (mode: ReportGenerationMode) => void;
    onInteractiveStepChange?: (step: number) => void;
}

interface ReportModeManagerReturn {
    // 基本レポート管理（既存機能）
    selectedReport: ReportKey;
    csvFiles: Record<string, File | null>;
    currentStep: number;
    previewUrl: string | null;
    isFinalized: boolean;
    isModalOpen: boolean;
    isLoading: boolean;
    selectedConfig: unknown;

    // モード関連の新機能
    modeInfo: ReportModeInfo;
    isInteractiveMode: boolean;
    interactiveState: InteractiveProcessState;

    // アクション（既存）
    changeReport: (reportKey: string) => void;
    uploadCsvFile: (label: string, file: File | null) => void;
    setCurrentStep: (step: number) => void;
    setPreviewUrl: (url: string | null) => void;
    setIsFinalized: (finalized: boolean) => void;
    setIsModalOpen: (open: boolean) => void;
    setIsLoading: (loading: boolean) => void;

    // 新しいアクション
    generateReport: () => Promise<void>;
    continueInteractiveProcess: (
        userInput: Record<string, unknown>
    ) => Promise<void>;
    resetInteractiveState: () => void;

    // ヘルパー
    areRequiredCsvsUploaded: () => boolean;
    getReportBaseProps: () => unknown;
}

// ==============================
// 🎮 メインフック
// ==============================

export const useReportModeManager = (
    options: UseReportModeManagerOptions = {}
): ReportModeManagerReturn => {
    const {
        initialReportKey = 'factory_report',
        onModeChange,
        onInteractiveStepChange,
    } = options;

    // 既存のuseReportManagerを活用
    const baseManager = useReportManager(initialReportKey);

    // インタラクティブモード専用の状態
    const [interactiveState, setInteractiveState] =
        useState<InteractiveProcessState>({
            currentStep: INTERACTIVE_STEPS.INITIAL,
            isLoading: false,
        });

    // インタラクティブAPIサービス
    const interactiveApiService = getInteractiveApiService();

    // セッション管理
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [sessionData, setSessionData] = useState<SessionData>({});

    // 最新の処理結果（将来の拡張用）
    const [, setLastResult] = useState<ReportProcessResult | null>(null);

    // 現在のモード情報を取得
    const modeInfo = ReportModeService.getModeInfo(baseManager.selectedReport);
    const isInteractiveMode = modeInfo.isInteractive;

    // ==============================
    // 🔄 エフェクト
    // ==============================

    // レポートタイプ変更時のモード切り替え
    useEffect(() => {
        const newModeInfo = ReportModeService.getModeInfo(
            baseManager.selectedReport
        );
        onModeChange?.(newModeInfo.mode);

        // インタラクティブモードでない場合は状態をリセット
        if (!newModeInfo.isInteractive) {
            resetInteractiveState();
        }
    }, [baseManager.selectedReport, onModeChange]);

    // インタラクティブステップ変更の通知
    useEffect(() => {
        if (isInteractiveMode) {
            onInteractiveStepChange?.(interactiveState.currentStep);
        }
    }, [
        isInteractiveMode,
        interactiveState.currentStep,
        onInteractiveStepChange,
    ]);

    // ==============================
    // 🎯 アクション関数
    // ==============================

    /**
     * レポート生成を実行（最適化されたAPI通信）
     */
    const generateReport = useCallback(async () => {
        try {
            baseManager.setIsLoading(true);
            baseManager.setIsModalOpen(true);
            baseManager.setCurrentStep(0);

            // nullファイルを除外してAPIに渡す
            const filteredCsvFiles: Record<string, File> = {};
            Object.entries(baseManager.csvFiles).forEach(([key, file]) => {
                if (file !== null) {
                    filteredCsvFiles[key] = file;
                }
            });

            if (isInteractiveMode) {
                // インタラクティブモード - 専用API使用
                setInteractiveState((prev) => ({
                    ...prev,
                    isLoading: true,
                    currentStep: INTERACTIVE_STEPS.PROCESSING,
                }));

                const response =
                    await interactiveApiService.startInteractiveProcess({
                        reportKey: baseManager.selectedReport,
                        csvFiles: filteredCsvFiles,
                    });

                // セッション情報を保存
                setSessionId(response.sessionInfo.sessionId);
                setSessionData(response.sessionInfo.sessionData);

                // ユーザー入力が必要な場合
                if (response.nextStep === INTERACTIVE_STEPS.USER_INPUT) {
                    setInteractiveState((prev) => ({
                        ...prev,
                        isLoading: false,
                        currentStep: response.nextStep as InteractiveStep,
                        interactions: response.interactions,
                        data: response.initialData,
                    }));
                } else {
                    // 追加処理が必要な場合
                    setInteractiveState((prev) => ({
                        ...prev,
                        currentStep: response.nextStep as InteractiveStep,
                    }));
                }
            } else {
                // 自動モード - 既存のReportModeService使用
                const callbacks: ReportCallbacks = {
                    onStart: () => {},
                    onProgress: (step: number, message?: string) => {
                        baseManager.setCurrentStep(step);
                        console.log(
                            `Progress: Step ${step}, Message: ${message}`
                        );
                    },
                    onComplete: () => {
                        baseManager.setIsLoading(false);
                        baseManager.setIsFinalized(true);
                    },
                    onError: (error: string) => {
                        baseManager.setIsLoading(false);
                        baseManager.setIsModalOpen(false);
                        console.error('Report generation error:', error);
                    },
                };

                const result = await ReportModeService.generateReport(
                    filteredCsvFiles,
                    baseManager.selectedReport,
                    callbacks
                );

                setLastResult(result);

                if (result.success && result.previewUrl) {
                    baseManager.setPreviewUrl(result.previewUrl);
                }
            }
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : 'Unknown error';
            notification.error({
                message: 'レポート生成エラー',
                description: errorMessage,
            });

            baseManager.setIsLoading(false);
            baseManager.setIsModalOpen(false);

            if (isInteractiveMode) {
                setInteractiveState((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: errorMessage,
                }));
            }
        }
    }, [baseManager, isInteractiveMode, interactiveApiService]);

    /**
     * インタラクティブ処理の継続（最適化されたAPI通信）
     */
    const continueInteractiveProcess = useCallback(
        async (userInput: Record<string, unknown>) => {
            if (!isInteractiveMode || !sessionId) {
                throw new Error('Not in interactive mode or no active session');
            }

            try {
                // ユーザー入力を適切な型に変換
                const convertedUserInput: UserSelections = {};
                Object.entries(userInput).forEach(([key, value]) => {
                    if (
                        typeof value === 'string' ||
                        typeof value === 'number' ||
                        typeof value === 'boolean'
                    ) {
                        convertedUserInput[key] = value;
                    } else if (
                        Array.isArray(value) &&
                        value.every((item) => typeof item === 'string')
                    ) {
                        convertedUserInput[key] = value as string[];
                    } else {
                        convertedUserInput[key] = String(value);
                    }
                });

                setInteractiveState((prev) => ({
                    ...prev,
                    isLoading: true,
                    userSelections: {
                        ...prev.userSelections,
                        ...convertedUserInput,
                    },
                }));

                const response =
                    await interactiveApiService.updateInteractiveProcess({
                        sessionId,
                        userInput: convertedUserInput,
                        currentStep: interactiveState.currentStep,
                    });

                if (response.isComplete) {
                    // 最終完了処理
                    const finalResponse =
                        await interactiveApiService.completeInteractiveProcess({
                            sessionId,
                        });

                    setInteractiveState((prev) => ({
                        ...prev,
                        isLoading: false,
                        currentStep: INTERACTIVE_STEPS.COMPLETED,
                    }));

                    if (finalResponse.downloadUrl) {
                        baseManager.setPreviewUrl(finalResponse.downloadUrl);
                    }
                    baseManager.setIsFinalized(true);

                    // セッションを清理
                    setSessionId(null);
                    setSessionData({});
                } else {
                    // 次のステップに進む
                    setInteractiveState((prev) => ({
                        ...prev,
                        isLoading: false,
                        currentStep: response.nextStep as InteractiveStep,
                        interactions: response.interactions,
                        data: response.data,
                    }));
                }
            } catch (error) {
                const errorMessage =
                    error instanceof Error ? error.message : 'Unknown error';
                notification.error({
                    message: 'インタラクティブ処理エラー',
                    description: errorMessage,
                });

                setInteractiveState((prev) => ({
                    ...prev,
                    isLoading: false,
                    error: errorMessage,
                }));
            }
        },
        [
            isInteractiveMode,
            sessionId,
            interactiveState.currentStep,
            interactiveApiService,
            baseManager,
        ]
    );

    /**
     * インタラクティブ状態のリセット
     */
    const resetInteractiveState = useCallback(() => {
        setInteractiveState({
            currentStep: INTERACTIVE_STEPS.INITIAL,
            isLoading: false,
        });

        // セッション情報もクリア
        if (sessionId) {
            interactiveApiService.clearSession(sessionId);
            setSessionId(null);
            setSessionData({});
        }
    }, [sessionId, interactiveApiService]);

    // ==============================
    // � ヘルパー関数
    // ==============================

    /**
     * 必須CSVファイルがアップロード済みかチェック
     */
    const checkRequiredCsvsUploaded = useCallback((): boolean => {
        return baseManager.selectedConfig.csvConfigs
            .filter((entry: { required: boolean }) => entry.required)
            .every(
                (entry: { config: { label: string } }) =>
                    baseManager.csvFiles[entry.config.label]
            );
    }, [baseManager.selectedConfig.csvConfigs, baseManager.csvFiles]);

    // ==============================
    // �🎁 戻り値
    // ==============================

    return {
        // 基本レポート管理（個別にマッピング）
        selectedReport: baseManager.selectedReport,
        csvFiles: baseManager.csvFiles,
        currentStep: baseManager.currentStep,
        previewUrl: baseManager.previewUrl,
        isFinalized: baseManager.isFinalized,
        isModalOpen: baseManager.isModalOpen,
        isLoading: baseManager.isLoading,
        selectedConfig: baseManager.selectedConfig,

        // アクション関数
        changeReport: baseManager.changeReport,
        uploadCsvFile: baseManager.uploadCsvFile,
        setCurrentStep: baseManager.setCurrentStep,
        setPreviewUrl: baseManager.setPreviewUrl,
        setIsFinalized: baseManager.setIsFinalized,
        setIsModalOpen: baseManager.setIsModalOpen,
        setIsLoading: baseManager.setIsLoading,

        // ヘルパー関数
        areRequiredCsvsUploaded: checkRequiredCsvsUploaded,
        getReportBaseProps: baseManager.getReportBaseProps,

        // モード関連の新機能
        modeInfo,
        isInteractiveMode,
        interactiveState,

        // 拡張されたアクション
        generateReport,
        continueInteractiveProcess,
        resetInteractiveState,
    };
};
