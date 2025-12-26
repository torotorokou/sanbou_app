# app/providers

## 役割

アプリケーション全体で使用するProviders（Context、Theme等）を管理します。

## 責務

- Reactコンテキストプロバイダー
- テーマプロバイダー
- 認証プロバイダー
- グローバル状態管理プロバイダー

## FSDレイヤー

**app層** - アプリケーション横断的な状態・設定提供

## 想定ファイル

- `ThemeProvider.tsx` - テーマ管理
- `AuthProvider.tsx` - 認証管理
- `AppProviders.tsx` - プロバイダーラッパー
