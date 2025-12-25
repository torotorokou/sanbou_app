/**
 * Auth HTTP Repository - 認証リポジトリ HTTP 実装
 *
 * バックエンドの /auth/me エンドポイントを呼び出して
 * ユーザー情報を取得する実装。
 */

import type { AuthRepository } from '../ports/AuthRepository';
import type { AuthUser } from '../domain/authUser';
import { coreApi } from '@/shared';

/**
 * バックエンドからのレスポンス型
 */
type AuthMeResponse = {
  email: string;
  display_name?: string | null;
  user_id?: string | null;
  role?: string | null;
};

export class AuthHttpRepository implements AuthRepository {
  /**
   * 現在ログインしているユーザー情報を取得
   *
   * バックエンドの GET /auth/me を呼び出します。
   *
   * @returns 認証済みユーザー情報
   * @throws エラー時（401/403/ネットワークエラー等）
   */
  async fetchCurrentUser(): Promise<AuthUser> {
    const response = await coreApi.get<AuthMeResponse>('/core_api/auth/me');

    return {
      email: response.email,
      displayName: response.display_name ?? null,
      userId: response.user_id ?? null,
      role: response.role ?? null,
    };
  }
}
