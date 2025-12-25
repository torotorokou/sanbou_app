/**
 * AuthProvider - 認証プロバイダー
 *
 * アプリケーション全体の認証状態を管理し、初期化処理を担当します。
 *
 * 【責務】
 * - アプリケーション起動時に認証情報を取得
 * - 認証完了までローディング画面を表示
 * - 認証エラー時のエラー画面を表示
 * - 認証状態をContextで子コンポーネントに提供
 */

import React, { createContext, useContext, useEffect, useState } from "react";
import { Spin, Result, Button } from "antd";
import type { AuthUser } from "@features/authStatus/domain/authUser";
import { AuthHttpRepository } from "@features/authStatus/infrastructure/AuthHttpRepository";

/**
 * 認証コンテキストの型
 */
interface AuthContextType {
  /** 認証済みユーザー情報 */
  user: AuthUser | null;
  /** 認証状態が初期化中かどうか */
  isInitializing: boolean;
  /** 認証エラー */
  error: string | null;
  /** 認証情報を再取得する関数 */
  refetch: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * 認証状態を取得するカスタムフック
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

const repository = new AuthHttpRepository();

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * 認証プロバイダーコンポーネント
 *
 * アプリケーションのルートに配置し、全体の認証状態を管理します。
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = async () => {
    try {
      setIsInitializing(true);
      setError(null);
      const fetchedUser = await repository.fetchCurrentUser();
      setUser(fetchedUser);
    } catch (e) {
      const errorMessage =
        e instanceof Error ? e.message : "ユーザー情報の取得に失敗しました";
      setError(errorMessage);
      console.error("認証エラー:", e);
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  // 初期化中はローディング画面を表示
  if (isInitializing) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <Spin size="large" />
        <div style={{ color: "#666" }}>認証情報を確認しています...</div>
      </div>
    );
  }

  // 認証エラー時はエラー画面を表示
  if (error) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          padding: "24px",
        }}
      >
        <Result
          status="error"
          title="認証エラー"
          subTitle={error}
          extra={
            <Button type="primary" onClick={fetchUser}>
              再試行
            </Button>
          }
        />
      </div>
    );
  }

  const contextValue: AuthContextType = {
    user,
    isInitializing,
    error,
    refetch: fetchUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};
