/**
 * 将軍_速報版 CSV 検証アダプタ
 */

import { validateHeaders } from '../core/csvHeaderValidator';
import type { ValidationStatus } from '../../shared/types/common';

const SHOGUN_FLASH_HEADERS: Record<string, string[]> = {
  shogun_flash_ship: ['伝票日付', '荷主', '品名'],
  shogun_flash_receive: ['伝票日付', '荷主', '品名'],
  shogun_flash_yard: ['品名', '荷主'],
};

export async function validateShogunFlashCsv(
  typeKey: string,
  file: File
): Promise<ValidationStatus> {
  const requiredHeaders = SHOGUN_FLASH_HEADERS[typeKey];
  if (!requiredHeaders) return 'unknown';
  return await validateHeaders(file, requiredHeaders);
}
