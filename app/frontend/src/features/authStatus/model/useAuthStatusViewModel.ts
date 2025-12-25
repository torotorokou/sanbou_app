/**
 * useAuthStatusViewModel - 認証状態管理 ViewModel
 *
 * 現在ログインしているユーザー情報を取得・管理するカスタムフック。
 * MVVM パターンに基づき、UI（View）とビジネスロジックを分離します。
 *
 * 【責務】
 * - 初回マウント時に /auth/me を1回だけ呼び出し
 * - ユーザー情報、ローディング状態、エラー状態を管理
 * - アンマウント時のクリーンアップ
 */

import { useEffect, useState } from "react";
import type { AuthUser } from "../domain/authUser";
import type { AuthRepository } from "../ports/AuthRepository";
import { AuthHttpRepository } from "../infrastructure/AuthHttpRepository";

/**
 * ViewModel の状態型
 */
type State = {
  /** 認証済みユーザー情報（未取得時は null） */
  user: AuthUser | null;
  /** ローディング中フラグ */
  isLoading: boolean;
  /** エラーメッセージ（エラー時のみ） */
  error: string | null;
};

/**
 * リポジトリインスタンス（シングルトン）
 *
 * コンポーネントごとに新しいインスタンスを作成するのではなく、
 * モジュールレベルで1つのインスタンスを共有します。
 */
const repository: AuthRepository = new AuthHttpRepository();

/**
 * 認証状態管理カスタムフック
 *
 * 初回マウント時に自動的にユーザー情報を取得します。
 * 取得成功時は user にユーザー情報をセット、
 * 失敗時は error にエラーメッセージをセットします。
 *
 * @returns ユーザー情報、ローディング状態、エラー状態
 *
 * @example
 * ```tsx
 * const { user, isLoading, error } = useAuthStatusViewModel();
 *
 * if (isLoading) {
 *   return <span>読み込み中...</span>;
 * }
 *
 * if (error) {
 *   return <span>エラー: {error}</span>;
 * }
 *
 * if (!user) {
 *   return <span>未ログイン</span>;
 * }
 *
 * return <span>{user.displayName ?? user.email}</span>;
 * ```
 */
export const useAuthStatusViewModel = () => {
  const [state, setState] = useState<State>({
    user: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    // アンマウント時のフラグ
    // フェッチ中にアンマウントされた場合、setState を呼ばないようにする
    let cancelled = false;

    (async () => {
      try {
        const user = await repository.fetchCurrentUser();

        // アンマウント済みの場合は setState しない
        if (cancelled) return;

        setState({
          user,
          isLoading: false,
          error: null,
        });
      } catch (e) {
        // アンマウント済みの場合は setState しない
        if (cancelled) return;

        // エラーメッセージの抽出
        const errorMessage =
          e instanceof Error ? e.message : "ユーザー情報の取得に失敗しました";

        setState({
          user: null,
          isLoading: false,
          error: errorMessage,
        });
      }
    })();

    // クリーンアップ: アンマウント時にフラグを立てる
    return () => {
      cancelled = true;
    };
  }, []); // 空配列 = 初回マウント時のみ実行

  return state;
};
