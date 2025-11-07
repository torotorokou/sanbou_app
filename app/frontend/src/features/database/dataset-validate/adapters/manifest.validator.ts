/**
 * マニフェスト CSV 検証アダプタ
 */

import { validateHeaders } from '../core/csvHeaderValidator';
import type { ValidationStatus } from '../../shared/types/common';

const MANIFEST_HEADERS: Record<string, string[]> = {
  manifest_primary: ['マニフェスト番号', '処分方法'],
  manifest_secondary: ['マニフェスト番号', '処分方法'],
};

export async function validateManifestCsv(
  typeKey: string,
  file: File
): Promise<ValidationStatus> {
  const requiredHeaders = MANIFEST_HEADERS[typeKey];
  if (!requiredHeaders) return 'unknown';
  return await validateHeaders(file, requiredHeaders);
}
