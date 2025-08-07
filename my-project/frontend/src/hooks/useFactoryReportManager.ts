// /app/src/hooks/useFactoryReportManager.ts
import { useState, useCallback } from 'react';
import type {
    FactoryReportKey,
    FactoryReportType,
} from '../constants/reportConfig/factoryReportConfig';
import {
    FACTORY_REPORT_KEYS,
    factoryReportConfigMap as configMap,
    getFactoryReportType,
} from '../constants/reportConfig/factoryReportConfig';

interface FactoryReportManagerState {
    selectedReport: FactoryReportKey;
    currentStep: number;
    csvFiles: File[];
    validationResults: Record<string, 'valid' | 'invalid' | 'unknown'>;
    isProcessing: boolean;
}

/**
 * 工場帳簿専用のレポートマネージャーフック
 *
 * 🎯 責任：
 * - 工場帳簿の状態管理
 * - CSV バリデーション
 * - ステップ制御
 * - レポート切り替え
 *
 * 📝 managementReportManagerとは独立した設計
 */
export const useFactoryReportManager = (
    defaultReportKey?: FactoryReportKey
) => {
    const [state, setState] = useState<FactoryReportManagerState>({
        selectedReport: defaultReportKey || 'performance_report',
        currentStep: 0,
        csvFiles: [],
        validationResults: {},
        isProcessing: false,
    });

    // レポート切り替え
    const changeReport = useCallback((reportKey: FactoryReportKey) => {
        setState((prev) => ({
            ...prev,
            selectedReport: reportKey,
            currentStep: 0,
            csvFiles: [],
            validationResults: {},
            isProcessing: false,
        }));
    }, []);

    // ステップ変更
    const setCurrentStep = useCallback((step: number) => {
        setState((prev) => ({ ...prev, currentStep: step }));
    }, []);

    // CSV ファイル設定
    const setCsvFiles = useCallback((files: File[]) => {
        setState((prev) => ({ ...prev, csvFiles: files }));
    }, []);

    // バリデーション結果設定
    const setValidationResults = useCallback(
        (results: Record<string, 'valid' | 'invalid' | 'unknown'>) => {
            setState((prev) => ({ ...prev, validationResults: results }));
        },
        []
    );

    // 処理状態設定
    const setIsProcessing = useCallback((processing: boolean) => {
        setState((prev) => ({ ...prev, isProcessing: processing }));
    }, []);

    // バリデーション結果取得
    const getValidationResult = useCallback(
        (label: string): 'valid' | 'invalid' | 'unknown' => {
            return state.validationResults[label] || 'unknown';
        },
        [state.validationResults]
    );

    // レポートベースプロパティ取得
    const getReportBaseProps = useCallback(() => {
        const reportConfig = configMap[state.selectedReport];
        const reportType = getFactoryReportType(state.selectedReport);

        return {
            reportKey: state.selectedReport,
            csvFiles: state.csvFiles,
            currentStep: state.currentStep,
            csvConfigs: reportConfig.csvConfigs,
            type: reportType,
            validationResults: state.validationResults,
            isProcessing: state.isProcessing,
            step: {
                steps: reportConfig.steps,
                currentStep: state.currentStep,
                setCurrentStep,
            },
            onUpload: setCsvFiles,
            onValidationChange: setValidationResults,
            onProcessingChange: setIsProcessing,
        };
    }, [
        state.selectedReport,
        state.csvFiles,
        state.currentStep,
        state.validationResults,
        state.isProcessing,
        setCurrentStep,
        setCsvFiles,
        setValidationResults,
        setIsProcessing,
    ]);

    // 現在のレポート設定取得
    const getCurrentReportConfig = useCallback(() => {
        return configMap[state.selectedReport];
    }, [state.selectedReport]);

    // レポートタイプ取得
    const getCurrentReportType = useCallback((): FactoryReportType => {
        return getFactoryReportType(state.selectedReport);
    }, [state.selectedReport]);

    // レポート定義取得
    const getCurrentReportDefinition = useCallback(() => {
        return FACTORY_REPORT_KEYS[state.selectedReport];
    }, [state.selectedReport]);

    return {
        // 状態
        selectedReport: state.selectedReport,
        currentStep: state.currentStep,
        csvFiles: state.csvFiles,
        validationResults: state.validationResults,
        isProcessing: state.isProcessing,

        // アクション
        changeReport,
        setCurrentStep,
        setCsvFiles,
        setValidationResults,
        setIsProcessing,

        // ヘルパー
        getValidationResult,
        getReportBaseProps,
        getCurrentReportConfig,
        getCurrentReportType,
        getCurrentReportDefinition,
    };
};

export default useFactoryReportManager;
