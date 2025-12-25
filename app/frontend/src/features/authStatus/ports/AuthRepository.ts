/**
 * Auth Repository - 認証リポジトリインターフェース
 *
 * 認証情報を取得するためのポート定義。
 * Infrastructure 層でこのインターフェースを実装します。
 */

import type { AuthUser } from "../domain/authUser";

export interface AuthRepository {
  /**
   * 現在ログインしているユーザー情報を取得
   *
   * @returns 認証済みユーザー情報
   * @throws エラー時（認証失敗、ネットワークエラー等）
   */
  fetchCurrentUser(): Promise<AuthUser>;
}
