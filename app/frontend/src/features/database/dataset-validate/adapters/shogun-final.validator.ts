/**
 * 将軍_最終版 CSV 検証アダプタ
 */

import { validateHeaders } from '../core/csvHeaderValidator';
import type { ValidationStatus } from '../../shared/types/common';
import { getRequiredHeaders } from '../../config/datasets';

export async function validateShogunFinalCsv(
  typeKey: string,
  file: File
): Promise<ValidationStatus> {
  const requiredHeaders = getRequiredHeaders(typeKey);
  if (!requiredHeaders) return 'unknown';
  return await validateHeaders(file, requiredHeaders);
}
