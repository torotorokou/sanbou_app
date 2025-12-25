/**
 * APIレスポンス型定義とエラーハンドリング
 *
 * 機能:
 *   - 統一的なAPIレスポンス形式
 *   - カスタムApiErrorクラス
 *   - HTTPステータスコードとエラーコードの管理
 *
 * 設計方重:
 *   - FastAPIの backend_shared.adapters.presentation と互換性あり
 *   - フロントエンド側でのエラーハンドリングを統一
 *   - TypeScriptの型安全性を活用
 */

/**
 * APIレスポンスの共通形式
 *
 * バックエンドのSuccessApiResponse/ErrorApiResponseと対応。
 *
 * @template T - 成功時の結果型
 *
 * @example
 * // 成功レスポンス
 * const response: ApiResponse<User[]> = {
 *   status: 'success',
 *   code: 'USERS_FETCHED',
 *   detail: 'ユーザー一覧を取得しました',
 *   result: [{ id: 1, name: 'Taro' }]
 * };
 *
 * @example
 * // エラーレスポンス
 * const errorResponse: ApiResponse<null> = {
 *   status: 'error',
 *   code: 'USER_NOT_FOUND',
 *   detail: 'ユーザーが見つかりません',
 *   result: null,
 *   hint: 'IDを確認してください'
 * };
 */
export type ApiResponse<T> = {
  /** レスポンスステータス：'success' or 'error' */
  status: "success" | "error";
  /** エラーコード（大文字スネークケース） */
  code: string;
  /** ユーザー向け詳細メッセージ（日本語） */
  detail: string;
  /** 成功時の結果データ（エラー時はnull） */
  result?: T | null;
  /** ユーザーへのヒント（任意） */
  hint?: string | null;
};

/**
 * APIエラークラス
 *
 * HTTPエラーを抽象化し、フロントエンドでのエラーハンドリングを統一する。
 *
 * 機能:
 *   - HTTPステータスコードとエラーコードの両方を保持
 *   - ユーザー向けメッセージとトレースIDを含む
 *   - Ant Designのnotification/messageで表示しやすい形式
 *
 * @example
 * // 基本的な使用例
 * try {
 *   const response = await apiClient.get('/users');
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     console.error(`Error: ${error.code} (${error.httpStatus})`);
 *     notification.error({
 *       message: error.title || 'エラー',
 *       description: error.userMessage,
 *       traceId: error.traceId
 *     });
 *   }
 * }
 *
 * @example
 * // カスタムエラーの生成
 * throw new ApiError(
 *   'VALIDATION_ERROR',
 *   400,
 *   '入力値が不正です',
 *   'バリデーションエラー',
 *   'trace-12345'
 * );
 */
export class ApiError extends Error {
  /** エラーコード（例: 'USER_NOT_FOUND', 'VALIDATION_ERROR'） */
  code: string;
  /** HTTPステータスコード（例: 404, 400, 500） */
  httpStatus: number;
  /** ユーザー向けエラーメッセージ（日本語） */
  userMessage: string;
  /** エラータイトル（任意、notificationのtitleに使用） */
  title?: string;
  /** トレースID（デバッグ用、バックエンドログと紐付け） */
  traceId?: string;

  /**
   * ApiErrorコンストラクタ
   *
   * @param code - エラーコード（大文字スネークケース推奨）
   * @param httpStatus - HTTPステータスコード
   * @param userMessage - ユーザー向けメッセージ
   * @param title - エラータイトル（任意）
   * @param traceId - トレースID（任意）
   */
  constructor(
    code: string,
    httpStatus: number,
    userMessage: string,
    title?: string,
    traceId?: string,
  ) {
    super(userMessage);
    this.name = "ApiError";
    this.code = code;
    this.httpStatus = httpStatus;
    this.userMessage = userMessage;
    this.title = title;
    this.traceId = traceId;
  }
}
