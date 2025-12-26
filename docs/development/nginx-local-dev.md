# local_dev 環境での nginx 利用ガイド

## 概要

local_dev 環境で、本番環境（vm_stg / vm_prod）に近い nginx 経由のルーティングを使用して開発・検証できるようになりました。

## 起動方法

### 通常の開発環境（nginx なし）

```bash
# 従来通りの起動方法（各サービスに直接アクセス）
make up ENV=local_dev
```

**アクセスURL:**

- フロントエンド: http://localhost:5173
- AI API: http://localhost:8001
- Core API: http://localhost:8002
- Ledger API: http://localhost:8003
- RAG API: http://localhost:8004
- Manual API: http://localhost:8005

### nginx 付き開発環境（本番に近い構成）

```bash
# nginx 経由でアクセスする構成で起動
make dev-with-nginx
```

**アクセスURL:**

- **nginx 経由**: http://localhost:8080

  - フロントエンド: http://localhost:8080/
  - API (新形式): http://localhost:8080/api/core_api/...
  - API (旧形式): http://localhost:8080/core_api/...
  - Docs: http://localhost:8080/docs
  - Health Check: http://localhost:8080/health

- **直接アクセス**（デバッグ用）:
  - フロントエンド: http://localhost:5173
  - 各 API: http://localhost:800x（従来通り）

## 停止方法

```bash
# nginx 付き環境の停止
make down ENV=local_dev
```

## 設定ファイル

### nginx 設定ファイルの構成

```
app/nginx/conf.d/
├── dev.conf              # local_dev 用設定（新規追加）
├── stg.conf              # vm_stg 用設定
├── prod.conf             # vm_prod 用設定
├── _proxy_common.conf    # 共通 proxy 設定（VPN/STG用、IAPヘッダなし）
├── _proxy_headers.conf   # 共通 proxy 設定（PROD用、IAPヘッダあり）
└── default.conf          # 無効化済み（空ファイル）
```

### dev.conf の特徴

- **upstream**: docker-compose のサービス名（ai_api, core_api など）を使用
- **フロントエンド**: Vite 開発サーバー（frontend:5173）にプロキシ
  - WebSocket サポート（HMR 用）
- **バックエンドAPI**: 各 FastAPI サービスへのプロキシ
  - `/api/xxx/` 形式（推奨）
  - `/xxx/` 形式（レガシー対応）
- **認証**: なし（開発環境のため）

## トラブルシューティング

### nginx が起動しない

```bash
# nginx のログを確認
docker compose -f docker/docker-compose.dev.yml -p local_dev logs nginx

# 設定ファイルの構文チェック
docker compose -f docker/docker-compose.dev.yml -p local_dev exec nginx nginx -t
```

### ポート 8080 が使用中

環境変数 `DEV_NGINX_PORT` で変更可能:

```bash
# .env.local_dev に追加
DEV_NGINX_PORT=8888
```

### upstream ホストが見つからない

全サービスが起動しているか確認:

```bash
make ps ENV=local_dev
```

必要なサービスが起動していない場合:

```bash
make up ENV=local_dev
```

## 開発ワークフロー

### 1. 通常の開発（直接アクセス）

```bash
# フロントエンドとバックエンドに直接アクセス
make up ENV=local_dev

# ブラウザで http://localhost:5173 を開く
# API は http://localhost:800x で直接アクセス
```

**メリット:**

- 高速（プロキシのオーバーヘッドなし）
- デバッグしやすい
- HMR（Hot Module Replacement）が高速

### 2. 本番確認（nginx 経由）

```bash
# nginx 経由でアクセス
make dev-with-nginx

# ブラウザで http://localhost:8080 を開く
# 本番と同じルーティングで動作確認
```

**メリット:**

- 本番環境（vm_stg / vm_prod）と同じルーティング
- nginx のリバースプロキシ動作を検証
- CORS、ヘッダー、リダイレクトの挙動確認
- 本番デプロイ前の最終確認

## 環境間の違い

| 項目           | local_dev       | local_dev (nginx)       | vm_stg       | vm_prod      |
| -------------- | --------------- | ----------------------- | ------------ | ------------ |
| アクセス       | 直接            | nginx 経由              | nginx 経由   | nginx 経由   |
| ポート         | 5173, 800x      | 8080                    | 80, 443      | 80, 443      |
| フロントエンド | Vite dev server | Vite dev server (proxy) | 静的ファイル | 静的ファイル |
| 認証           | なし            | なし                    | VPN          | IAP          |
| ホットリロード | ✅              | ✅                      | ❌           | ❌           |
| ビルド         | 不要            | 不要                    | 必要         | 必要         |

## 参考

- Makefile: `make dev-with-nginx` の実装
- docker-compose.dev.yml: nginx サービス定義（profiles: with-nginx）
- app/nginx/conf.d/dev.conf: local_dev 用 nginx 設定
- app/nginx/conf.d/stg.conf: vm_stg 用 nginx 設定
- app/nginx/conf.d/prod.conf: vm_prod 用 nginx 設定
