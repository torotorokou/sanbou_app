// /app/src/components/Report/GenericReportFactory.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';

import { GenericStepController } from './controllers/GenericStepController';
import GenericBaseReportComponent from './GenericBaseReportComponent';
import type { GenericZipResult } from './GenericBaseReportComponent';
import type { ReportConfigPackage } from '../../types/reportConfig';

interface GenericReportFactoryProps {
    config: ReportConfigPackage;
    reportKey: string;
    csvFiles: File[];
    onComplete?: (result: unknown) => void;
    onError?: (error: string) => void;
    onStepChange?: (step: number) => void;
}

/**
 * 汎用的な帳票生成ファクトリーコンポーネント
 * 
 * どの帳票設定パッケージでも使用可能な汎用ファクトリー
 */
export const GenericReportFactory: React.FC<GenericReportFactoryProps> = ({
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

    // ステップ変更の通知
    useEffect(() => {
        onStepChange?.(currentStep);
    }, [currentStep, onStepChange]);

    // 帳票タイプの取得
    const reportType = config.getReportType(reportKey);
    const reportDefinition = config.reportKeys[reportKey];

    // APIエンドポイントの取得
    const apiUrl = config.apiUrlMap[reportKey];

    // CSVアップロード処理
    const handleCsvUpload = useCallback(async () => {
        if (!csvFiles.length) {
            onError?.('CSVファイルが選択されていません');
            return;
        }

        setIsLoading(true);

        try {
            // FormDataの構築
            const formData = new FormData();

            // CSVファイルの追加
            csvFiles.forEach((file, index) => {
                formData.append(`file${index}`, file);
            });

            // 帳票キーの追加
            formData.append('report_key', reportKey);

            // 帳票タイプの追加
            formData.append('type', reportType);

            console.log(`[${config.name}] Uploading to: ${apiUrl}`);
            console.log(`[${config.name}] Report key: ${reportKey}, Type: ${reportType}`);

            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            // レスポンスの処理
            const contentType = response.headers.get('content-type');

            if (contentType?.includes('application/zip')) {
                // ZIPファイルの処理
                const zipBuffer = await response.arrayBuffer();
                const zipData = new Uint8Array(zipBuffer);

                // ZIPファイルの解析（JSZipを使用）
                const JSZip = (await import('jszip')).default;
                const zip = await JSZip.loadAsync(zipData);

                let excelFile: Uint8Array | undefined;
                let pdfFile: Uint8Array | undefined;

                // ZIP内のファイルを確認
                for (const [filename, file] of Object.entries(zip.files)) {
                    if (!file.dir) {
                        const content = await file.async('uint8array');

                        if (filename.includes('.xlsx') || filename.includes('.xls')) {
                            excelFile = content;
                        } else if (filename.includes('.pdf')) {
                            pdfFile = content;
                        }
                    }
                }

                const result: GenericZipResult = {
                    excelFile,
                    pdfFile,
                    originalResponse: {
                        type: 'zip',
                        filename: 'report_files.zip'
                    },
                    success: true,
                    hasExcel: !!excelFile,
                    hasPdf: !!pdfFile,
                    type: 'zip'
                };

                setZipResult(result);

                // バックエンド処理完了後のステップ遷移
                await stepController.onBackendComplete(setCurrentStep, setIsLoading);

                onComplete?.(result);

            } else {
                // JSON レスポンスの処理
                const jsonResult = await response.json();

                // バックエンド処理完了後のステップ遷移
                await stepController.onBackendComplete(setCurrentStep, setIsLoading);

                onComplete?.(jsonResult);
            }

        } catch (error) {
            console.error(`[${config.name}] Upload error:`, error);
            setIsLoading(false);

            const errorMessage = error instanceof Error ? error.message : '不明なエラーが発生しました';
            message.error(`${reportDefinition?.label}の処理に失敗しました: ${errorMessage}`);
            onError?.(errorMessage);
        }
    }, [config, reportKey, reportType, apiUrl, csvFiles, stepController, onComplete, onError, reportDefinition]);

    // 自動実行の処理
    useEffect(() => {
        if (reportType === 'auto' && csvFiles.length > 0) {
            handleCsvUpload();
        }
    }, [reportType, csvFiles, handleCsvUpload]);

    // 戻るボタンのハンドラー
    const handlePrevious = useCallback(async () => {
        await stepController.goToPreviousStep(setCurrentStep, setIsLoading);
    }, [stepController]);

    // 次へボタンのハンドラー
    const handleNext = useCallback(async () => {
        const currentStepConfig = stepController.getCurrentStepConfig();

        // 進行可能かチェック
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
