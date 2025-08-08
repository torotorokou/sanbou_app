// /app/src/pages/report/ReportModeFactory.tsx

/**
 * モード対応工場レポートページ
 * 
 * 🎯 目的：
 * - 既存のReportFactoryを拡張し、モード分岐に対応
 * - 自動・インタラクティブモードの統合管理
 * - 既存機能との完全な後方互換性を保持
 */

import React from 'react';
import ReportModeBase from '../../components/Report/ReportModeBase';
import ReportHeader from '../../components/Report/common/ReportHeader';
import { useReportModeManager } from '../../hooks/report/useReportModeManager';
import type { ReportBaseProps } from '../../types/reportBase';

/**
 * モード対応工場レポートページ
 * 
 * 🔄 リファクタリング内容：
 * - useReportModeManagerで自動・インタラクティブモード統合
 * - ReportModeBaseで共通UI処理を統合
 * - 既存のReportFactoryと同等の機能を提供
 * 
 * 📝 実装の特徴：
 * - factory_reportは自動モード
 * - 必要に応じて他の帳票タイプも選択可能
 * - インタラクティブモードへの切り替えも対応
 */

const ReportModeFactory: React.FC = () => {
    // モード対応レポート管理フック
    const reportManager = useReportModeManager({
        initialReportKey: 'factory_report',
        onModeChange: (mode) => {
            console.log(`Mode changed to: ${mode}`);
        },
        onInteractiveStepChange: (step) => {
            console.log(`Interactive step changed to: ${step}`);
        },
    });

    // ==============================
    // � イベントハンドラー
    // ==============================

    /**
     * レポートタイプ変更ハンドラー
     */
    const handleChangeReportKey = (reportKey: string) => {
        reportManager.changeReport(reportKey);
    };

    // 型安全なconfig取得
    const selectedConfig = reportManager.selectedConfig as {
        steps?: string[];
        csvConfigs?: Array<{
            config: { label: string };
            required: boolean;
        }>;
    };

    // ==============================
    // �🎨 レンダリング
    // ==============================

    return (
        <>
            {/* ヘッダー（レポート選択・ステップ表示） */}
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={handleChangeReportKey}
                currentStep={reportManager.currentStep}
                pageGroup="factory"
            />

            {/* メインコンテンツ（モード対応） */}
            <ReportModeBase
                step={{
                    steps: selectedConfig.steps || [],
                    currentStep: reportManager.currentStep,
                    setCurrentStep: reportManager.setCurrentStep,
                }}
                file={{
                    csvConfigs: (selectedConfig.csvConfigs || []) as Array<{
                        config: { label: string; onParse: (csvText: string) => void };
                        required: boolean;
                    }>,
                    files: reportManager.csvFiles,
                    onUploadFile: reportManager.uploadCsvFile,
                }}
                preview={{
                    previewUrl: reportManager.previewUrl,
                    setPreviewUrl: reportManager.setPreviewUrl,
                }}
                modal={{
                    modalOpen: reportManager.isModalOpen,
                    setModalOpen: reportManager.setIsModalOpen,
                }}
                finalized={{
                    finalized: reportManager.isFinalized,
                    setFinalized: reportManager.setIsFinalized,
                }}
                loading={{
                    loading: reportManager.isLoading,
                    setLoading: reportManager.setIsLoading,
                }}
                reportKey={reportManager.selectedReport}
                onContinueInteractive={reportManager.continueInteractiveProcess}
                onResetInteractive={reportManager.resetInteractiveState}
                interactiveState={reportManager.interactiveState}
            />
        </>
    );
};

export default ReportModeFactory;
