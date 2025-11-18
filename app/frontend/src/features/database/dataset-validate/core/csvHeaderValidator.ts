/**
 * CSV ヘッダー検証(コア検証ロジック)
 * 
 * @deprecated このファイルは非推奨です。代わりに @shared を使用してください
 */

import { parseHeader as sharedParseHeader, validateHeaders as sharedValidateHeaders } from '@shared';
import type { ValidationStatus } from '../../shared/types/common';

/**
 * ヘッダーを検証する
 * @deprecated 代わりに @features/shared/csv-validation の validateHeaders を使用してください
 */
export async function validateHeaders(
  file: File,
  required: string[]
): Promise<ValidationStatus> {
  return await sharedValidateHeaders(file, required);
}

/**
 * CSV文字列からヘッダーをパースする
 * @deprecated 代わりに @features/shared/csv-validation の parseHeader を使用してください
 */
export function parseHeader(csvText: string): string[] {
  return sharedParseHeader(csvText);
}
