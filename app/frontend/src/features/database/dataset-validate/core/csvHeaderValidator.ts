/**
 * CSV ヘッダー検証（コア検証ロジック）
 */

import { parseHeader } from '../../shared/csv/parseCsv';
import type { ValidationStatus } from '../../shared/types/common';

export async function validateHeaders(
  file: File,
  required: string[]
): Promise<ValidationStatus> {
  try {
    const text = await file.text();
    const headers = parseHeader(text);
    const ok = required.every(h => headers.includes(h));
    return ok ? 'valid' : 'invalid';
  } catch {
    return 'invalid';
  }
}
