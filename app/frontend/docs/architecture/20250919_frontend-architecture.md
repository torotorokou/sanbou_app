# フロントエンド レイアウト規約（React + Ant Design）

目的: 二重スクロールの根絶と、レイアウト責務の集約（MVC/SOLID）。

## 基本方針

- html, body, #root は `height: 100%`。
- アプリ全体は `MainLayout` がレイアウト責務を負い、ページは固定高さを持たない。
- 縦スクロールは常に `Layout.Content` 一箇所のみで発生させる。
- `100vh/100dvh` の使用禁止。必要なら `minHeight: 0` の付与や Flex で調整。

## 実装ルール

- `MainLayout.tsx`
  - ルート `<Layout>` に `{ minHeight: '100%', height: '100%' }`。
  - `<Content>` に `{ flex:1, overflowY:'auto', overflowX:'hidden', minHeight:0 }`。
- `Sidebar.tsx`
  - `<Sider>` は `{ position:'sticky', top:0, height:'100%' }`。
  - メニュー部は `{ height:'calc(100% - 64px)' }` で内部スクロール。
- ページコンポーネント
  - ルート要素に `height:'100%'` は可、`100vh/100dvh` 禁止。
  - セクションの内部でスクロールさせる必要がある場合は、親に `display:'flex'`、対象に `{ flex:1, minHeight:0, overflow:auto }` を適用。

## AntD Table

- 外側コンテナで高さを作り、Table の `scroll.y` 固定値（例: 400px）は禁止。
- 横スクロールは `scroll={{ x: 'max-content' }}` を基本とする。

## API呼び出し

- すべて `src/lib/apiClient.ts` の `apiGet/apiPost/apiGetBlob/apiPostBlob` を使用。
- サービス別パスは `/rag_api`, `/ledger_api`, `/manual_api` をエンドポイントで明示する。

## コンポーネント責務

- Model: `types/*` DTO、`services/*`（API repository）
- Controller: `pages/*`（画面ロジック薄め、UseCase は `hooks/*`）
- View: `components/*`（受け取った props を描画）
