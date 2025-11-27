/**
 * csv-validation Feature Public API
 * 
 * CSV バリデーション関連の機能を提供
 * - 型定義（バリデーションステータス）
 * - UI コンポーネント（バリデーションバッジ）
 * - バリデーションロジック（ヘッダー・行検証）
 * - バリデーションフック
 */

// ========================================
// Validation Status Types & Utilities
// ========================================

/**
 * CSV バリデーションステータス型
 * 'valid' | 'invalid' | 'unknown'
 */
export type { 
  CsvValidationStatus,
  LegacyReportStatus,
} from './model/validationStatus';

/**
 * ステータス変換ユーティリティ
 */
export { 
  mapLegacyToCsvStatus,
  mapCsvToLegacyStatus,
  normalizeValidationStatus,
  toLegacyValidationStatus,
} from './model/validationStatus';

// ========================================
// UI Components
// ========================================

/**
 * CSV バリデーションバッジコンポーネント
 * valid → 緑「OK」, invalid → 赤「NG」, unknown → グレー「未検証」
 */
export { CsvValidationBadge } from './ui/CsvValidationBadge';
export type { CsvValidationBadgeProps } from './ui/CsvValidationBadge';

// ========================================
// Validation Logic
// ========================================

export { parseHeader, validateHeaders, validateHeadersFromText } from './core/csvHeaderValidator';
export * from './core/csvRowValidator';

// ========================================
// Hooks
// ========================================

export { useCsvFileValidator } from './hooks/useCsvFileValidator';
export type { CsvFileValidatorOptions } from './hooks/useCsvFileValidator';
export * from './hooks/useValidateOnPick';

// ========================================
// Model Types
// ========================================

export type { ValidationResult } from './model/types';
