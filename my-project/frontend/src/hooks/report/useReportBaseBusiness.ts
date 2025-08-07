import { useCallback } from 'react';
import type { UploadProps } from 'antd/es/upload';
import { useCsvValidation } from '../data/useCsvValidation';
import { useZipFileGeneration } from '../data/useZipFileGeneration';
import type {
    CsvFiles,
    CsvConfigEntry,
    UploadFileConfig,
    MakeUploadPropsFn,
} from '../../types/reportBase';
import type { ReportKey } from '../../constants/reportConfig/managementReportConfig.tsx';

/**
 * ReportBaseのビジネスロジックを統合管理するフック
 *
 * 🎯 目的：
 * - CSV検証、Excel生成の複雑なロジックを統合
 * - ReportBaseコンポーネントをシンプルに保つ
 * - 関連する機能を一元化して保守性向上
 */
export const useReportBaseBusiness = (
    csvConfigs: CsvConfigEntry[],
    csvFiles: CsvFiles,
    onUploadFile: (label: string, file: File | null) => void,
    reportKey: ReportKey,
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown'
) => {
    const csvValidation = useCsvValidation();
    const zipGeneration = useZipFileGeneration();

    /**
     * ファイル削除処理
     */
    const handleRemoveFile = useCallback(
        (label: string) => {
            onUploadFile(label, null);
            // グローバルバリデーション使用時はローカルリセット不要
            if (!getValidationResult) {
                csvValidation.resetValidation(label);
            }
        },
        [onUploadFile, getValidationResult, csvValidation]
    );

    /**
     * アップロード用props生成
     */
    const makeUploadProps = useCallback(
        (label: string, parser: (csvText: string) => void): UploadProps => ({
            accept: '.csv',
            showUploadList: false,
            beforeUpload: (fileObj) => {
                onUploadFile(label, fileObj);

                if (!fileObj) {
                    csvValidation.resetValidation(label);
                    return false;
                }

                csvValidation.validateCsvFile(fileObj, label, parser);
                return false;
            },
        }),
        [onUploadFile, csvValidation]
    );

    /**
     * レポート生成準備チェック
     */
    const isReadyToCreate = useCallback((): boolean => {
        return csvConfigs.every((entry) => {
            const label = entry.config.label;
            const fileObj = csvFiles[label];
            const validation = getValidationResult
                ? getValidationResult(label)
                : csvValidation.getValidationResult(label);

            if (fileObj) {
                return validation === 'valid';
            } else {
                return !entry.required;
            }
        });
    }, [csvConfigs, csvFiles, getValidationResult, csvValidation]);

    /**
     * アップロードファイル設定を生成
     */
    const getUploadFileConfigs = useCallback((): UploadFileConfig[] => {
        return csvConfigs.map((entry: CsvConfigEntry): UploadFileConfig => {
            const label = entry.config.label;
            return {
                label,
                file: csvFiles[label] ?? null,
                onChange: (f: File | null) => {
                    onUploadFile(label, f);
                    if (f === null && !getValidationResult) {
                        csvValidation.resetValidation(label);
                    }
                },
                required: entry.required,
                validationResult: getValidationResult
                    ? getValidationResult(label)
                    : csvValidation.getValidationResult(label),
                onRemove: () => handleRemoveFile(label),
            };
        });
    }, [
        csvConfigs,
        csvFiles,
        onUploadFile,
        getValidationResult,
        csvValidation,
        handleRemoveFile,
    ]);

    /**
     * MakeUploadProps関数を生成
     */
    const createMakeUploadProps = useCallback((): MakeUploadPropsFn => {
        return (label: string): UploadProps => {
            let entry = null;
            for (let i = 0; i < csvConfigs.length; i++) {
                if (csvConfigs[i].config.label === label) {
                    entry = csvConfigs[i];
                    break;
                }
            }
            return entry ? makeUploadProps(label, entry.config.onParse) : {};
        };
    }, [csvConfigs, makeUploadProps]);

    /**
     * レポート生成処理（ZIP形式）
     * block_unit_priceの場合は特別な処理フローを実行
     */
    const handleGenerateReport = useCallback(
        async (
            onStart: () => void,
            onComplete: () => void,
            onSuccess: () => void
        ) => {
            // block_unit_priceの場合は、まずCSVバリデーションと初期処理のみ実行
            if (reportKey === 'block_unit_price') {
                onStart();

                try {
                    // CSVファイルの存在チェック
                    const hasRequiredFiles = csvConfigs.every((entry) => {
                        const label = entry.config.label;
                        const fileObj = csvFiles[label];
                        const validation =
                            csvValidation.getValidationResult(label);

                        if (entry.required) {
                            return fileObj && validation === 'valid';
                        }
                        return true;
                    });

                    if (!hasRequiredFiles) {
                        throw new Error('必要なCSVファイルが不足しています');
                    }

                    // ファイル検証完了時点で成功とみなす（実際のAPI処理は呼び出し元で実行）
                    onSuccess();
                } catch (error) {
                    console.error('Block unit price初期処理エラー:', error);
                } finally {
                    onComplete();
                }
                return;
            }

            // 通常のレポート生成処理
            const success = await zipGeneration.generateZipReport(
                csvFiles,
                reportKey,
                onStart,
                onComplete
            );

            if (success) {
                onSuccess();
            }
        },
        [zipGeneration, csvFiles, reportKey, csvConfigs, csvValidation]
    );

    return {
        // 状態
        validationResults: csvValidation.validationResults,

        // ZIP関連
        zipUrl: zipGeneration.zipUrl,
        zipFileName: zipGeneration.zipFileName,

        // Excel関連
        excelBlob: zipGeneration.excelBlob,
        excelFileName: zipGeneration.excelFileName,
        hasExcel: zipGeneration.hasExcel,

        // PDF関連
        pdfBlob: zipGeneration.pdfBlob,
        pdfFileName: zipGeneration.pdfFileName,
        hasPdf: zipGeneration.hasPdf,
        pdfPreviewUrl: zipGeneration.pdfPreviewUrl,

        // 計算されたプロパティ
        isReadyToCreate: isReadyToCreate(),
        uploadFileConfigs: getUploadFileConfigs(),
        makeUploadPropsFn: createMakeUploadProps(),
        isReportReady: zipGeneration.isReady,

        // アクション
        handleRemoveFile,
        handleGenerateReport,
        downloadExcel: zipGeneration.downloadExcel,
        downloadPdf: zipGeneration.downloadPdf,
        printPdf: zipGeneration.printPdf,
        getPdfPreviewUrl: zipGeneration.getPdfPreviewUrl,
        downloadZip: zipGeneration.downloadZip,
        cleanup: zipGeneration.cleanup,
    };
};
