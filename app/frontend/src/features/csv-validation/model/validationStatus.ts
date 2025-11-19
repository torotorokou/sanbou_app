/**
 * CSV バリデーションステータス型定義
 * 
 * @/shared/types/validation の ValidationStatus を CSV 用に再エクスポート
 * CSV 特化の型やユーティリティをここに集約
 */

import type { ValidationStatus } from '@/shared';

// ========================================
// Core Types - @/shared から再エクスポート
// ========================================

/**
 * CSV バリデーションステータス
 * - valid: バリデーション成功
 * - invalid: バリデーション失敗  
 * - unknown: 未検証
 */
export type { ValidationStatus as CsvValidationStatus } from '@/shared';

// ========================================
// Legacy Compatibility Types
// ========================================

/**
 * レガシーなレポートステータス表記（互換性のため）
 * report 機能で使用されている 'ok'/'ng' 表記
 */
export type LegacyReportStatus = 'ok' | 'ng' | 'unknown';

// ========================================
// Mapping Functions
// ========================================

/**
 * レガシーなレポートステータスを CsvValidationStatus に変換
 * 
 * @param status - レガシーステータス ('ok' | 'ng' | 'unknown')
 * @returns 正規化された CsvValidationStatus
 * 
 * @example
 * ```ts
 * const csvStatus = mapLegacyToCsvStatus('ok'); // 'valid'
 * const csvStatus = mapLegacyToCsvStatus('ng'); // 'invalid'
 * ```
 */
export const mapLegacyToCsvStatus = (
  status: LegacyReportStatus,
): ValidationStatus => {
  switch (status) {
    case 'ok':
      return 'valid';
    case 'ng':
      return 'invalid';
    default:
      return 'unknown';
  }
};

/**
 * CsvValidationStatus をレガシーなレポートステータスに逆変換
 * 
 * @param status - CsvValidationStatus
 * @returns レガシーステータス ('ok' | 'ng' | 'unknown')
 * 
 * @example
 * ```ts
 * const legacyStatus = mapCsvToLegacyStatus('valid'); // 'ok'
 * const legacyStatus = mapCsvToLegacyStatus('invalid'); // 'ng'
 * ```
 */
export const mapCsvToLegacyStatus = (
  status: ValidationStatus,
): LegacyReportStatus => {
  switch (status) {
    case 'valid':
      return 'ok';
    case 'invalid':
      return 'ng';
    default:
      return 'unknown';
  }
};

// ========================================
// Re-exports from @/shared
// ========================================

/**
 * 汎用的なバリデーションステータス変換関数
 * レガシー表記と新表記の両方に対応
 */
export { normalizeValidationStatus, toLegacyValidationStatus } from '@/shared';

