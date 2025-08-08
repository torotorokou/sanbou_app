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
import { useReportManager } from './useReportManager';
import { ReportModeService } from '../../services/reportModeService';
import type { ReportKey } from '../../constants/reportConfig';
import type { 
    InteractiveProcessState, 
    InteractiveResult,
    InteractiveStep,
    UserSelections
} from '../../pages/types/interactiveMode';
import type { 
    ReportGenerationMode,
    ReportModeInfo 
} from '../../pages/types/reportMode';
import type { 
    ReportProcessResult,
    ReportCallbacks 
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
    continueInteractiveProcess: (userInput: Record<string, unknown>) => Promise<void>;
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
    const [interactiveState, setInteractiveState] = useState<InteractiveProcessState>({
        currentStep: -1, // INTERACTIVE_STEPS.INITIAL
        isLoading: false,
    });

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
        const newModeInfo = ReportModeService.getModeInfo(baseManager.selectedReport);
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
    }, [isInteractiveMode, interactiveState.currentStep, onInteractiveStepChange]);

    // ==============================
    // 🎯 アクション関数
    // ==============================

    /**
     * レポート生成を実行（モードに応じて自動で分岐）
     */
    const generateReport = useCallback(async () => {
        const callbacks: ReportCallbacks = {
            onStart: () => {
                baseManager.setIsLoading(true);
                baseManager.setIsModalOpen(true);
                baseManager.setCurrentStep(0);
                
                if (isInteractiveMode) {
                    setInteractiveState(prev => ({
                        ...prev,
                        isLoading: true,
                        currentStep: 0, // INTERACTIVE_STEPS.PROCESSING
                    }));
                }
            },
            onProgress: (step: number, message?: string) => {
                if (isInteractiveMode) {
                    setInteractiveState(prev => ({
                        ...prev,
                        currentStep: step as InteractiveStep,
                        error: undefined,
                    }));
                } else {
                    baseManager.setCurrentStep(step);
                }
                console.log(`Progress: Step ${step}, Message: ${message}`);
            },
            onComplete: () => {
                baseManager.setIsLoading(false);
                baseManager.setIsFinalized(true);
                
                if (isInteractiveMode) {
                    setInteractiveState(prev => ({
                        ...prev,
                        isLoading: false,
                    }));
                }
            },
            onError: (error: string) => {
                baseManager.setIsLoading(false);
                baseManager.setIsModalOpen(false);
                
                if (isInteractiveMode) {
                    setInteractiveState(prev => ({
                        ...prev,
                        isLoading: false,
                        error,
                    }));
                }
                console.error('Report generation error:', error);
            },
        };

        try {
            // nullファイルを除外してAPIに渡す
            const filteredCsvFiles: Record<string, File> = {};
            Object.entries(baseManager.csvFiles).forEach(([key, file]) => {
                if (file !== null) {
                    filteredCsvFiles[key] = file;
                }
            });

            const result = await ReportModeService.generateReport(
                filteredCsvFiles,
                baseManager.selectedReport,
                callbacks
            );

            setLastResult(result);

            if (result.success && result.previewUrl) {
                baseManager.setPreviewUrl(result.previewUrl);
            }

        } catch (error) {
            callbacks.onError(error instanceof Error ? error.message : 'Unknown error');
        }
    }, [baseManager, isInteractiveMode]);

    /**
     * インタラクティブ処理の継続
     */
    const continueInteractiveProcess = useCallback(async (
        userInput: Record<string, unknown>
    ) => {
        if (!isInteractiveMode) {
            throw new Error('Not in interactive mode');
        }

        // ユーザー入力を適切な型に変換
        const convertedUserInput: Record<string, string | number | boolean | string[]> = {};
        Object.entries(userInput).forEach(([key, value]) => {
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                convertedUserInput[key] = value;
            } else if (Array.isArray(value) && value.every(item => typeof item === 'string')) {
                convertedUserInput[key] = value as string[];
            } else {
                convertedUserInput[key] = String(value);
            }
        });

        setInteractiveState(prev => ({
            ...prev,
            isLoading: true,
            userSelections: { ...prev.userSelections, ...convertedUserInput },
        }));

        try {
            const processor = ReportModeService.getInteractiveProcessor(baseManager.selectedReport);
            
            const result: InteractiveResult = await processor.continueInteractiveProcess(
                userInput,
                {
                    onStart: () => {},
                    onProgress: (step: number) => {
                        setInteractiveState(prev => ({ ...prev, currentStep: step as InteractiveStep }));
                    },
                    onComplete: () => {
                        setInteractiveState(prev => ({ ...prev, isLoading: false }));
                    },
                    onError: (error: string) => {
                        setInteractiveState(prev => ({ 
                            ...prev, 
                            isLoading: false, 
                            error 
                        }));
                    },
                }
            );

            if (result.success) {
                if (result.previewUrl) {
                    baseManager.setPreviewUrl(result.previewUrl);
                }
                baseManager.setIsFinalized(true);
            }

        } catch (error) {
            setInteractiveState(prev => ({
                ...prev,
                isLoading: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            }));
        }
    }, [isInteractiveMode, baseManager]);

    /**
     * インタラクティブ状態のリセット
     */
    const resetInteractiveState = useCallback(() => {
        setInteractiveState({
            currentStep: -1, // INTERACTIVE_STEPS.INITIAL
            isLoading: false,
        });
    }, []);

    // ==============================
    // � ヘルパー関数
    // ==============================

    /**
     * 必須CSVファイルがアップロード済みかチェック
     */
    const checkRequiredCsvsUploaded = useCallback((): boolean => {
        return baseManager.selectedConfig.csvConfigs
            .filter((entry: { required: boolean }) => entry.required)
            .every((entry: { config: { label: string } }) => baseManager.csvFiles[entry.config.label]);
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
