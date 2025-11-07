/**
 * 将軍_最終版 CSV 検証アダプタ
 */

import { validateHeaders } from '../core/csvHeaderValidator';
import type { ValidationStatus } from '../../shared/types/common';

const SHOGUN_FINAL_HEADERS: Record<string, string[]> = {
  shogun_final_ship: ['伝票日付', '荷主', '品名'],
  shogun_final_receive: ['伝票日付', '荷主', '品名'],
  shogun_final_yard: ['品名', '荷主'],
};

export async function validateShogunFinalCsv(
  typeKey: string,
  file: File
): Promise<ValidationStatus> {
  const requiredHeaders = SHOGUN_FINAL_HEADERS[typeKey];
  if (!requiredHeaders) return 'unknown';
  return await validateHeaders(file, requiredHeaders);
}
