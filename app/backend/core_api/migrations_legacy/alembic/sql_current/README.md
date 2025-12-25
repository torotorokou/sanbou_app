# sql_current - 最新版スキーマスナップショット

## 目的

このディレクトリは、Alembic マイグレーション履歴の「最新版（HEAD）」時点における
PostgreSQL スキーマ定義を保持します。

## 従来の `sql/` ディレクトリとの違い

| ディレクトリ   | 用途                                  | 更新頻度                     |
| -------------- | ------------------------------------- | ---------------------------- |
| `sql/`         | 既存 revision が参照する**履歴用SQL** | 原則更新しない（互換性維持） |
| `sql_current/` | **最新版スキーマのスナップショット**  | HEAD更新時に再生成           |

## ファイル構成

```
sql_current/
├── README.md                    # このファイル
├── schema_head.sql              # 全スキーマ一括ダンプ（pg_dump --schema-only の出力）
└── separated/                   # （将来的に）スキーマ別・オブジェクト種別に分割したSQLファイル
    ├── tables/
    ├── views/
    ├── materialized_views/
    └── indexes/
```

### `schema_head.sql`

- `pg_dump --schema-only` で生成した全スキーマ定義
- 新規環境構築時に `psql < schema_head.sql` で一括投入可能
- git で差分管理されるため、スキーマ変更の履歴追跡が容易

### `separated/` （将来的）

- 巨大な `schema_head.sql` を読みやすくするため、種別ごとに分割したバージョン
- 現時点では未実装（必要に応じて追加）

## 更新手順

### 自動更新（推奨）

```bash
# Makefile タスクを使用
make al-dump-schema-current
```

### 手動更新

```bash
# Docker コンテナ経由で pg_dump を実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  pg_dump -U myuser -d sanbou_dev --schema-only \
  > app/backend/core_api/migrations/alembic/sql_current/schema_head.sql
```

## 使用タイミング

1. **新規環境構築時**

   - `schema_head.sql` を投入してスキーマ作成
   - `alembic stamp head` で履歴を最新化

2. **重要な revision 追加後**

   - テーブル・ビュー・MV の定義変更を行った revision を適用した直後
   - CI/CD でのスキーマ整合性チェック用

3. **定期的なスナップショット**
   - 週次/月次でスキーマ変更を記録したい場合
   - git タグと合わせて管理することで、リリースバージョンとスキーマの対応付けが可能

## 注意事項

- **このディレクトリ内のSQLファイルは Alembic revision から参照しません**
- 既存の `sql/` ディレクトリ内のファイルは今後も revision から参照され続けます
- 新規 revision では、外部SQLファイルに依存せず、revision 内にべた書きする方針です

## 関連ドキュメント

- [DB Migration Policy](../../../../docs/db_migration_policy.md)
- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/)
