import { useCallback, useEffect, useState } from 'react';
import type { UploadProps } from 'antd/es/upload';
// useCsvValidation は削除されました - 新しい検証ロジックへの移行が必要
// import { useCsvValidation } from '@features/database';
import { useReportArtifact } from '@features/report/report-preview/model/useReportArtifact';
import type {
    CsvFiles,
    CsvConfigEntry,
    UploadFileConfig,
    MakeUploadPropsFn,
} from '@features/report/types/report.types';
import type { ReportKey } from '@features/report/config';

/**
 * ReportBaseのビジネスロジックを統合管理するフック
 *
 * ⚠️ 注意: useCsvValidation は削除されました
 * TODO: useValidateOnPick を使用するように移行が必要
 *
 * 🎯 目的：
 * - CSV検証、Excel生成の複雑なロジックを統合
 * - ReportBaseコンポーネントをシンプルに保つ
 * - 関連する機能を一元化して保守性向上
 */

// 一時的なスタブ実装
const useCsvValidation = () => {
    const [validationResults, setValidationResults] = useState<Record<string, 'valid' | 'invalid' | 'unknown'>>({});
    
    const validateCsvFile = useCallback((file: File, label: string) => {
        // TODO: 実装が必要
        setValidationResults(prev => ({ ...prev, [label]: 'unknown' }));
    }, []);
    
    const resetValidation = useCallback((label: string) => {
        setValidationResults(prev => ({ ...prev, [label]: 'unknown' }));
    }, []);
    
    const getValidationResult = useCallback((label: string) => {
        return validationResults[label] ?? 'unknown';
    }, [validationResults]);
    
    return { validationResults, validateCsvFile, resetValidation, getValidationResult };
};
export const useReportBaseBusiness = (
    csvConfigs: CsvConfigEntry[],
    csvFiles: CsvFiles,
    onUploadFile: (label: string, file: File | null) => void,
    reportKey: ReportKey
) => {
    const csvValidation = useCsvValidation();
    const artifact = useReportArtifact();

    useEffect(() => {
        artifact.cleanup();
    }, [artifact.cleanup, reportKey]);

    /**
     * ファイル削除処理
     */
    const handleRemoveFile = useCallback(
        (label: string) => {
            onUploadFile(label, null);
            csvValidation.resetValidation(label);
        },
        [onUploadFile, csvValidation]
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
            const validation = csvValidation.getValidationResult(label);

            if (fileObj) {
                return validation === 'valid';
            } else {
                return !entry.required;
            }
        });
    }, [csvConfigs, csvFiles, csvValidation]);

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
                    if (f === null) {
                        csvValidation.resetValidation(label);
                    }
                },
                required: entry.required,
                validationResult: csvValidation.getValidationResult(label),
                onRemove: () => handleRemoveFile(label),
            };
        });
    }, [csvConfigs, csvFiles, onUploadFile, csvValidation, handleRemoveFile]);

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
     */
    const handleGenerateReport = useCallback(
        async (
            onStart: () => void,
            onComplete: () => void,
            onSuccess: () => void
        ) => {
            const success = await artifact.generateReport(
                csvFiles,
                reportKey,
                onStart,
                onComplete
            );

            if (success) {
                onSuccess();
            }
        },
        [artifact, csvFiles, reportKey]
    );

    return {
        // 状態
        validationResults: csvValidation.validationResults,

        // ZIP関連
        excelUrl: artifact.excelUrl,
        pdfUrl: artifact.pdfUrl,
        excelFileName: artifact.excelFileName,
        pdfFileName: artifact.pdfFileName,
        hasExcel: Boolean(artifact.excelUrl),
    hasPdf: Boolean(artifact.pdfUrl),
    pdfPreviewUrl: artifact.pdfUrl,
        reportToken: artifact.reportToken,
        reportDate: artifact.reportDate,
        reportKey: artifact.reportKey,
        summary: artifact.summary,
        metadata: artifact.metadata,
        lastResponse: artifact.lastResponse,

        // 計算されたプロパティ
        isReadyToCreate: isReadyToCreate(),
        uploadFileConfigs: getUploadFileConfigs(),
        makeUploadPropsFn: createMakeUploadProps(),
        isReportReady: artifact.isReady,

        // アクション
        handleRemoveFile,
        handleGenerateReport,
        downloadExcel: artifact.downloadExcel,
        printPdf: artifact.printPdf,
        getPdfPreviewUrl: artifact.getPdfPreviewUrl,
        cleanup: artifact.cleanup,
        applyArtifactResponse: artifact.applyArtifactResponse,
    };
};
