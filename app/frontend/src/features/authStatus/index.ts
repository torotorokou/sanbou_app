/**
 * Auth Status Feature - 認証状態管理機能
 *
 * 現在ログインしているユーザー情報を管理・表示する機能。
 * Feature-Sliced Design (FSD) に基づいた構成。
 *
 * 【エクスポート】
 * - UserInfoChip: ユーザー情報表示UIコンポーネント
 * - useAuth: グローバル認証状態フック（推奨）
 * - useAuthStatusViewModel: 認証状態管理ViewModel（後方互換性のため維持、非推奨）
 * - AuthUser: ユーザー型定義（型チェック用）
 *
 * 【注意】
 * - useAuthStatusViewModelは非推奨です。代わりにuseAuthを使用してください。
 * - useAuthはAuthProviderで管理される認証状態にアクセスします。
 */

// UI Components
export { UserInfoChip } from "./ui/UserInfoChip";

// Auth Hook (推奨)
export { useAuth } from "@app/providers/AuthProvider";

// ViewModel (後方互換性のため維持、非推奨)
export { useAuthStatusViewModel } from "./model/useAuthStatusViewModel";

// Types
export type { AuthUser } from "./domain/authUser";
