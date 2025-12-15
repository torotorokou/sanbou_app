# Alembic v2 マイグレーションシステム

> **✅ ステータス**: **標準システム** (2025年12月12日以降)

## 概要

これは sanbou_app の標準データベースマイグレーションシステムです。

legacy `migrations/` フォルダは2025年12月12日に完全削除され、このシステムが唯一のマイグレーション管理ツールとなりました。

## ディレクトリ構成

```
migrations_v2/
├── README.md                 # このファイル
├── alembic.ini              # Alembic設定ファイル
├── alembic/
│   ├── env.py               # Alembic環境設定
│   ├── script.py.mako       # マイグレーションテンプレート
│   └── versions/            # マイグレーションファイル
│       ├── 0001_baseline.py  # ベースライン（no-op）
│       └── 20251212_100000000_grant_comprehensive_permissions.py
└── sql/
    └── schema_baseline.sql  # スキーマスナップショット（2476行）
```

## 使い方

### 標準コマンド（推奨）

すべての標準 `make al-*-env` コマンドは自動的に migrations_v2 を使用します:

```bash
# マイグレーション適用
make al-up-env ENV=local_dev

# 現在のリビジョン確認
make al-cur-env ENV=local_dev

# マイグレーション履歴
make al-hist-env ENV=local_dev

# 1つ戻る
make al-down-env ENV=local_dev
```

### 新規マイグレーション作成（local_dev）

```bash
# 自動生成
make al-rev-auto MSG="add new column"

# 手動作成
make al-rev MSG="custom migration"
```

**作成されるファイル**: `migrations_v2/alembic/versions/YYYYMMDD_HHMMSS_<msg>.py`

### 環境別適用

```bash
# ステージング環境
make al-up-env ENV=vm_stg

# 本番環境（注意して実行）
make al-up-env ENV=vm_prod
```

## マイグレーションポリシー

1. **リビジョンID形式**: `YYYYMMDD_HHMMSSNNN` (例: 20251212_100000000)
2. **前方依存のみ**: downgrade は緊急時のみ
3. **データ移行**: マイグレーション内で完結させる
4. **テスト必須**: local_dev → vm_stg → vm_prod の順に適用

## トラブルシューティング

### `alembic_version` テーブルが見つからない

```bash
# DB Bootstrap実行
make db-bootstrap-roles-env ENV=local_dev

# ベースラインをスタンプ
make al-stamp-env ENV=local_dev REV=0001_baseline

# マイグレーション適用
make al-up-env ENV=local_dev
```

### 権限エラー

```bash
# 権限を再付与
make db-bootstrap-roles-env ENV=local_dev
```

### マイグレーション競合

```bash
# 現在の状態確認
make al-cur-env ENV=local_dev
make al-heads-env ENV=local_dev

# 必要に応じてマージ
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  exec core_api alembic -c /backend/migrations_v2/alembic.ini \
  merge -m "merge branches" <rev1> <rev2>
```

## ベースラインについて

### schema_baseline.sql

- **作成元**: local_dev の head 時点のスキーマ
- **内容**: すべてのスキーマ・テーブル・ビュー・インデックス・関数の定義
- **用途**: 新規環境（vm_stg/vm_prod）の初期化

### 0001_baseline.py

- **タイプ**: No-op migration（何もしない）
- **目的**: 既存DBに対してマイグレーション履歴の起点を設定
- **使い方**: `make al-stamp-env ENV=local_dev REV=0001_baseline`

## 関連ドキュメント

- [Makefile運用ガイド](../../../docs/infrastructure/MAKEFILE_GUIDE.md)
- [Alembic v2 移行ガイド](../../../docs/backend/db_baseline_migration.md)
- [MAKEFILE_QUICKREF.md](../../../MAKEFILE_QUICKREF.md)

## バージョン履歴

- **2025-12-12**: migrations_v2 が標準システムに昇格、legacy migrations/ 削除
- **2025-12-12**: 20251212_100000000 - 包括的権限付与マイグレーション追加
- **2025-12-11**: 0001_baseline - ベースラインマイグレーション作成
