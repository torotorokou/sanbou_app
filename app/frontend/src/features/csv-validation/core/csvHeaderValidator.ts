/**
 * CSV ヘッダー検証（コアロジック）
 *
 * database と report の両方で使用される共通検証ロジック
 */

import type { ValidationStatus } from "@/shared";
import { logger } from "@/shared";

/**
 * CSV文字列からヘッダーをパースする
 */
export function parseHeader(csvText: string): string[] {
  const firstLine = (csvText.split(/\r?\n/)[0] ?? "").trim();
  return firstLine ? firstLine.split(",").map((s) => s.trim()) : [];
}

/**
 * ヘッダーを検証する
 * @param file 検証対象のCSVファイル
 * @param required 必須ヘッダーの配列
 * @returns 検証結果
 *
 * 注: 最初の5つのヘッダーのみが必須ヘッダーと一致すればOKとする
 */
export async function validateHeaders(
  file: File,
  required: string[],
): Promise<ValidationStatus> {
  logger.log("[csvHeaderValidator] 検証開始:", file.name);
  logger.log("[csvHeaderValidator] 必須ヘッダー:", required);

  try {
    const text = await file.text();
    const headers = parseHeader(text);
    logger.log("[csvHeaderValidator] パース済みヘッダー(全体):", headers);

    // 最初の5つのヘッダーのみを検証
    const headersToCheck = headers.slice(0, 5);
    const requiredToCheck = required.slice(0, 5);

    logger.log(
      "[csvHeaderValidator] 検証対象ヘッダー(最初5つ):",
      headersToCheck,
    );
    logger.log("[csvHeaderValidator] 必須ヘッダー(最初5つ):", requiredToCheck);

    // 順序と内容が完全一致するかチェック
    const ok =
      requiredToCheck.length === headersToCheck.length &&
      requiredToCheck.every((h, i) => {
        const match = headersToCheck[i] === h;
        if (!match) {
          logger.log(
            `[csvHeaderValidator] 不一致: index=${i}, 期待="${h}", 実際="${headersToCheck[i]}"`,
          );
        }
        return match;
      });

    logger.log("[csvHeaderValidator] 検証結果:", ok ? "valid" : "invalid");
    return ok ? "valid" : "invalid";
  } catch (error) {
    console.error("[csvHeaderValidator] エラー発生:", error);
    return "invalid";
  }
}

/**
 * CSV文字列を直接検証する（ファイルではなくテキスト）
 */
export function validateHeadersFromText(
  csvText: string,
  required: string[],
): ValidationStatus {
  try {
    const headers = parseHeader(csvText);
    const headersToCheck = headers.slice(0, 5);
    const requiredToCheck = required.slice(0, 5);

    const ok =
      requiredToCheck.length === headersToCheck.length &&
      requiredToCheck.every((h, i) => headersToCheck[i] === h);

    return ok ? "valid" : "invalid";
  } catch (error) {
    console.error("[csvHeaderValidator] テキスト検証エラー:", error);
    return "invalid";
  }
}
