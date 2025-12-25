# Local Demo 環境構築ドキュメント

**作成日**: 2025-11-27  
**環境**: local_demo（ローカルデモ環境）  
**目的**: local_dev と完全に独立したデモ用環境の提供

---

## 📋 概要

`local_demo` 環境は、`local_dev` と完全に独立したローカルデモ環境です。以下が独立しています：

- **Docker コンテナ**（プロジェクト名: `local_demo`）
- **ポート番号**（dev と衝突しない）
- **データベース**（`sanbou_demo` / `data/local_demo/postgres/`）
- **環境変数**（`env/.env.local_demo`）
- **シークレット**（`secrets/.env.local_demo.secrets`）

### ユースケース

- 本番相当のデータでデモを実施したい
- 開発環境を壊さずに新機能を試したい
- 複数の環境を同時に起動してテストしたい
- クライアントデモ用に安定した環境を用意したい

---

## 🚀 クイックスタート

### 1. Demo 環境の起動

```bash
make demo-up
```

起動が完了したら、以下の URL にアクセスできます：

- **フロントエンド**: http://localhost:5174
- **Core API (BFF)**: http://localhost:8013/docs
- **AI API**: http://localhost:8011/docs
- **Ledger API**: http://localhost:8012/docs
- **RAG API**: http://localhost:8014/docs
- **Manual API**: http://localhost:8015/docs
- **PostgreSQL**: `localhost:5433`

### 2. 状態確認

```bash
make demo-ps
```

### 3. ログ確認

```bash
# 全サービスのログ
make demo-logs

# 特定のサービスのみ
make demo-logs S=core_api
make demo-logs S=frontend
```

### 4. 停止

```bash
make demo-down
```

---

## 🔧 主要な Makefile コマンド

| コマンド                      | 説明                               |
| ----------------------------- | ---------------------------------- |
| `make demo-up`                | demo 環境を起動（ビルド含む）      |
| `make demo-down`              | demo 環境を停止                    |
| `make demo-restart`           | demo 環境を再起動                  |
| `make demo-ps`                | コンテナの状態を確認               |
| `make demo-logs`              | ログをリアルタイム表示             |
| `make demo-db-shell`          | PostgreSQL に接続                  |
| `make demo-db-clone-from-dev` | local_dev の DB を demo にクローン |

---

## 📊 ポート番号一覧

### local_dev vs local_demo

| サービス       | local_dev | local_demo | 差分 |
| -------------- | --------- | ---------- | ---- |
| Frontend       | 5173      | 5174       | +1   |
| AI API         | 8001      | 8011       | +10  |
| Ledger API     | 8002      | 8012       | +10  |
| Core API (BFF) | 8003      | 8013       | +10  |
| RAG API        | 8004      | 8014       | +10  |
| Manual API     | 8005      | 8015       | +10  |
| PostgreSQL     | 5432      | 5433       | +1   |

---

## 🗄️ データベース管理

### DB に接続

```bash
make demo-db-shell
```

PostgreSQL に接続後、以下のコマンドが使えます：

```sql
-- データベース一覧
\l

-- テーブル一覧
\dt

-- スキーマ一覧
\dn

-- 特定のテーブルの構造確認
\d table_name

-- 終了
\q
```

### local_dev → local_demo への DB クローン

開発環境のデータをデモ環境にコピーする場合：

```bash
make demo-db-clone-from-dev
```

**処理内容**:

1. `local_dev` の `sanbou_dev` DB をダンプ
2. ダンプファイルを `backup/dev_to_demo.dump` に保存
3. `local_demo` の既存 `sanbou_demo` DB を削除
4. 新しい `sanbou_demo` DB を作成
5. ダンプをリストア

**注意**: この操作は `local_demo` の既存データを完全に上書きします。

### 手動で DB クローンする場合

```bash
# 1. local_dev からダンプ
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  pg_dump -U myuser -d sanbou_dev --format=custom --file=/tmp/dev_to_demo.dump

docker compose -f docker/docker-compose.dev.yml -p local_dev cp \
  db:/tmp/dev_to_demo.dump ./backup/dev_to_demo.dump

# 2. local_demo にコピー
docker compose -f docker/docker-compose.local_demo.yml -p local_demo cp \
  ./backup/dev_to_demo.dump db:/tmp/dev_to_demo.dump

# 3. DB を再作成してリストア
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec -T db \
  dropdb -U myuser --if-exists sanbou_demo

docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec -T db \
  createdb -U myuser sanbou_demo

docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec -T db \
  pg_restore -U myuser -d sanbou_demo /tmp/dev_to_demo.dump
```

---

## 🔄 dev と demo の同時起動

`local_dev` と `local_demo` は完全に独立しているため、同時起動が可能です：

```bash
# 開発環境を起動
make up ENV=local_dev

# デモ環境を起動
make demo-up

# 両方の状態を確認
docker ps --filter "name=local_dev" --filter "name=local_demo"
```

### 確認ポイント

- ポートの衝突がないこと
- コンテナ名が重複していないこと（プロジェクト名で分離）
- それぞれのフロントエンドにアクセスできること
  - dev: http://localhost:5173
  - demo: http://localhost:5174

---

## ⚙️ 環境設定ファイル

### 設定ファイルの構成

```
env/
├── .env.common              # 全環境共通設定
├── .env.local_dev          # local_dev 専用
└── .env.local_demo         # local_demo 専用（新規）

secrets/
├── .env.local_dev.secrets  # local_dev シークレット
└── .env.local_demo.secrets # local_demo シークレット（新規）
```

### 主要な環境変数（.env.local_demo）

| 変数名              | 値                                                   | 説明                       |
| ------------------- | ---------------------------------------------------- | -------------------------- |
| `APP_TAG`           | `local_demo`                                         | 環境識別子                 |
| `STAGE`             | `demo`                                               | ステージ名                 |
| `POSTGRES_DB`       | `sanbou_demo`                                        | データベース名             |
| `DATABASE_URL`      | `postgresql://<USER>:<PASSWORD>@db:5432/sanbou_demo` | DB接続URL (secrets で設定) |
| `PUBLIC_BASE_URL`   | `http://localhost:5174`                              | フロントエンドURL          |
| `DEV_FRONTEND_PORT` | `5174`                                               | フロントエンドポート       |
| `DEV_CORE_API_PORT` | `8013`                                               | Core API ポート            |
| `DEV_DB_PORT`       | `5433`                                               | PostgreSQL ポート          |

---

## 📁 ディレクトリ構造

```
sanbou_app/
├── docker/
│   ├── docker-compose.dev.yml        # local_dev 用
│   └── docker-compose.local_demo.yml # local_demo 用（新規）
├── env/
│   ├── .env.common
│   ├── .env.local_dev
│   └── .env.local_demo               # 新規
├── secrets/
│   ├── .env.local_dev.secrets
│   └── .env.local_demo.secrets       # 新規
├── data/
│   ├── postgres_v17/                 # local_dev の DB データ
│   └── local_demo/
│       └── postgres/                 # local_demo の DB データ（新規）
├── backup/                           # DB バックアップ保存先
└── makefile                          # demo-* ターゲット追加
```

---

## 🛡️ トラブルシューティング

### 1. ポートが既に使用されている

**症状**: `Error: bind: address already in use`

**原因**: 他のプロセスが demo のポートを使用している

**解決方法**:

```bash
# ポート使用状況を確認（Linux）
sudo lsof -i :5174  # フロントエンド
sudo lsof -i :8013  # Core API
sudo lsof -i :5433  # PostgreSQL

# プロセスを停止してから再起動
make demo-down
make demo-up
```

### 2. DB 接続エラー

**症状**: `psql: connection refused` または `could not connect to server`

**確認事項**:

```bash
# DB コンテナが起動しているか
make demo-ps | grep db

# DB ログを確認
make demo-logs S=db

# ヘルスチェック
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec db pg_isready -U myuser -d sanbou_demo
```

### 3. コンテナが起動しない

**症状**: サービスが `Exit 1` または `Restarting` 状態

**解決方法**:

```bash
# 詳細ログを確認
make demo-logs S=<サービス名>

# コンテナを再ビルド
make demo-down
docker compose -f docker/docker-compose.local_demo.yml -p local_demo build --no-cache
make demo-up
```

### 4. データが見つからない

**症状**: DB は起動するがテーブルが空

**原因**: マイグレーションが未実行、または DB クローンが必要

**解決方法**:

```bash
# 1. local_dev からデータをクローン
make demo-db-clone-from-dev

# または

# 2. マイグレーションを実行（Core API コンテナ内で）
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head
```

### 5. フロントエンドが API に接続できない

**症状**: フロントエンドは開くが API エラーが発生

**確認事項**:

```bash
# Core API が起動しているか
curl http://localhost:8013/health

# フロントエンドの環境変数を確認
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec frontend env | grep VITE

# Vite の proxy 設定を確認
# app/frontend/vite.config.ts で Core API のポート（8013）が正しく設定されているか
```

---

## ⚠️ 注意事項

### 1. データの独立性

- `local_dev` と `local_demo` のデータは完全に独立しています
- 一方の環境でデータを変更しても、もう一方には影響しません
- 意図的に同期する場合は `make demo-db-clone-from-dev` を使用してください

### 2. シークレット管理

- `.env.local_demo.secrets` は Git に含めないでください
- 本番環境では必ず異なる API キーを使用してください
- 現在は dev と同じキーを使用していますが、セキュリティ要件に応じて変更してください

### 3. リソース使用量

- 両環境を同時起動すると、CPU とメモリの使用量が倍増します
- スペックが不足する場合は、片方ずつ起動してください

### 4. Docker ボリューム

- `docker compose down -v` を実行すると、名前付きボリューム（`node_modules_demo` など）が削除されます
- データを保持したい場合は `-v` オプションを付けずに停止してください：
  ```bash
  make demo-down  # ボリュームは保持
  ```

### 5. Alembic マイグレーション

- 現在の Makefile の `al-*` ターゲットは `local_dev` 専用です
- `local_demo` でマイグレーションを実行する場合は、以下のコマンドを使用してください：

```bash
# demo 環境でマイグレーション実行
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head

# マイグレーション履歴確認
docker compose -f docker/docker-compose.local_demo.yml -p local_demo exec core_api \
  alembic -c /backend/migrations/alembic.ini history
```

---

## 🔍 動作確認チェックリスト

### 起動確認

- [ ] `make demo-up` が正常に完了する
- [ ] `make demo-ps` で全サービスが `Up` になっている
- [ ] http://localhost:5174 でフロントエンドが開く
- [ ] http://localhost:8013/docs で Core API ドキュメントが開く

### 環境独立性の確認

- [ ] `make up ENV=local_dev` と `make demo-up` を同時実行できる
- [ ] dev と demo の両方のフロントエンドに同時アクセスできる
- [ ] demo でデータを変更しても dev に影響しない

### DB 確認

- [ ] `make demo-db-shell` で DB に接続できる
- [ ] `\l` でデータベース一覧に `sanbou_demo` が表示される
- [ ] `\dt` でテーブルが表示される（マイグレーション済みの場合）

---

## 📚 関連ドキュメント

- **開発規約（バックエンド）**: `docs/conventions/backend/20251127_webapp_development_conventions_backend.md`
- **開発規約（フロントエンド）**: `docs/conventions/frontend/20251127_webapp_development_conventions_frontend.md`
- **DB 規約**: `docs/conventions/db/20251127_webapp_development_conventions_db.md`
- **Docker Compose 設定**: `docker/docker-compose.local_demo.yml`
- **環境変数設定**: `env/.env.local_demo`

---

## 🚧 今後の拡張案

### 1. Demo 専用の Alembic ターゲット

Makefile に demo 用の Alembic コマンドを追加：

```makefile
DC_DEMO = docker compose -f docker/docker-compose.local_demo.yml -p local_demo
ALEMBIC_DEMO = $(DC_DEMO) exec core_api alembic -c /backend/migrations/alembic.ini

demo-al-up:
	$(ALEMBIC_DEMO) upgrade head

demo-al-down:
	$(ALEMBIC_DEMO) downgrade -1

demo-al-current:
	$(ALEMBIC_DEMO) current

demo-al-history:
	$(ALEMBIC_DEMO) history
```

### 2. Demo データのシード

デモ用の初期データを投入するスクリプト：

```bash
demo-seed-data:
	@echo "[info] Seeding demo data..."
	$(DC_DEMO) exec -T db psql -U myuser -d sanbou_demo < scripts/seed/demo_data.sql
```

### 3. スナップショット機能

demo 環境の状態をスナップショットとして保存：

```bash
demo-snapshot:
	@echo "[info] Creating demo snapshot..."
	$(DC_DEMO) exec -T db pg_dump -U myuser -d sanbou_demo --format=custom --file=/tmp/demo_snapshot.dump
	$(DC_DEMO) cp db:/tmp/demo_snapshot.dump ./backup/demo_snapshot_$(DATE).dump
```

---

## 📝 変更履歴

| 日付       | 内容                      |
| ---------- | ------------------------- |
| 2025-11-27 | local_demo 環境の初回構築 |

---

## 💡 まとめ

`local_demo` 環境は、開発環境とは独立したデモ・検証用の環境です。以下の特徴があります：

✅ **完全独立**: コンテナ、ポート、DB、設定がすべて分離  
✅ **同時起動可能**: dev と demo を同時に実行できる  
✅ **簡単操作**: Makefile で `make demo-up` するだけ  
✅ **データクローン**: dev の DB を簡単にコピーできる

デモや新機能の検証、クライアントプレゼンテーションなど、様々な場面で活用してください！
