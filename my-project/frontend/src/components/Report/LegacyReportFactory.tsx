// /app/src/components/Report/LegacyReportFactory.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';

import { GenericStepController } from './controllers/GenericStepController';
import GenericBaseReportComponent from './GenericBaseReportComponent';
import { LegacyReportService } from './services/LegacyReportService';
import type { ReportConfigPackage } from '../../types/reportConfig';
import type { GenericZipResult } from './GenericBaseReportComponent';
import type { WorkerRow, ValuableRow, ShipmentRow } from '../../types/report';

interface LegacyReportFactoryProps {
    config: ReportConfigPackage;
    reportKey: string;
    csvFiles: File[];
    onComplete?: (result: unknown) => void;
    onError?: (error: string) => void;
    onStepChange?: (step: number) => void;
}

/**
 * 既存ReportFactory.tsx用のカスタムファクトリー
 * 
 * 既存のバリデーションロジックを保持しつつ、
 * 新しい汎用システムと統合
 */
export const LegacyReportFactory: React.FC<LegacyReportFactoryProps> = ({
    config,
    reportKey,
    csvFiles,
    onComplete,
    onError,
    onStepChange,
}) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [stepController] = useState(() => new GenericStepController(config, reportKey));
    const [zipResult, setZipResult] = useState<GenericZipResult | null>(null);

    // レガシーデータ状態管理（バリデーション用）
    const [workerData, setWorkerData] = useState<WorkerRow[]>([]);
    const [valuableData, setValuableData] = useState<ValuableRow[]>([]);
    const [shipmentData, setShipmentData] = useState<ShipmentRow[]>([]);
    const [validationResults, setValidationResults] = useState({
        shipFileValid: 'unknown' as 'valid' | 'invalid' | 'unknown',
        yardFileValid: 'unknown' as 'valid' | 'invalid' | 'unknown',
        receiveFileValid: 'unknown' as 'valid' | 'invalid' | 'unknown',
    });

    // デバッグ用ログ（データが正しく解析されているか確認）
    useEffect(() => {
        if (workerData.length > 0) console.log(`[${config.name}] Worker data loaded:`, workerData.length);
        if (valuableData.length > 0) console.log(`[${config.name}] Valuable data loaded:`, valuableData.length);
        if (shipmentData.length > 0) console.log(`[${config.name}] Shipment data loaded:`, shipmentData.length);
    }, [workerData, valuableData, shipmentData, config.name]);

    // ステップ変更の通知
    useEffect(() => {
        onStepChange?.(currentStep);
    }, [currentStep, onStepChange]);

    // CSVファイルの検証と解析
    const validateCSVFiles = useCallback(async () => {
        if (!csvFiles.length) return;

        console.log(`[${config.name}] Validating ${csvFiles.length} CSV files...`);

        const newValidationResults = { ...validationResults };

        for (const file of csvFiles) {
            // ファイル名からタイプを推定
            let label = '';
            if (file.name.includes('出荷') || file.name.includes('shipment')) {
                label = '出荷一覧';
            } else if (file.name.includes('ヤード') || file.name.includes('yard')) {
                label = 'ヤード一覧';
            } else if (file.name.includes('受入') || file.name.includes('receive')) {
                label = '受入一覧';
            }

            if (label) {
                try {
                    const { isValid, data } = await LegacyReportService.validateAndParseCSV(file, label);

                    if (label === '出荷一覧') {
                        newValidationResults.shipFileValid = isValid ? 'valid' : 'invalid';
                        if (isValid && data) {
                            setShipmentData(data as ShipmentRow[]);
                        }
                    } else if (label === 'ヤード一覧') {
                        newValidationResults.yardFileValid = isValid ? 'valid' : 'invalid';
                        if (isValid && data) {
                            setWorkerData(data as WorkerRow[]);
                        }
                    } else if (label === '受入一覧') {
                        newValidationResults.receiveFileValid = isValid ? 'valid' : 'invalid';
                        if (isValid && data) {
                            setValuableData(data as ValuableRow[]);
                        }
                    }
                } catch (error) {
                    console.error(`[${config.name}] Validation error for ${file.name}:`, error);
                }
            }
        }

        setValidationResults(newValidationResults);
    }, [csvFiles, config.name, validationResults]);

    // CSVファイル変更時の検証実行
    useEffect(() => {
        if (csvFiles.length > 0) {
            validateCSVFiles();
        }
    }, [csvFiles, validateCSVFiles]);

    // レガシーレポート生成処理
    const handleLegacyReportGeneration = useCallback(async () => {
        if (!csvFiles.length) {
            onError?.('CSVファイルが選択されていません');
            return;
        }

        // 出荷ファイルの必須チェック（レガシーロジック）
        const shipFile = csvFiles.find(f =>
            f.name.includes('出荷') || f.name.includes('shipment')
        );

        if (!LegacyReportService.isReadyToCreate(shipFile || null, validationResults.shipFileValid)) {
            onError?.('出荷一覧ファイルが有効でありません');
            return;
        }

        setIsLoading(true);

        try {
            console.log(`[${config.name}] Starting legacy report generation...`);

            // ステップ1: データ処理開始
            await stepController.executeTransition(1, setCurrentStep, setIsLoading);

            // レガシーサービスでレポート生成
            const result = await LegacyReportService.generateLegacyReport(csvFiles);

            if (result.success) {
                const zipResult: GenericZipResult = {
                    success: true,
                    hasExcel: false,
                    hasPdf: !!result.pdfFile,
                    type: 'zip',
                    pdfFile: result.pdfFile,
                    originalResponse: {
                        pdfUrl: result.pdfUrl,
                        type: 'legacy_factory_report'
                    }
                };

                setZipResult(zipResult);

                // ステップ2: 完了
                await stepController.onBackendComplete(setCurrentStep, setIsLoading);

                onComplete?.(zipResult);
            } else {
                throw new Error('レポート生成に失敗しました');
            }

        } catch (error) {
            console.error(`[${config.name}] Legacy report generation error:`, error);
            setIsLoading(false);

            const errorMessage = error instanceof Error ? error.message : '不明なエラーが発生しました';
            message.error(`レガシーレポートの処理に失敗しました: ${errorMessage}`);
            onError?.(errorMessage);
        }
    }, [config.name, csvFiles, validationResults, stepController, onComplete, onError]);

    // 自動実行（レガシーモード）
    useEffect(() => {
        const reportType = config.getReportType(reportKey);
        if (reportType === 'auto' && csvFiles.length > 0 && validationResults.shipFileValid === 'valid') {
            handleLegacyReportGeneration();
        }
    }, [csvFiles, validationResults.shipFileValid, handleLegacyReportGeneration, config, reportKey]);

    // 戻るボタンのハンドラー
    const handlePrevious = useCallback(async () => {
        await stepController.goToPreviousStep(setCurrentStep, setIsLoading);
    }, [stepController]);

    // 次へボタンのハンドラー
    const handleNext = useCallback(async () => {
        const currentStepConfig = stepController.getCurrentStepConfig();

        if (currentStepConfig?.canProceed && !currentStepConfig.canProceed()) {
            message.warning('この段階では次に進むことができません');
            return;
        }

        await stepController.goToNextStep(setCurrentStep, setIsLoading);
    }, [stepController]);

    return (
        <GenericBaseReportComponent
            config={config}
            reportKey={reportKey}
            currentStep={currentStep}
            isLoading={isLoading}
            zipResult={zipResult}
            onPrevious={handlePrevious}
            onNext={handleNext}
        />
    );
};
