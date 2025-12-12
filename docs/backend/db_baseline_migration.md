# Alembic v2: ベースライン起点のマイグレーション管理（標準）

> **✅ ステータス**: **本番運用中** - migrations_v2 が標準マイグレーションシステムです（legacy migrations/ は削除済み）

## 📋 目次

1. [概要](#概要)
2. [背景と目的](#背景と目的)
3. [アーキテクチャ](#アーキテクチャ)
4. [ディレクトリ構成](#ディレクトリ構成)
5. [導入手順](#導入手順)
6. [運用手順](#運用手順)
7. [トラブルシューティング](#トラブルシューティング)
8. [よくある質問](#よくある質問)

---

## 概要

Alembic v2 は、既存の複雑なマイグレーション履歴を整理し、**現在のスキーマをベースライン（起点）** として新たにAlembic管理を開始する仕組みです。

**2025年12月12日以降、migrations_v2 が標準のマイグレーションシステムとなりました。** legacy migrations/ フォルダは完全に削除されています。

### 主な特徴

- ✅ **ベースライン起点**: local_dev の head 時点のスキーマを `schema_baseline.sql` として保存
- ✅ **Legacy 削除**: 既存Alembic（migrations/）は完全に削除済み
- ✅ **標準管理**: `migrations_v2/` がデフォルトのマイグレーションシステム
- ✅ **安全装置**: vm_prod の初期化操作には `FORCE=1` が必須
- ✅ **環境対応**: local_dev / vm_stg / vm_prod / local_demo すべてに対応

---

## 背景と目的

### 問題

既存の Alembic マイグレーションは以下の問題を抱えていました:

1. **依存関係の複雑化**: VIEW が後続テーブルに依存するなど、依存順序が崩れている
2. **空DBからの失敗**: `alembic upgrade head` が空DBから実行できない
3. **履歴の肥大化**: 100+ のマイグレーションファイルが存在し、管理が困難

### 解決策

1. **現在のスキーマ（正常動作中の local_dev）をベースラインとする**
2. **過去の履歴は legacy として保存し、通常運用では使わない**
3. **vm_stg / vm_prod は スナップショットSQL から構築し、v2 で前進する**

---

## アーキテクチャ

### マイグレーション管理の流れ

```
┌─────────────────────────────────────────────────────────────┐
│ 旧 Alembic (migrations/) - 削除済み                          │
│ - 100+ revision files                                        │
│ - 依存関係が複雑                                              │
│ - 空DBから upgrade head が失敗                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 完全削除 (2025-12-12)
                          ↓
                    [削除完了]

┌─────────────────────────────────────────────────────────────┐
│ Alembic v2 (migrations_v2/) - 現在の標準システム              │
│ - 0001_baseline (no-op revision)                             │
│ - 20251212_100000000_grant_comprehensive_permissions         │
│ - schema_baseline.sql (2476 lines, schema-only dump)        │
│ - 今後の変更はここに追加                                      │
│ - make al-*-env コマンドで操作                               │
└─────────────────────────────────────────────────────────────┘
```

### スキーマスナップショット

`schema_baseline.sql` の内容:

- **対象**: local_dev の head 時点（20251212_110000000）
- **生成方法**: `pg_dump --schema-only --no-owner --no-privileges`
- **含まれるもの**:
  - すべてのスキーマ（public / raw / ref / mart / stg / kpi）
  - テーブル / ビュー / マテリアライズドビュー
  - インデックス / 関数 / シーケンス
  - 構造のみ（データは含まない）

---

## ディレクトリ構成

```
app/backend/core_api/
└── migrations_v2/                 # Alembic v2（標準マイグレーションシステム）
    ├── alembic.ini               # v2用設定
    ├── alembic/
    │   ├── env.py                # v2用環境設定
    │   ├── script.py.mako        # テンプレート
    │   └── versions/
    │       ├── 0001_baseline.py  # ベースラインrevision（no-op）
    │       └── 20251212_100000000_grant_comprehensive_permissions.py
    └── sql/
        └── schema_baseline.sql   # スキーマスナップショット（2476行）
```

**注意**: 
- legacy `migrations/` フォルダは2025年12月12日に完全削除されました
- `migrations_legacy/` も存在しません
- 標準コマンド（`make al-up-env`, `make al-cur-env`）が自動的に migrations_v2 を使用します

---

## 導入手順

### 1. 新規環境構築（vm_stg / vm_prod）

#### vm_stg の場合

```bash
# 1. 環境起動
make up ENV=vm_stg

# 2. スナップショット適用
make db-apply-snapshot-v2-env ENV=vm_stg

# 3. Roles bootstrap
make db-bootstrap-roles-env ENV=vm_stg

# 4. Baseline stamp
make al-stamp-v2-env ENV=vm_stg REV=0001_baseline

# 5. 以降の変更を適用
make al-up-v2-env ENV=vm_stg

# 6. 確認
make al-cur-v2-env ENV=vm_stg
# → 0001_baseline (head) が表示されればOK
```

#### vm_prod の場合（FORCE必須）

```bash
# ⚠️ 本番環境は FORCE=1 が必須
make db-init-from-snapshot-v2-env ENV=vm_prod FORCE=1

# これで以下が自動実行される:
# 1. make down ENV=vm_prod
# 2. docker volume rm vm_prod_postgres_data
# 3. make up ENV=vm_prod
# 4. make db-apply-snapshot-v2-env ENV=vm_prod FORCE=1
# 5. make db-bootstrap-roles-env ENV=vm_prod

# 手動でstampと適用
make al-stamp-v2-env ENV=vm_prod REV=0001_baseline
make al-up-v2-env ENV=vm_prod
```

### 2. local_dev から移行

local_dev は既にデータが存在するため、スナップショット適用は不要です。

```bash
# 1. 現在のrevisionを確認
make al-cur-env ENV=local_dev
# → 20251212_110000000 (head) など

# 2. v2 baseline にstamp（データはそのまま）
make al-stamp-v2-env ENV=local_dev REV=0001_baseline

# 3. 確認
make al-cur-v2-env ENV=local_dev
# → 0001_baseline (head)

# 4. 以降は v2 で管理
make al-up-v2-env ENV=local_dev
```

---

## 運用手順

### 新しいマイグレーションの作成

```bash
# 1. local_dev で ORM モデルを変更
#    例: app/infra/db/orm_models.py にカラム追加

# 2. Alembic v2 で autogenerate
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  exec core_api alembic -c /backend/migrations_v2/alembic.ini \
  revision --autogenerate -m "Add new column to users table"

# 3. 生成されたファイルを確認・編集
# migrations_v2/alembic/versions/0002_add_new_column_to_users_table.py

# 4. local_dev で適用テスト
make al-up-v2-env ENV=local_dev

# 5. 確認
make al-cur-v2-env ENV=local_dev

# 6. コミット
git add app/backend/core_api/migrations_v2/alembic/versions/
git commit -m "Add migration: new column to users table"
```

### vm_stg へのデプロイ

```bash
# 1. vm_stg でコードを pull
cd /path/to/sanbou_app
git pull origin main

# 2. マイグレーション適用
make al-up-v2-env ENV=vm_stg

# 3. 確認
make al-cur-v2-env ENV=vm_stg
```

### vm_prod へのデプロイ

```bash
# ⚠️ 本番デプロイ前に必ずバックアップ
make backup ENV=vm_prod

# マイグレーション適用
make al-up-v2-env ENV=vm_prod

# 確認
make al-cur-v2-env ENV=vm_prod
```

---

## トラブルシューティング

### Q1. `make al-up-v2-env` で "relation does not exist" エラー

**原因**: スナップショットが適用されていない

**解決策**:
```bash
# スナップショット適用状態を確認
make ps ENV=vm_stg
docker compose -p vm_stg exec db psql -U myuser -d sanbou_dev -c "\dt mart.*"

# テーブルが存在しない場合はスナップショット再適用
make db-apply-snapshot-v2-env ENV=vm_stg
make al-stamp-v2-env ENV=vm_stg REV=0001_baseline
```

### Q2. vm_prod で誤ってスナップショット適用してしまった

**原因**: `FORCE=1` なしで実行してしまった

**解決策**:
```bash
# ❌ 実行できない（ガードされている）
make db-apply-snapshot-v2-env ENV=vm_prod

# [error] ❌ vm_prod への snapshot 適用には FORCE=1 が必須です
```

vm_prod では `FORCE=1` がないと実行できないため、誤操作は防止されています。

### Q3. Legacy Alembic を使いたい

通常は使用しませんが、参照が必要な場合:

```bash
# Legacy の現在のrevision確認
make al-cur-env-legacy ENV=local_dev

# Legacy で upgrade（非推奨）
make al-up-env-legacy ENV=local_dev
```

### Q4. schema_baseline.sql を再生成したい

```bash
# 1. local_dev が head であることを確認
make al-cur-env ENV=local_dev

# 2. スナップショット再エクスポート
./scripts/db/export_schema_baseline_local_dev.sh

# 3. 確認
wc -l app/backend/core_api/migrations_v2/sql/schema_baseline.sql

# 4. コミット
git add app/backend/core_api/migrations_v2/sql/schema_baseline.sql
git commit -m "Update schema baseline"
```

---

## よくある質問

### Q1. 既存の migrations/ はどうなるの？

**A**: そのまま残ります。local_dev は既存マイグレーションで head まで到達しているため、データも保持されます。v2 stamp 後は v2 で管理されます。

### Q2. migrations_legacy/ は削除していい？

**A**: 削除しないでください。過去の履歴として参照が必要な場合があります。legacy用コマンド（`make al-up-env-legacy`）も残してあります。

### Q3. local_dev と vm_stg で revision が異なるのは正常？

**A**: v2 導入直後は:
- **local_dev**: 既存データを保持し、v2 baseline にstamp
- **vm_stg**: スナップショットから新規構築し、v2 baseline にstamp

どちらも `0001_baseline (head)` になるため、以降は同期されます。

### Q4. MV（マテリアライズドビュー）のREFRESHは？

**A**: `schema_baseline.sql` にはMVの**定義**のみが含まれます。データ投入後に手動でREFRESHが必要です:

```bash
# 例: mart.mv_receive_daily をREFRESH
docker compose -p vm_stg exec db psql -U myuser -d sanbou_dev \
  -c "REFRESH MATERIALIZED VIEW mart.mv_receive_daily;"
```

または、データインポート後に一括REFRESH:

```bash
# すべてのMVをREFRESH
docker compose -p vm_stg exec db psql -U myuser -d sanbou_dev \
  -c "REFRESH MATERIALIZED VIEW mart.mv_receive_daily; \
      REFRESH MATERIALIZED VIEW mart.mv_target_card_per_day; \
      ..."
```

### Q5. Alembic v2 で --autogenerate が動かない

**A**: `env.py` の `target_metadata` が正しく設定されているか確認:

```python
# migrations_v2/alembic/env.py
from app.infra.db.orm_models import Base
target_metadata = Base.metadata  # ← これが必要
```

また、コンテナ内で実行する必要があります:

```bash
# コンテナ内で実行
docker compose -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini \
  revision --autogenerate -m "description"
```

---

## まとめ

Alembic v2 により:

✅ **新規環境（vm_stg/vm_prod）**: スナップショットから構築し、v2で前進  
✅ **既存環境（local_dev）**: データを保持したまま v2 に移行  
✅ **安全性**: vm_prod の初期化には `FORCE=1` が必須  
✅ **Legacy保持**: 過去の履歴は `migrations_legacy/` に退避して参照可能  

今後の運用は `migrations_v2/` で行い、`make al-up-v2-env` でマイグレーション適用してください。
