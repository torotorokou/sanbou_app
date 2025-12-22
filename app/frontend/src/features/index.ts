/**
 * Features - Public API
 */

// WipNotice - 開発中機能警告バナー
export { WipNotice, type WipNoticeProps } from './wip-notice';

// CSV Validation - 個別エクスポートで重複を回避
export {
  // Types
  type CsvValidationStatus,
  type LegacyReportStatus,
  // Utilities
  mapLegacyToCsvStatus,
  mapCsvToLegacyStatus,
  normalizeValidationStatus,
  toLegacyValidationStatus,
  // UI
  CsvValidationBadge,
  type CsvValidationBadgeProps,
  // Core
  parseHeader,
  validateHeaders,
  validateHeadersFromText,
  // Hooks
  useCsvFileValidator,
  type CsvFileValidatorOptions,
} from './csv-validation';

// Dataset (includes dataset-import, dataset-submit, dataset-preview, etc.)
export * from './dataset';
