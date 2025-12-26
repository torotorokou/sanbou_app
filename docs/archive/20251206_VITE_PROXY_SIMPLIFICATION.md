# Vite Proxy & API 呼び出しの簡素化

## 概要

このドキュメントは `chore/vite-proxy-simplify` ブランチで実施した、Vite設定とAPI呼び出しパターンの統一・簡素化について説明します。

## 変更内容

### 1. vite.config.ts の簡素化

#### 削除した機能

- **YAML plugin**: 未使用だったため削除（`@rollup/plugin-yaml`）
- **レガシープロキシエンドポイント**: `/ai_api`, `/ledger_api`, `/rag_api`, `/manual_api` など複数のプロキシ設定を削除
- **カスタム環境変数読み込みロジック**: 約40行の複雑なファイル走査処理を削除

#### 保持した機能

- **custom-media plugin**: CSSの`@custom-media`ルール処理（5つのCSSファイルで使用中）
- **単一プロキシエンドポイント**: `/api` → `http://localhost:8003` (Core API) のみ
- **環境変数読み込み**: Vite標準の`loadEnv()`を使用

#### 変更後の構成

```typescript
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import customMediaPlugin from "./src/plugins/vite-plugin-custom-media";

export default defineConfig(({ mode }) => {
  const envDir = path.resolve(__dirname, "../../env");
  const env = loadEnv(mode, envDir, "");

  return {
    envDir,
    plugins: [react(), customMediaPlugin()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
        "@/app": path.resolve(__dirname, "src/app"),
        "@/shared": path.resolve(__dirname, "src/shared"),
        "@/features": path.resolve(__dirname, "src/features"),
        "@/pages": path.resolve(__dirname, "src/pages"),
        // Backward compatibility
        "@app": path.resolve(__dirname, "src/app"),
        "@shared": path.resolve(__dirname, "src/shared"),
        "@features": path.resolve(__dirname, "src/features"),
        "@pages": path.resolve(__dirname, "src/pages"),
      },
    },
    server: {
      proxy: {
        "/api": { target: `http://localhost:${CORE_PORT}`, changeOrigin: true },
      },
    },
  };
});
```

**削減量**: 約70行 → 約50行（30%削減）

### 2. tsconfig.json paths の統一

#### 変更前

20以上のpath aliasが定義されていた（`@app`, `@domain`, `@infra`, `@controllers`, `@entities`, `@widgets`, `@components`, `@hooks`, `@services`, `@stores`, `@types`, `@utils`, `@config`, `@constants`, `@layout`, `@theme` など）

#### 変更後

9つのaliasに統一（スラッシュあり/なし両方サポート）:

```json
{
  "paths": {
    "@/*": ["*"],
    "@/app/*": ["app/*"],
    "@/shared/*": ["shared/*"],
    "@/features/*": ["features/*"],
    "@/pages/*": ["pages/*"],
    "@app/*": ["app/*"], // 後方互換
    "@shared/*": ["shared/*"], // 後方互換
    "@features/*": ["features/*"], // 後方互換
    "@pages/*": ["pages/*"] // 後方互換
  }
}
```

### 3. API呼び出しの相対パス化

#### 変更前

```typescript
// 環境変数を使用した絶対URL
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const url = `${apiBaseUrl}/calendar/month?year=${year}&month=${month}`;
```

#### 変更後

```typescript
// 相対パスでプロキシを活用
const url = `/api/calendar/month?year=${year}&month=${month}`;
```

**影響ファイル**:

- `src/features/calendar/repository/http.calendar.repository.ts`
- `src/features/notification/controller/sse.ts`

**メリット**:

- 環境変数依存が減少
- Vite dev serverのプロキシが自動適用される
- 本番環境でもNginxリバースプロキシで同じパターンが使える

### 4. 環境変数ファイルの明確化

#### env/.env.local_dev の変更

```bash
# === Frontend: API Base URL (deprecated) ===
# 注意: フロントエンドでは相対パス /api を使用してください
# Vite dev server が /api を localhost:${DEV_CORE_API_PORT} にプロキシします
# この変数は後方互換のために残していますが、新規コードでは使用しないでください
VITE_API_BASE_URL=http://localhost:8003/api
```

既存コードとの互換性を保ちながら、新規開発では相対パスを推奨することを明記。

### 5. package.json の整理

#### 削除した依存関係

```json
{
  "devDependencies": {
    "@rollup/plugin-yaml": "^4.1.2" // 削除
  }
}
```

## 実装前後の比較

| 項目                      | Before    | After                       | 改善          |
| ------------------------- | --------- | --------------------------- | ------------- |
| vite.config.ts 行数       | ~70行     | ~50行                       | -30%          |
| プロキシエンドポイント数  | 5+        | 1                           | BFFパターン化 |
| tsconfig paths エントリ数 | 20+       | 9                           | -55%          |
| 環境変数参照箇所          | 3ファイル | 0ファイル（deprecated扱い） | 依存削減      |
| npmパッケージ数           | +1 (yaml) | 0                           | 軽量化        |

## 動作確認

### TypeCheck

```bash
npm run typecheck
```

**結果**: 既存エラー4件のみ（`DASHBOARD`ルート未定義、カレンダー無関係）

### Lint

```bash
npm run lint
```

**結果**: 既存エラー1件のみ（未使用import、カレンダー無関係）

### Dev Server

```bash
npm run dev
```

**結果**: ✅ エラーなしで起動（ポート5174）

### カレンダー機能確認

1. ブラウザで `http://localhost:5174/dashboard/ukeire` にアクセス
2. 営業カレンダーカードが表示される
3. モックデータで2025年1月のカレンダーが表示される

## 今後の推奨パターン

### ✅ 推奨: 相対パスでAPI呼び出し

```typescript
// Good: Viteプロキシが自動適用される
const response = await fetch("/api/calendar/month?year=2025&month=1");
```

### ❌ 非推奨: 環境変数の絶対URL

```typescript
// Bad: 環境変数に依存、本番設定が複雑化
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const response = await fetch(`${apiBaseUrl}/calendar/month?...`);
```

## BFFパターンの採用

Core API (`localhost:8003`) が Backend for Frontend (BFF) として機能:

- フロントエンドは `/api/**` のみを呼び出す
- Core APIが他のマイクロサービス（RAG API、Ledger API等）を内部で呼び出す
- フロントエンドの環境変数設定が簡素化される

## 関連ファイル

- `app/frontend/vite.config.ts` - Vite設定の簡素化
- `app/frontend/tsconfig.json` - paths設定の統一
- `env/.env.local_dev` - 環境変数の明確化
- `src/features/calendar/repository/http.calendar.repository.ts` - 相対パス化
- `src/features/notification/controller/sse.ts` - 相対パス化
- `app/frontend/package.json` - 不要依存削除

## マイグレーションガイド

既存のAPI呼び出しコードを更新する場合:

1. `import.meta.env.VITE_API_BASE_URL` を削除
2. 絶対URL `${apiBaseUrl}/endpoint` を相対パス `/api/endpoint` に変更
3. SSEなど他のAPIも同様に相対パス化（例: `/ledger_api/notifications/stream`）

## コミットメッセージ

```
chore(vite): simplify proxy to /api; unify env via /env; align tsconfig paths; make API calls relative

- Remove unused yaml plugin and legacy proxy endpoints
- Reduce vite.config.ts from ~70 to ~50 lines
- Unify tsconfig paths from 20+ to 9 aliases
- Convert API calls to relative paths (/api/*)
- Add deprecation notice to VITE_API_BASE_URL
- Remove @rollup/plugin-yaml dependency
- Adopt BFF pattern (Core API as single frontend proxy)
```

---

**日付**: 2025-10-16  
**ブランチ**: `chore/vite-proxy-simplify`  
**作成者**: GitHub Copilot
