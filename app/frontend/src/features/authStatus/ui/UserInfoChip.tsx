/**
 * UserInfoChip - ユーザー情報表示コンポーネント
 * 
 * 現在ログインしているユーザーの情報を表示する小型のUIコンポーネント。
 * サイドバーやヘッダーに配置して、ユーザーに認証状態を伝えます。
 * 
 * 【表示内容】
 * - ローディング中: "ユーザー情報取得中..."
 * - エラー時: エラーメッセージ（赤色）
 * - 未ログイン: "未ログイン"
 * - ログイン中: "ログイン中：{表示名 or メールアドレス}"
 */

import type { FC } from "react";
import { useAuthStatusViewModel } from "../model/useAuthStatusViewModel";
import { customTokens } from "@/shared/theme/tokens";

export const UserInfoChip: FC = () => {
  const { user, isLoading, error } = useAuthStatusViewModel();

  // ローディング中の表示
  if (isLoading) {
    return (
      <span style={{
        fontSize: '12px',
        color: customTokens.colorTextSecondary,
      }}>
        ユーザー情報取得中...
      </span>
    );
  }

  // エラー時の表示
  if (error) {
    return (
      <span 
        style={{
          fontSize: '12px',
          color: customTokens.colorError,
        }}
        title={error}
      >
        {error}
      </span>
    );
  }

  // 未ログイン時の表示
  if (!user) {
    return (
      <span style={{
        fontSize: '12px',
        color: customTokens.colorTextSecondary,
      }}>
        未ログイン
      </span>
    );
  }

  // ログイン中の表示
  // 表示名が存在すればそれを使用、なければメールアドレスを使用
  const displayLabel = user.displayName ?? user.email;

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      borderRadius: '16px',
      border: `1px solid ${customTokens.colorBorderSecondary}`,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      padding: '6px 12px',
      fontSize: '13px',
    }}>
      <span style={{ 
        fontWeight: 600,
        color: customTokens.colorSiderText,
        opacity: 0.8,
      }}>
        ログイン中：
      </span>
      <span style={{ 
        color: customTokens.colorSiderText,
      }}>
        {displayLabel}
      </span>
    </div>
  );
};
