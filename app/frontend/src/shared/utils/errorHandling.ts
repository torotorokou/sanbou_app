/**
 * Error Handling Utilities
 * 統一されたエラーハンドリングパターン
 *
 * このモジュールは、API呼び出しやその他の非同期処理における
 * エラーハンドリングを標準化し、通知機構との統合を簡素化します。
 *
 * @module shared/utils/errorHandling
 */

import { notifyApiError, notifyError } from "@features/notification";

/**
 * APIエラー型
 * axios/fetchのエラーレスポンスを想定
 */
export interface ApiError {
  response?: {
    data?: {
      detail?: string;
      message?: string;
      error_code?: string;
    };
    status?: number;
  };
  message?: string;
}

/**
 * 標準的なAPI呼び出しエラーハンドリング
 *
 * try-catchブロックをラップし、エラー時の通知を自動化します。
 * エラー時はnullを返すため、呼び出し側でnullチェックが必要です。
 *
 * @example
 * ```typescript
 * // Repository内での使用例
 * export class UserRepository {
 *   async getUser(id: string): Promise<User | null> {
 *     return await handleApiCall(
 *       () => coreApi.get<User>(`/api/users/${id}`),
 *       'ユーザー取得'
 *     );
 *   }
 * }
 *
 * // ViewModel内での使用例
 * const data = await handleApiCall(
 *   () => repository.fetchData(params),
 *   'データ取得'
 * );
 * if (data) {
 *   setState(data);
 * }
 * ```
 *
 * @param apiCall - 実行するAPI呼び出し関数
 * @param operationName - 操作名（エラーメッセージに使用）
 * @returns 成功時はAPI呼び出しの結果、失敗時はnull
 */
export async function handleApiCall<T>(
  apiCall: () => Promise<T>,
  operationName: string,
): Promise<T | null> {
  try {
    return await apiCall();
  } catch (error) {
    notifyApiError(error, `${operationName}に失敗しました`);
    console.error(`[${operationName}] Error:`, error);
    return null;
  }
}

/**
 * リトライ付きAPI呼び出し
 *
 * ネットワークエラーや一時的な障害に対して、指定回数までリトライします。
 * リトライ間隔は attempt * 1000ms（1秒、2秒、3秒...）で増加します。
 *
 * @example
 * ```typescript
 * // 重要なアップロード処理など
 * const result = await handleApiCallWithRetry(
 *   () => coreApi.post('/api/upload', formData),
 *   'ファイルアップロード',
 *   3  // 最大3回リトライ
 * );
 * ```
 *
 * @param apiCall - 実行するAPI呼び出し関数
 * @param operationName - 操作名（エラーメッセージに使用）
 * @param maxRetries - 最大リトライ回数（デフォルト: 3）
 * @returns 成功時はAPI呼び出しの結果、全リトライ失敗時はnull
 */
export async function handleApiCallWithRetry<T>(
  apiCall: () => Promise<T>,
  operationName: string,
  maxRetries = 3,
): Promise<T | null> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      if (attempt === maxRetries) {
        notifyApiError(
          error,
          `${operationName}に失敗しました（${maxRetries}回試行）`,
        );
        console.error(`[${operationName}] Final attempt failed:`, error);
        return null;
      }
      console.warn(`[${operationName}] Retry ${attempt}/${maxRetries}...`);
      await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
    }
  }
  return null;
}

/**
 * 汎用エラーハンドリング（非API処理用）
 *
 * ファイル処理、計算処理など、APIに関係しない処理のエラーハンドリングに使用します。
 *
 * @example
 * ```typescript
 * const result = await handleOperation(
 *   async () => {
 *     // 複雑な計算処理
 *     return processData(input);
 *   },
 *   '計算処理'
 * );
 * ```
 *
 * @param operation - 実行する操作関数
 * @param operationName - 操作名（エラーメッセージに使用）
 * @returns 成功時は操作の結果、失敗時はnull
 */
export async function handleOperation<T>(
  operation: () => Promise<T>,
  operationName: string,
): Promise<T | null> {
  try {
    return await operation();
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "不明なエラー";
    notifyError(`${operationName}に失敗しました: ${errorMessage}`);
    console.error(`[${operationName}] Error:`, error);
    return null;
  }
}

/**
 * エラーコードの標準化規約
 *
 * 新しいエラーコードを追加する際は、以下の規約に従ってください：
 * - 命名規則: UPPER_SNAKE_CASE
 * - カテゴリプレフィックスを使用
 * - 明確で一貫性のある命名
 *
 * @example
 * ```typescript
 * // ✅ 良い例
 * const GOOD_EXAMPLES = [
 *   'INPUT_INVALID',
 *   'VALIDATION_ERROR',
 *   'USER_NOT_FOUND',
 *   'PROCESSING_TIMEOUT',
 *   'JOB_FAILED',
 * ];
 *
 * // ❌ 悪い例
 * const BAD_EXAMPLES = [
 *   'error',                // 小文字
 *   'Error',                // PascalCase
 *   'validation-error',     // kebab-case
 *   'userNotFound',         // camelCase
 * ];
 * ```
 */
export const ERROR_CODE_CONVENTIONS = {
  /**
   * 命名規則
   */
  naming: "UPPER_SNAKE_CASE" as const,

  /**
   * カテゴリプレフィックス
   * 各カテゴリはエラーの種類を表します
   */
  categories: [
    "INPUT_*", // 入力エラー（フォーム、パラメータなど）
    "VALIDATION_*", // バリデーションエラー
    "AUTH_*", // 認証・認可エラー
    "*_NOT_FOUND", // リソース未発見
    "PROCESSING_*", // 処理エラー（計算、変換など）
    "TIMEOUT", // タイムアウト
    "JOB_*", // ジョブエラー（バックグラウンド処理）
    "NETWORK_*", // ネットワークエラー
    "DATABASE_*", // データベースエラー
  ] as const,

  /**
   * 命名例
   */
  examples: {
    /** 推奨される命名 */
    good: [
      "INPUT_INVALID",
      "VALIDATION_ERROR",
      "USER_NOT_FOUND",
      "PROCESSING_TIMEOUT",
      "JOB_FAILED",
      "AUTH_REQUIRED",
      "NETWORK_ERROR",
      "DATABASE_CONNECTION_FAILED",
    ],
    /** 避けるべき命名 */
    bad: [
      "error", // 小文字
      "Error", // PascalCase
      "validation-error", // kebab-case
      "userNotFound", // camelCase
      "err", // 省略形
      "failed", // 抽象的すぎる
    ],
  },

  /**
   * エラーコード追加時のチェックリスト
   */
  checklist: [
    "[ ] UPPER_SNAKE_CASE で命名されている",
    "[ ] カテゴリプレフィックスを使用している",
    "[ ] 既存のエラーコードと重複していない",
    "[ ] エラーの原因と種類が明確に分かる",
    "[ ] ドキュメント（features/notification/domain/config.ts）に追加済み",
  ],
} as const;

/**
 * エラーコードの検証
 * 開発時にエラーコードが規約に準拠しているかチェックします
 *
 * @param errorCode - 検証するエラーコード
 * @returns 規約に準拠している場合はtrue
 */
export function validateErrorCode(errorCode: string): boolean {
  // UPPER_SNAKE_CASE チェック
  const isUpperSnakeCase = /^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$/.test(errorCode);

  if (!isUpperSnakeCase) {
    console.warn(
      `[Error Code] "${errorCode}" は UPPER_SNAKE_CASE ではありません`,
    );
    return false;
  }

  // カテゴリプレフィックスチェック（推奨）
  const hasKnownCategory = ERROR_CODE_CONVENTIONS.categories.some((pattern) => {
    const regex = pattern.replace("*", ".*");
    return new RegExp(`^${regex}$`).test(errorCode);
  });

  if (!hasKnownCategory) {
    console.info(
      `[Error Code] "${errorCode}" は既知のカテゴリに該当しません（新規カテゴリの可能性）`,
    );
  }

  return true;
}
