// /app/src/components/Report/ReportModeBase.tsx

/**
 * モード対応レポートベースコンポーネント
 * 
 * 🎯 目的：
 * - 既存のReportBaseを拡張し、モード分岐に対応
 * - 自動・インタラクティブモードの統合UI管理
 * - 既存アーキテクチャとの互換性を保持
 */

import React, { useEffect } from 'react';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import InteractiveReportModal from './interactive/InteractiveReportModal';
import PDFViewer from './viewer/PDFViewer';
import { pdfPreviewMap, modalStepsMap } from '../../constants/reportConfig';
import { useReportBaseBusiness } from '../../hooks/report';
import { ReportModeService } from '../../services/reportModeService';
import type { ReportBaseProps } from '../../types/reportBase';
import type { InteractiveStep } from '../../pages/types/interactiveMode';
import type { ReportKey } from '../../constants/reportConfig';

// ==============================
// 🔧 拡張Props型定義
// ==============================

interface ReportModeBaseProps extends ReportBaseProps {
    // インタラクティブモード関連
    onContinueInteractive?: (userInput: Record<string, unknown>) => void;
    onResetInteractive?: () => void;
    interactiveState?: {
        currentStep: number;
        isLoading: boolean;
        error?: string;
    };
}

// ==============================
// 🎯 メインコンポーネント
// ==============================

const ReportModeBase: React.FC<ReportModeBaseProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    reportKey,
    onContinueInteractive,
    onResetInteractive,
    interactiveState,
}) => {
    // モード情報を取得
    const modeInfo = ReportModeService.getModeInfo(reportKey);
    const isInteractiveMode = modeInfo.isInteractive;

    // ビジネスロジックをフックに委譲（既存機能）
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey
    );

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (business.pdfPreviewUrl && business.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(business.pdfPreviewUrl);
        }
    }, [business.pdfPreviewUrl, preview]);

    // ==============================
    // 🎮 イベントハンドラー
    // ==============================

    /**
     * レポート生成処理（モード共通）
     */
    const handleGenerate = () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        if (isInteractiveMode) {
            // インタラクティブモードの場合、ここでは初期化のみ
            // 実際の処理は親コンポーネント（useReportModeManager）で実行
            console.log('Interactive mode generation started');
        } else {
            // 自動モードの場合、従来通りの処理
            business.handleGenerateReport(
                () => {}, // onStart
                () => {   // onComplete
                    loading.setLoading(false);
                    finalized.setFinalized(true);
                },
                () => {   // onSuccess
                    step.setCurrentStep(1);
                }
            );
        }
    };

    /**
     * Excel/ZIPダウンロード処理
     */
    const handleDownloadExcel = () => {
        if (business.zipUrl) {
            // ZIP形式のダウンロード
            const link = document.createElement('a');
            link.href = business.zipUrl;
            link.download = business.zipFileName || `report_${Date.now()}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else if (business.hasExcel && business.excelBlob) {
            // Excel形式のダウンロード（レガシー対応）
            const url = URL.createObjectURL(business.excelBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = business.excelFileName || `report_${Date.now()}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    };

    /**
     * PDFプリント処理
     */
    const handlePrintPdf = () => {
        if (business.pdfPreviewUrl) {
            window.open(business.pdfPreviewUrl, '_blank');
        }
    };

    // ==============================
    // 🎨 レンダリング
    // ==============================

    return (
        <>
            {/* メインレイアウト */}
            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={handleDownloadExcel}
                onPrintPdf={handlePrintPdf}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                pdfUrl={preview.previewUrl}
                excelUrl={business.zipUrl || (business.hasExcel ? 'available' : null)}
                excelReady={Boolean(business.zipUrl || business.hasExcel)}
                pdfReady={Boolean(business.pdfPreviewUrl)}
                sampleImageUrl={pdfPreviewMap[reportKey]}
            >
                {/* PDFプレビュー表示 */}
                <PDFViewer pdfUrl={preview.previewUrl} />
            </ReportManagePageLayout>

            {/* モーダル表示の分岐 */}
            {isInteractiveMode ? (
                /* インタラクティブモード専用モーダル */
                <InteractiveReportModal
                    open={modal.modalOpen}
                    onClose={() => modal.setModalOpen(false)}
                    reportName={getReportDisplayName(reportKey)}
                    state={{
                        currentStep: (interactiveState?.currentStep ?? -1) as InteractiveStep,
                        isLoading: interactiveState?.isLoading ?? false,
                        error: interactiveState?.error,
                    }}
                    onContinue={onContinueInteractive}
                    onReset={onResetInteractive}
                />
            ) : (
                /* 自動モード従来モーダル */
                <ReportStepperModal
                    open={modal.modalOpen}
                    steps={(modalStepsMap[reportKey] || []).map(step => step.label)}
                    currentStep={step.currentStep}
                    stepConfigs={modalStepsMap[reportKey] || []}
                    onNext={() => {}}
                    onClose={() => modal.setModalOpen(false)}
                >
                    <div>処理中...</div>
                </ReportStepperModal>
            )}
        </>
    );
};

// ==============================
// 🔧 ヘルパー関数
// ==============================

/**
 * レポートキーから表示名を取得
 */
const getReportDisplayName = (reportKey: ReportKey): string => {
    const displayNames: Record<ReportKey, string> = {
        factory_report: '工場日報',
        balance_sheet: '工場搬出入収支表',
        average_sheet: '集計項目平均表',
        block_unit_price: 'ブロック単価表',
        management_sheet: '管理票',
        ledger_book: '帳簿',
    };
    
    return displayNames[reportKey] || reportKey;
};

export default ReportModeBase;
