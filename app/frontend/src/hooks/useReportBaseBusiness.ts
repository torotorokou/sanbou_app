import { useCallback } from 'react';
import type { UploadProps } from 'antd/es/upload';
import { useCsvValidation } from './useCsvValidation';
import { useExcelGeneration } from './useExcelGeneration';
import type {
    CsvFiles,
    CsvConfigEntry,
    UploadFileConfig,
    MakeUploadPropsFn,
} from '../types/reportBase';
import type { ReportKey } from '../constants/reportConfig';

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
    reportKey: ReportKey
) => {
    const csvValidation = useCsvValidation();
    const excelGeneration = useExcelGeneration();

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
     * Excel生成処理
     */
    const handleGenerateExcel = useCallback(
        async (
            onStart: () => void,
            onComplete: () => void,
            onSuccess: () => void
        ) => {
            const success = await excelGeneration.generateExcel(
                csvFiles,
                reportKey,
                onStart,
                onComplete
            );

            if (success) {
                onSuccess();
            }
        },
        [excelGeneration, csvFiles, reportKey]
    );

    return {
        // 状態
        validationResults: csvValidation.validationResults,
        excelUrl: excelGeneration.excelUrl,
        excelFileName: excelGeneration.excelFileName,

        // 計算されたプロパティ
        isReadyToCreate: isReadyToCreate(),
        uploadFileConfigs: getUploadFileConfigs(),
        makeUploadPropsFn: createMakeUploadProps(),

        // アクション
        handleRemoveFile,
        handleGenerateExcel,
        downloadExcel: excelGeneration.downloadExcel,
    };
};
