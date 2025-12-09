/**
 * Auth Status Feature - 認証状態管理機能
 * 
 * 現在ログインしているユーザー情報を管理・表示する機能。
 * Feature-Sliced Design (FSD) に基づいた構成。
 * 
 * 【エクスポート】
 * - UserInfoChip: ユーザー情報表示UIコンポーネント
 * - useAuthStatusViewModel: 認証状態管理ViewModel（高度な使用ケース向け）
 * - AuthUser: ユーザー型定義（型チェック用）
 */

// UI Components
export { UserInfoChip } from "./ui/UserInfoChip";

// ViewModel (advanced usage)
export { useAuthStatusViewModel } from "./model/useAuthStatusViewModel";

// Types
export type { AuthUser } from "./domain/authUser";
