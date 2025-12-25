# Alembic マイグレーション運用ガイド

## 基本方針

### DDL 管理の原則

- **DDL は Alembic が唯一の真実**
  - すべてのスキーマ変更は Alembic リビジョンで管理
  - DBeaver は閲覧・検証専用（直接 DDL 実行は禁止）
- **ベースライン方式**
  - 現在の DB 状態を「ベースライン」として刻印（No-Op リビジョン）
  - 以降の変更は差分リビジョンで積み上げていく
- **破壊的変更は 3 段階で実施**
  1. 新カラム/テーブルを追加（NULL 許可）
  2. データをバックフィル（既存データの移行）
  3. 制約を付与（NOT NULL / UNIQUE など）

## ディレクトリ構成

```
app/backend/core_api/migrations/
├── alembic.ini              # Alembic 設定ファイル
├── alembic/
│   ├── env.py               # 環境設定（DSN/メタデータ/version_table）
│   ├── script.py.mako       # リビジョンテンプレート
│   └── versions/            # リビジョンファイル格納
│       ├── 9a092c4a1fcf_baseline_no_op.py  # ベースライン（唯一の起点）
│       └── _attic_YYYY-MM-DD/              # アーカイブ（未適用リビジョン）
└── env_legacy.py            # 旧環境設定（後方互換用・使用非推奨）
```

## version_table の場所

- **テーブル名**: `public.alembic_version`
- **カラム**: `version_num VARCHAR(32) PRIMARY KEY`
- このテーブルに現在適用されているリビジョン ID が記録される

## VS Code タスク一覧

以下のタスクは `.vscode/tasks.json` に定義されており、**ターミナル > タスクの実行** から選択できます。

| タスク名                           | 説明                                       |
| ---------------------------------- | ------------------------------------------ |
| `alembic: current`                 | 現在適用されているリビジョンを表示         |
| `alembic: history`                 | リビジョン履歴を表示                       |
| `alembic: revision (autogenerate)` | ORM との差分から新規リビジョンを自動生成   |
| `alembic: upgrade head`            | 最新リビジョンまで適用                     |
| `alembic: downgrade -1`            | 1つ前のリビジョンに戻す                    |
| `db: show alembic_version`         | DB の `alembic_version` テーブル内容を表示 |

## 初回セットアップ（ベースライン適用）

### 前提

- Docker Compose で `core_api` と `db` コンテナが起動済み
- DB: `sanbou_dev`（User: `myuser`）
- `public.alembic_version` テーブルがまだ存在しない状態

### 手順

1. **ベースラインの適用**

   - VS Code タスク: `alembic: upgrade head`
   - 実行すると `public.alembic_version` が作成され、ベースライン ID (`9a092c4a1fcf`) が刻印される

2. **適用確認**

   - VS Code タスク: `alembic: current`
   - 出力: `9a092c4a1fcf (head)` のように表示されれば成功

3. **DB 側の確認**
   - VS Code タスク: `db: show alembic_version`
   - 出力:
     ```
      version_num
     --------------
      9a092c4a1fcf
     (1 row)
     ```

## 日常運用フロー

### 1. ORM モデルを変更

- `app/repositories/orm_models.py` で `Base` を継承したモデルクラスを追加/変更

### 2. リビジョンを自動生成

- VS Code タスク: `alembic: revision (autogenerate)`
- プロンプトでメッセージを入力（例: `add user email column`）
- 生成されたリビジョンファイル（`versions/xxxx_add_user_email_column.py`）を確認・編集

### 3. リビジョンを適用

- VS Code タスク: `alembic: upgrade head`
- 実行後、`alembic: current` で適用済みリビジョンを確認

### 4. 問題があれば戻す

- VS Code タスク: `alembic: downgrade -1`
- リビジョンファイルを修正後、再度 `upgrade head`

## VIEW / 関数 / マテリアライズドビューの管理

### 方針

- これらは `CREATE OR REPLACE` で管理（Alembic の差分検出対象外）
- 手書きリビジョンで管理する

### 例: VIEW を追加するリビジョン

```python
"""add sales_summary view

Revision ID: xxxx
Revises: yyyy
Create Date: 2025-11-04 12:00:00
"""
from alembic import op

revision = 'xxxx'
down_revision = 'yyyy'

def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW ref.sales_summary AS
        SELECT
            product_id,
            SUM(quantity) as total_quantity
        FROM raw.sales
        GROUP BY product_id;
    """)

def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS ref.sales_summary;")
```

### 手順

1. VS Code タスク: `alembic: revision (autogenerate)` でベースを生成
2. 生成されたファイルを編集して `op.execute()` で SQL を記述
3. `upgrade head` で適用

## トラブルシュート

### Q1. `No config file 'alembic.ini' found`

**原因**: Alembic がコンテナ内で実行されているが、`alembic.ini` が見つからない

**対処**:

- コマンドに `-c /backend/migrations/alembic.ini` を指定（タスクで既に設定済み）
- コンテナ内のパスが正しいか確認

### Q2. `alembic_version` テーブルが存在しない

**原因**: ベースライン未適用

**対処**:

1. `alembic: upgrade head` でベースラインを適用
2. `db: show alembic_version` で確認

### Q3. `Multiple heads` エラー

**原因**: リビジョンチェーンが分岐している

**対処**:

1. `alembic: history` で確認
2. 分岐を解消するマージリビジョンを作成:
   ```bash
   docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
     alembic -c /backend/migrations/alembic.ini merge -m "merge branches" <rev1> <rev2>
   ```
3. `upgrade head` で適用

### Q4. Autogenerate が差分を検出しない

**原因**:

- メタデータが更新されていない（import 忘れ）
- `env.py` の `target_metadata` が正しく設定されていない

**対処**:

1. `app/repositories/orm_models.py` で `Base` に正しくモデルが登録されているか確認
2. `env.py` の `from app.repositories.orm_models import Base` が正しいか確認
3. コンテナを再起動（`docker compose restart core_api`）

### Q5. `psycopg` 関連エラー

**原因**: DSN の形式が間違っている

**対処**:

- `env.py` は自動的に `postgresql://` → `postgresql+psycopg://` に変換している
- 環境変数 `DB_DSN` または `DATABASE_URL` を確認
- 例: `postgresql+psycopg://myuser:password@db:5432/sanbou_dev`

## 破壊的変更の実施例

### ケース: `users` テーブルに NOT NULL 制約付きカラムを追加

#### ❌ 危険な方法（一発で実施）

```python
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255), nullable=False))
```

→ 既存レコードで失敗する（`email` が NULL のため）

#### ✅ 安全な方法（3段階）

**リビジョン 1: カラム追加（NULL 許可）**

```python
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))
```

**リビジョン 2: データをバックフィル**

```python
def upgrade():
    op.execute("""
        UPDATE users
        SET email = username || '@example.com'
        WHERE email IS NULL;
    """)
```

**リビジョン 3: NOT NULL 制約を付与**

```python
def upgrade():
    op.alter_column('users', 'email', nullable=False)
```

## 参考リンク

- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 ドキュメント](https://docs.sqlalchemy.org/en/20/)
- 本プロジェクトの `env.py`: `app/backend/core_api/migrations/alembic/env.py`
