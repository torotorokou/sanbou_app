/**
 * CSV 行検証（将来的な拡張用）
 */

import type { ValidationStatus } from '../../shared/types/common';

export async function validateRows(
  _file: File,
  _rules?: unknown
): Promise<ValidationStatus> {
  // 将来的な実装: 行ごとのバリデーション
  return 'unknown';
}
