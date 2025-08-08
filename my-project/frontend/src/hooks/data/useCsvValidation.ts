import { useState, useCallback } from 'react';
import {
    identifyCsvType,
    isCsvMatch,
} from '../../utils/validators/csvValidator';
import { notifySuccess, notifyError, notifyWarning } from '../../utils/notify';

/**
 * CSV検証とファイル管理を担当するフック
 *
 * 🎯 目的：
 * - CSV検証ロジックを分離・再利用可能にする
 * - ファイル管理の複雑性を隠蔽する
 * - 検証結果の状態管理を簡潔にする
 */
export const useCsvValidation = () => {
    const [validationResults, setValidationResults] = useState<{
        [label: string]: 'valid' | 'invalid' | 'unknown';
    }>({});

    /**
     * CSVファイルを検証する
     */
    const validateCsvFile = useCallback(
        (file: File, label: string, onParse: (csvText: string) => void) => {
            const reader = new FileReader();

            reader.onload = (e) => {
                const csvText = e.target?.result as string;
                const result = identifyCsvType(csvText);
                const isValid = isCsvMatch(result, label);

                // 検証結果を更新
                setValidationResults((prev) => ({
                    ...prev,
                    [label]: isValid ? 'valid' : 'invalid',
                }));

                if (isValid) {
                    onParse(csvText);
                    notifySuccess(
                        'CSV検証成功',
                        `「${label}」のファイルが正常に読み込まれました。`
                    );
                } else {
                    notifyWarning(
                        'CSVファイル形式エラー',
                        `「${label}」のファイル形式が正しくありません。`
                    );
                }
            };

            reader.onerror = () => {
                setValidationResults((prev) => ({
                    ...prev,
                    [label]: 'invalid',
                }));
                notifyError(
                    'ファイル読み取りエラー',
                    'ファイルの読み取りに失敗しました。'
                );
            };

            reader.readAsText(file);
        },
        []
    );

    /**
     * 検証結果をリセットする
     */
    const resetValidation = useCallback((label: string) => {
        setValidationResults((prev) => ({
            ...prev,
            [label]: 'unknown',
        }));
    }, []);

    /**
     * 指定ラベルの検証結果を取得
     */
    const getValidationResult = useCallback(
        (label: string) => {
            return validationResults[label] ?? 'unknown';
        },
        [validationResults]
    );

    return {
        validationResults,
        validateCsvFile,
        resetValidation,
        getValidationResult,
    };
};
