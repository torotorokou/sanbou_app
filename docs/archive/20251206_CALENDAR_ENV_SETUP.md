# Calendar Integration - 環境変数設定

## 概要

営業カレンダー機能の統合に伴い、フロントエンドから Core API の Calendar エンドポイントにアクセスするための環境変数を設定しました。

**重要**: `app/frontend/.env.local` ファイルは削除され、すべての環境変数は `env/.env.local_dev` に統合されました。

## 環境変数

### `VITE_API_BASE_URL`

- **用途**: フロントエンドから Calendar API（Core API）にアクセスするためのベース URL
- **設定場所**: `env/.env.local_dev` (開発環境)
- **デフォルト値**: `http://localhost:8003/api`

```bash
# env/.env.local_dev
VITE_API_BASE_URL=http://localhost:8003/api
```

## Vite 設定による環境変数の読み込み

`vite.config.ts` では以下のように環境変数を読み込みます：

1. `env/.env.common` - 全環境共通の設定
2. `env/.env.local_{mode}` - 環境別の設定（dev, stg, prod）
   - development mode → `.env.local_dev`
   - production mode → `.env.local_prod`
3. プロジェクトルート（`process.cwd()`）の `.env.local` - 互換性のため

`VITE_` プレフィックスの環境変数のみがクライアント側で利用可能になります。

## 開発環境での利用

### ローカル開発（ホットリロード）

環境変数は `env/.env.local_dev` から自動的に読み込まれます：

```bash
cd app/frontend
npm run dev
# Vite が env/.env.local_dev から VITE_API_BASE_URL を読み込む
```

### Docker Compose 利用時

Docker Compose では `env/.env.local_dev` を env_file として指定：

```yaml
# docker-compose.dev.yml
frontend:
  env_file:
    - ../../env/.env.common
    - ../../env/.env.local_dev
  environment:
    - NODE_ENV=development
```

Core API は `DEV_CORE_API_PORT` (8003) でホストにマッピングされます。

### フロントエンドでの使用例

```typescript
// HttpCalendarRepository.ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
```

## ステージ別設定

### 開発環境（dev）

- **ファイル**: `env/.env.local_dev`
- **Core API**: `http://localhost:8003/api`

### ステージング環境（stg）

- **ファイル**: `env/.env.local_stg` または `env/.env.vm_stg`
- **設定が必要**: Core API の実際の URL に応じて `VITE_API_BASE_URL` を追加

### 本番環境（prod）

- **ファイル**: `env/.env.vm_prod`
- **設定が必要**: Core API の実際の URL に応じて `VITE_API_BASE_URL` を追加

## 注意事項

1. **VITE\_ プレフィックス**

   - Vite ビルド時にフロントエンドに埋め込まれる環境変数は `VITE_` で始まる必要があります
   - このプレフィックスがない変数はフロントエンドコードから参照できません

2. **セキュリティ**

   - `VITE_` プレフィックスの環境変数はビルド時にクライアント側のコードに埋め込まれます
   - 機密情報（APIキー、シークレットなど）は含めないでください

3. **Docker Compose との統合**
   - フロントエンドコンテナでも `env/.env.local_dev` を env_file として指定することを推奨
   - または、docker-compose.yml の environment セクションで明示的に設定

## 関連ファイル

- `env/.env.local_dev` - ローカル開発環境の設定（環境変数の定義場所）
- `app/frontend/vite.config.ts` - Vite 設定（環境変数の読み込みロジック）
- `app/frontend/src/features/calendar/repository/http.calendar.repository.ts` - 環境変数を使用
- ~~`app/frontend/.env.local`~~ - **削除済み**: `env/.env.local_dev` に統合

## トラブルシューティング

### 環境変数が読み込まれない場合

1. **ファイルの存在確認**

   ```bash
   ls -la env/.env.local_dev
   ```

2. **VITE\_ プレフィックスの確認**

   - 環境変数名が `VITE_` で始まっていることを確認
   - 例: `API_BASE_URL` → `VITE_API_BASE_URL`

3. **サーバーの再起動**

   - 環境変数の変更後は Vite サーバーを再起動

   ```bash
   # 開発サーバーを停止 (Ctrl+C)
   npm run dev
   ```

4. **ビルド時の確認**
   ```bash
   npm run build
   # dist/ 内のファイルで環境変数が正しく埋め込まれているか確認
   ```
