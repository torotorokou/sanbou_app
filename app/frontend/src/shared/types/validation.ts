/**
 * バリデーション関連の共通型定義
 * アプリケーション全体で共有するバリデーション状態の型とユーティリティ
 */

/**
 * バリデーション状態
 * - valid: バリデーション成功
 * - invalid: バリデーション失敗
 * - unknown: 未検証
 */
export type ValidationStatus = "valid" | "invalid" | "unknown";

/**
 * レガシーなステータス表記('ok'/'ng')をValidationStatusに変換
 * @param status - 'ok' | 'ng' | 'unknown'
 * @returns ValidationStatus
 */
export function normalizeValidationStatus(
  status: "ok" | "ng" | "unknown" | ValidationStatus,
): ValidationStatus {
  if (status === "ok") return "valid";
  if (status === "ng") return "invalid";
  if (status === "valid" || status === "invalid" || status === "unknown") {
    return status;
  }
  return "unknown";
}

/**
 * ValidationStatusをレガシー表記('ok'/'ng')に逆変換
 * @param status - ValidationStatus
 * @returns 'ok' | 'ng' | 'unknown'
 */
export function toLegacyValidationStatus(
  status: ValidationStatus,
): "ok" | "ng" | "unknown" {
  if (status === "valid") return "ok";
  if (status === "invalid") return "ng";
  return "unknown";
}
