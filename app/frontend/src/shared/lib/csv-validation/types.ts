/**
 * CSV検証の共通型定義
 */

export type ValidationStatus = 'valid' | 'invalid' | 'unknown';

export interface ValidationResult {
  status: ValidationStatus;
  errors?: string[];
}

export interface CsvValidationOptions {
  /** 必須ヘッダー（最初の5つを検証） */
  requiredHeaders?: string[];
  /** カスタムバリデーター関数 */
  customValidator?: (text: string) => Promise<boolean>;
}
