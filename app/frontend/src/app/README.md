# app/

## 役割

アプリケーションの初期化とグローバル設定を管理するレイヤー

## 配置するもの

- **ルーター設定**: React Router の設定、ルート定義
- **グローバル設定**: テーマプロバイダー、多言語化設定、グローバルストア初期化
- **エラーバウンダリ**: アプリケーション全体のエラーハンドリング
- **プロバイダー**: 認証プロバイダー、通知プロバイダーなど
- **アプリケーションエントリーポイント**: App コンポーネント

## 依存関係

- ✅ pages, widgets, features, entities, shared に依存可能
- ❌ 他のレイヤーから依存されない（最上位レイヤー）

## 例

```
app/
├── providers/
│   ├── ThemeProvider.tsx
│   ├── AuthProvider.tsx
│   └── NotificationProvider.tsx
├── routes/
│   └── AppRoutes.tsx
├── errorBoundary/
│   └── ErrorBoundary.tsx
└── App.tsx
```
