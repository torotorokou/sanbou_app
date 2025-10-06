# app/router

## 役割
アプリケーション全体のルーティング設定と、ルート定義の集約を管理します。

## 責務
- ルート定義（パス、コンポーネントのマッピング）
- ルートガード（認証、権限チェック）
- ルート遷移処理
- 404エラーハンドリング

## 依存方向
- `pages/*` - ページコンポーネントをインポート
- `shared/constants/router` - ルートパス定数

## 例
```typescript
// routes.tsx
export const routes = [
  { path: ROUTER_PATHS.HOME, component: HomePage },
  { path: ROUTER_PATHS.DASHBOARD, component: DashboardPage },
];
```
