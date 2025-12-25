/**
 * CSV ファイル検証フック
 *
 * database と report の両方で使用できる汎用的な検証フック
 */

import { useCallback, useState } from 'react';
import { validateHeaders } from '../core/csvHeaderValidator';
import type { CsvValidationStatus } from '../model/validationStatus';

export interface CsvFileValidatorOptions {
  /** ラベルごとの必須ヘッダーを取得する関数 */
  getRequiredHeaders?: (label: string) => string[] | undefined;
  /** カスタムバリデーション関数 */
  onValidate?: (label: string, file: File, text: string) => Promise<boolean>;
}

/**
 * CSV ファイル検証フック
 */
export function useCsvFileValidator(options?: CsvFileValidatorOptions) {
  const [validationResults, setValidationResults] = useState<Record<string, CsvValidationStatus>>(
    {}
  );

  /**
   * ファイルを検証
   */
  const validateFile = useCallback(
    async (label: string, file: File): Promise<CsvValidationStatus> => {
      try {
        // 必須ヘッダーの取得
        const requiredHeaders = options?.getRequiredHeaders?.(label);

        // 必須ヘッダーがない場合はunknown
        if (!requiredHeaders || requiredHeaders.length === 0) {
          setValidationResults((prev) => ({ ...prev, [label]: 'unknown' }));
          return 'unknown';
        }

        // ヘッダー検証
        const status = await validateHeaders(file, requiredHeaders);

        // カスタムバリデーションがある場合は追加で実行
        if (status === 'valid' && options?.onValidate) {
          const text = await file.text();
          const customValid = await options.onValidate(label, file, text);
          const finalStatus: CsvValidationStatus = customValid ? 'valid' : 'invalid';
          setValidationResults((prev) => ({ ...prev, [label]: finalStatus }));
          return finalStatus;
        }

        setValidationResults((prev) => ({ ...prev, [label]: status }));
        return status;
      } catch (error) {
        console.error(`[useCsvFileValidator] 検証エラー for ${label}:`, error);
        setValidationResults((prev) => ({ ...prev, [label]: 'invalid' }));
        return 'invalid';
      }
    },
    [options]
  );

  /**
   * 検証結果をリセット
   */
  const resetValidation = useCallback((label: string) => {
    setValidationResults((prev) => ({ ...prev, [label]: 'unknown' }));
  }, []);

  /**
   * 検証結果を取得
   */
  const getValidationResult = useCallback(
    (label: string): CsvValidationStatus => {
      return validationResults[label] ?? 'unknown';
    },
    [validationResults]
  );

  /**
   * すべての検証結果をクリア
   */
  const clearAll = useCallback(() => {
    setValidationResults({});
  }, []);

  return {
    validationResults,
    validateFile,
    resetValidation,
    getValidationResult,
    clearAll,
  };
}
