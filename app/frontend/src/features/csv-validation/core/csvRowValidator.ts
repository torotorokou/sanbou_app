/**
 * CSV 行検証（将来的な拡張用）
 */

import type { ValidationStatus } from "@/shared";

export async function validateRows(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _file: File,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _rules?: unknown,
): Promise<ValidationStatus> {
  // 将来的な実装: 行ごとのバリデーション
  return "unknown";
}
