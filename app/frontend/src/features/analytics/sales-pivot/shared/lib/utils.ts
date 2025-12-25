/**
 * shared/lib/utils.ts
 * 共通ユーティリティ関数
 */

import type { ExportOptions } from '../model/types';

/**
 * デフォルトのエクスポートオプション
 */
export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  addAxisB: false,
  addAxisC: false,
  excludeZero: true,
  splitBy: 'none',
};

/**
 * Blobをダウンロードするヘルパー関数
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
