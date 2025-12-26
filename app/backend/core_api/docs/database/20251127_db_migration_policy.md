# DB Migration Policy & Best Practices

最終更新: 2025-11-26

## 目次

1. [概要](#概要)
2. [現状の構成](#現状の構成)
3. [基本方針](#基本方針)
4. [新規 Revision 作成ガイドライン](#新規-revision-作成ガイドライン)
5. [新規環境構築手順](#新規環境構築手順)
6. [既存環境のマイグレーション手順](#既存環境のマイグレーション手順)
7. [外部SQLファイル参照の現状と今後](#外部sqlファイル参照の現状と今後)
8. [将来のリファクタリング計画](#将来のリファクタリング計画)
9. [トラブルシューティング](#トラブルシューティング)

---

## 概要

このドキュメントは、本プロジェクトにおける Alembic を使った PostgreSQL データベースマイグレーションの運用方針を定めます。

### 主な目的

- **既存履歴の保全**: 過去の revision を壊さず、再現性を維持
- **最新版スキーマの可視化**: `sql_current/` で HEAD 時点のスキーマを明示
- **運用の標準化**: 新規 revision 作成ルールを統一し、属人化を防ぐ
- **新規環境の高速起動**: スキーマダンプから一括初期化する仕組みを提供

---

## 現状の構成

```
app/backend/core_api/migrations/
├── alembic.ini                       # Alembic 設定ファイル
├── alembic/
│   ├── env.py                        # Alembic 環境設定（DSN取得、複数スキーマ対応等）
│   ├── script.py.mako                # Revision テンプレート
│   ├── versions/                     # マイグレーション履歴（70+ revisions）
│   │   ├── 20251104_154033124_mart_baseline.py
│   │   ├── 20251104_160703155_manage_views_mart.py
│   │   └── ...
│   ├── sql/                          # 既存 revision が参照する SQL ファイル
│   │   ├── mart/
│   │   │   ├── v_receive_daily.sql
│   │   │   ├── mv_target_card_per_day.sql
│   │   │   └── ...
│   │   ├── ref/
│   │   │   ├── v_calendar_classified.sql
│   │   │   └── tables/
│   │   ├── stg/                      # （現在空）
│   │   └── kpi/
│   └── sql_current/                  # ★新設★ 最新版スキーマスナップショット
│       ├── README.md
│       └── schema_head.sql           # pg_dump --schema-only の出力
└── _snapshots/                       # （用途不明、調査中）
```

### スキーマ構成

PostgreSQL 上には以下のスキーマが存在します：

- `public`: デフォルトスキーマ（主にテーブル定義）
- `raw`: 生データ（CSV アップロード元データ）
- `stg`: ステージングデータ（クレンジング後）
- `mart`: ビジネスロジック層（VIEW / Materialized VIEW）
- `ref`: マスタ・参照データ（カレンダー、休日等）
- `kpi`: KPI 集計テーブル

---

## 基本方針

### 1. 既存 revision は**原則変更しない**

- `alembic/versions/` 配下の revision ファイル（`.py`）は、一度 commit されたら編集しない
- 理由: 履歴の再現性を保つため（他の開発者や本番環境での整合性）

### 2. 既存の `sql/` ディレクトリは**互換性維持のため残す**

- 既存 revision が `sql/mart/*.sql` などを参照している
- これらのファイルを削除・移動すると、過去の revision が実行できなくなる
- **今後は新規 revision でこれらのファイルを参照しない**

### 3. 新規 revision では**外部SQLファイルに依存せず、べた書きする**

- `op.execute()` 内に SQL を直接記述
- 理由:
  - ファイル参照の複雑さを排除
  - Revision 単体で完結し、可搬性が高まる
  - IDE による SQL 補完・検証が効きやすい

### 4. 最新版スキーマは `sql_current/schema_head.sql` で管理

- 定期的に `make al-dump-schema-current` で更新
- 新規環境構築時は `schema_head.sql` → `alembic stamp head` で初期化
- git で差分管理し、スキーマ変更履歴を追跡

---

## 新規 Revision 作成ガイドライン

### ステップ1: Revision ファイル生成

```bash
# 自動生成（推奨）
make al-rev-auto MSG="add column xxx to table yyy"

# 手動生成（複雑な変更の場合）
make al-rev MSG="refactor view: mart.v_xxx"
```

- `REV_ID` は自動生成される（`YYYYMMDD_HHMMSS%3N` 形式）
- 明示したい場合: `make al-rev MSG="..." REV_ID=20251126_120000000`

### ステップ2: Revision ファイル編集

生成された `alembic/versions/YYYYMMDD_HHMMSS_xxx.py` を編集します。

#### ✅ 推奨パターン（SQL べた書き）

```python
"""add column status to stg.receive_king

Revision ID: 20251126_120000000
Revises: previous_revision_id
"""
from alembic import op
import sqlalchemy as sa

revision = "20251126_120000000"
down_revision = "previous_revision_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """カラム追加"""
    op.execute("""
        ALTER TABLE stg.receive_king
        ADD COLUMN status VARCHAR(20) DEFAULT 'pending'
    """)

    # インデックス追加
    op.execute("""
        CREATE INDEX idx_receive_king_status
        ON stg.receive_king (status)
        WHERE status != 'archived'
    """)


def downgrade() -> None:
    """ロールバック"""
    op.execute("DROP INDEX IF EXISTS stg.idx_receive_king_status")
    op.execute("ALTER TABLE stg.receive_king DROP COLUMN IF EXISTS status")
```

#### ❌ 避けるべきパターン（外部ファイル参照）

```python
# 今後は避ける
from pathlib import Path

BASE = Path("/backend/migrations/alembic/sql/mart")

def upgrade() -> None:
    sql = (BASE / "v_new_view.sql").read_text(encoding="utf-8")
    op.execute(sql)
```

### ステップ3: マイグレーション実行

```bash
# ローカル開発環境で適用
make al-up

# 確認
make al-cur
make al-hist
```

### ステップ4: 最新スキーマを更新（重要な変更の場合）

```bash
# スキーマダンプ
make al-dump-schema-current

# 差分確認
git diff app/backend/core_api/migrations/alembic/sql_current/schema_head.sql

# コミット
git add app/backend/core_api/migrations/alembic/sql_current/schema_head.sql
git commit -m "feat(db): add status column to stg.receive_king"
```

---

## 新規環境構築手順

### パターンA: スキーマダンプから初期化（推奨・高速）

新規環境（空の DB）をすばやく HEAD 状態にする方法。

```bash
# 1. DB コンテナ起動
make up ENV=local_dev

# 2. スキーマ一括投入
make al-init-from-schema

# 3. Alembic 履歴テーブルを HEAD にスタンプ
make al-cur  # 現在の HEAD revision ID を確認
make al-stamp REV=<HEAD_REVISION_ID>

# 4. 確認
make al-cur  # HEAD が表示されれば成功
```

#### メリット

- マイグレーション履歴を全て実行するより圧倒的に速い（数秒 vs 数分）
- 本番環境からのスキーマ再現も可能

#### デメリット

- 過去の revision を順番に実行したわけではないので、途中の状態を再現できない

### パターンB: マイグレーション履歴から順次適用（完全再現）

過去の全 revision を順に実行して、履歴を忠実に再現する方法。

```bash
# 1. DB コンテナ起動
make up ENV=local_dev

# 2. 全マイグレーション実行
make al-up

# 3. 確認
make al-cur
```

#### メリット

- 各 revision の動作を検証できる
- 履歴の整合性を確認できる

#### デメリット

- 時間がかかる（revision 数に比例）
- 過去の revision が外部ファイルに依存している場合、それらも必要

---

## 既存環境のマイグレーション手順

既に稼働中の DB を最新版に更新する場合。

```bash
# 1. 現在の revision 確認
make al-cur

# 2. 適用可能な未適用 revision を確認
make al-hist

# 3. 最新版に更新
make al-up

# 4. 確認
make al-cur  # HEAD になっていることを確認
```

### 本番環境での注意事項

1. **バックアップ必須**

   ```bash
   make backup ENV=vm_prod
   ```

2. **ダウンタイムの計画**

   - 大規模なテーブル変更（カラム追加、インデックス作成等）は時間がかかる
   - `CONCURRENTLY` オプションを活用してロックを最小化

3. **ロールバック計画**

   - `downgrade()` が正しく実装されているか事前確認
   - 必要に応じて手動 SQL でのロールバック手順を準備

4. **段階的適用**
   ```bash
   # 1 revision ずつ適用
   docker compose -f docker/docker-compose.prod.yml -p vm_prod exec core_api \
     alembic -c /backend/migrations/alembic.ini upgrade +1
   ```

---

## 外部SQLファイル参照の現状と今後

### 現状（2025-11-26 時点）

以下の revision が `alembic/sql/` 配下のファイルを参照しています：

| Revision ID          | ファイル                              | 用途                   |
| -------------------- | ------------------------------------- | ---------------------- |
| `20251104_160703155` | `sql/mart/receive_daily.sql` 他       | mart.\* VIEW 定義      |
| `20251104_162109457` | `sql/mart/mv_*.sql`                   | Materialized VIEW 定義 |
| `20251104_163649629` | `sql/ref/*.sql`                       | ref.\* VIEW 定義       |
| `20251105_100819527` | `sql/mart/v_receive_*.sql`            | VIEW 更新              |
| `20251105_115452784` | `sql/mart/*.sql`（複数）              | MV 定義更新            |
| `20251113_151556000` | `sql/mart/v_receive_daily.sql`        | VIEW 更新（stg参照化） |
| `20251117_135913797` | `sql/mart/mv_target_card_per_day.sql` | MV 作成                |

### 今後の方針

- **既存の参照は維持**: 上記 revision と `sql/` ディレクトリは変更しない
- **新規 revision では参照しない**: SQL はべた書きする
- **`sql_current/` とは別物**:
  - `sql/` = 過去の revision が依存するファイル（履歴用）
  - `sql_current/` = 最新版スキーマのスナップショット（参照用・初期化用）

---

## 将来のリファクタリング計画

現状の revision 数が増えてきた場合、以下のようなリファクタリングを検討できます。

### TODO 1: Baseline Revision の作成

#### 目的

- 過去の revision をまとめて 1 つの「ベースライン」revision にスカッシュ
- 履歴を簡潔に保ち、新規環境構築を高速化

#### 手順案

1. **現在の HEAD スキーマをダンプ**

   ```bash
   make al-dump-schema-current
   ```

2. **新しいベースライン revision を作成**

   ```bash
   make al-rev MSG="baseline: squash all migrations up to 20251126"
   ```

3. **Baseline revision 内で `schema_head.sql` を読み込む**

   ```python
   def upgrade() -> None:
       if context.is_offline_mode():
           # --sql モード: スキーマダンプを出力
           with open("/backend/migrations/alembic/sql_current/schema_head.sql") as f:
               op.execute(f.read())
       else:
           # オンラインモード: 既存DBなら何もしない
           pass
   ```

4. **古い revision を `_archive/` に移動**

   ```bash
   mkdir alembic/versions/_archive_2025_11
   mv alembic/versions/202511*.py alembic/versions/_archive_2025_11/
   ```

5. **本番環境では `alembic stamp` で対応**
   ```bash
   # 本番DBは既に最新状態なので、新しいベースラインを「適用済み」としてマーク
   alembic stamp <new_baseline_revision_id>
   ```

#### 注意点

- **本番環境には影響なし**: 既存DBは `stamp` でマーク更新のみ
- **新規環境が高速化**: ベースライン revision だけで全スキーマを作成
- **履歴の透明性**: アーカイブした revision は git 履歴に残る

### TODO 2: スキーマ別 SQL ファイル分割

`sql_current/schema_head.sql` が巨大になった場合、以下のように分割を検討：

```
sql_current/
├── schema_head.sql           # 全体（後方互換性のため残す）
└── separated/
    ├── 01_schemas.sql        # CREATE SCHEMA ...
    ├── 02_tables_raw.sql
    ├── 03_tables_stg.sql
    ├── 04_tables_mart.sql
    ├── 05_views_ref.sql
    ├── 06_views_mart.sql
    ├── 07_materialized_views.sql
    ├── 08_indexes.sql
    └── 09_grants.sql
```

#### 分割スクリプト例

```bash
#!/bin/bash
# scripts/db/split_schema_current.sh
pg_dump -U myuser -d sanbou_dev --schema-only --schema=raw > sql_current/separated/02_tables_raw.sql
pg_dump -U myuser -d sanbou_dev --schema-only --schema=stg > sql_current/separated/03_tables_stg.sql
# ... 他のスキーマも同様
```

### TODO 3: CI/CD でのスキーマ検証

GitHub Actions 等で以下を自動化：

1. **スキーマダンプの差分チェック**

   - PR 作成時に `make al-dump-schema-current` を実行
   - `schema_head.sql` に差分がある場合、コミット漏れを警告

2. **マイグレーションテスト**

   - 空の DB に `alembic upgrade head` を実行
   - エラーが出ないことを確認

3. **ロールバックテスト**
   - `alembic downgrade -1` → `alembic upgrade +1` が成功することを確認

---

## トラブルシューティング

### Q1: `alembic upgrade head` が失敗する

#### 原因A: 外部SQLファイルが見つからない

```
FileNotFoundError: [Errno 2] No such file or directory: '/backend/migrations/alembic/sql/mart/v_xxx.sql'
```

**解決策**:

- `sql/` ディレクトリが Docker コンテナ内にマウントされているか確認
- ホスト側で該当ファイルが存在するか確認

#### 原因B: DB の状態が revision と不整合

```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateTable) relation "xxx" already exists
```

**解決策**:

```bash
# 現在の revision を確認
make al-cur

# DB の実際の状態を確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec db psql -U myuser -d sanbou_dev -c "\dt mart.*"

# 不整合を解消（オプション1: stamp で強制的に履歴を合わせる）
make al-stamp REV=<actual_revision_id>

# 不整合を解消（オプション2: DB を初期化してやり直す）
make down ENV=local_dev
docker volume rm local_dev_pgdata
make up ENV=local_dev
make al-up
```

### Q2: `make al-dump-schema-current` が失敗する

#### 原因: DB コンテナが起動していない

**解決策**:

```bash
make up ENV=local_dev
# 起動完了を待つ（health check）
sleep 10
make al-dump-schema-current
```

### Q3: 新規 revision が autogenerate されない

#### 原因: ORM モデル（`app/infra/db/orm_models.py`）が更新されていない

Alembic の autogenerate は、SQLAlchemy の `Base.metadata` と実際の DB を比較します。

**解決策**:

1. ORM モデルを更新
2. `make al-rev-auto MSG="..."`
3. 生成された revision を確認・調整

### Q4: Materialized View の REFRESH が遅い

#### 原因: UNIQUE INDEX がない

`REFRESH MATERIALIZED VIEW CONCURRENTLY` には UNIQUE INDEX が必須です。

**解決策**:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_xxx_pk
ON mart.mv_xxx (primary_key_column);

REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_xxx;
```

---

## まとめ

- **既存の revision と `sql/` は変更しない** → 互換性維持
- **新規 revision は SQL べた書き** → シンプル・可搬性高
- **`sql_current/schema_head.sql` で最新版を管理** → 新規環境の高速構築
- **将来的には baseline でスカッシュ** → 履歴の整理

この方針に従うことで、安全かつ効率的な DB マイグレーション運用が実現できます。

---

## 関連ドキュメント

- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/)
- [PostgreSQL pg_dump マニュアル](https://www.postgresql.org/docs/current/app-pgdump.html)
- [sql_current/ README](../app/backend/core_api/migrations/alembic/sql_current/README.md)

---

## 変更履歴

| 日付       | 変更内容 | 担当者         |
| ---------- | -------- | -------------- |
| 2025-11-26 | 初版作成 | GitHub Copilot |
