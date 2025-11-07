/**
 * dataset-validate 型定義
 */

export interface ValidationResult {
  typeKey: string;
  isValid: boolean;
  errors: string[];
}
