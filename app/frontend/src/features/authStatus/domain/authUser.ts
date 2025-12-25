/**
 * Auth User - 認証ユーザー型定義
 *
 * バックエンドの AuthUser エンティティに対応するフロントエンド型。
 */

export type AuthUser = {
  /**
   * ユーザーのメールアドレス（一意識別子）
   */
  email: string;

  /**
   * ユーザーの表示名（オプション）
   *
   * UI に表示する際に使用します。
   * 未設定の場合は email を表示名として使用します。
   */
  displayName?: string | null;

  /**
   * ユーザーID（オプション）
   *
   * システム内部の識別子。
   */
  userId?: string | null;

  /**
   * ユーザーロール（オプション）
   *
   * 権限管理に使用します（例: "admin", "user", "viewer"）。
   */
  role?: string | null;
};
