# 外部SQL参照パターン調査結果

調査日: 2025-11-26

## 概要

`alembic/versions/` 配下の全 revision ファイルをスキャンし、外部SQLファイルを読み込んでいる箇所を特定しました。

## 調査方法

```bash
# grep で open(), read(), Path().read_text() などのパターンを検索
grep -r "open\(|Path\(.*\)\.read_text\(|\.read\(\)" alembic/versions/*.py
```

## 調査結果サマリー

- **外部SQL参照している revision 数**: 7 個
- **参照されている SQL ファイル数**: 約 15 個
- **参照先ディレクトリ**: `alembic/sql/mart/`, `alembic/sql/ref/`

## 詳細リスト

### 1. `20251104_160703155_manage_views_mart.py`

**作成日**: 2025-11-04  
**目的**: mart.* スキーマの VIEW 定義を作成

**参照ファイル** (upgrade):
- `sql/mart/receive_daily.sql`
- `sql/mart/receive_weekly.sql`
- `sql/mart/receive_monthly.sql`
- `sql/mart/v_daily_target_with_calendar.sql`
- `sql/mart/v_target_card_per_day.sql`

**参照方法**:
```python
BASE = Path("/backend/migrations/alembic/sql/mart")
def _sql(name: str) -> str: 
    return (BASE / name).read_text(encoding="utf-8")

def upgrade():
    op.execute(_sql("receive_daily.sql"))
    op.execute(_sql("receive_weekly.sql"))
    # ...
```

**downgrade**: なし（空実装）

---

### 2. `20251104_162109457_manage_materialized_views_mart.py`

**作成日**: 2025-11-04  
**目的**: mart.* スキーマの Materialized VIEW 定義を作成・リフレッシュ

**参照ファイル** (upgrade):
- `sql/mart/mv_inb5y_week_profile_min.sql`
- `sql/mart/mv_inb_avg5y_day_biz.sql`
- `sql/mart/mv_inb_avg5y_day_scope.sql`
- `sql/mart/mv_inb_avg5y_weeksum_biz.sql`

**参照方法**:
```python
BASE = Path("/backend/migrations/alembic/sql/mart")

def _read_sql(name_wo_ext: str) -> str:
    p = BASE / f"{name_wo_ext}.sql"
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def _ensure_mv(name: str, create_sql_name: str, indexes: list[str]) -> None:
    if not _exists(name):
        op.execute(_read_sql(create_sql_name))
        # ...
```

**downgrade**: MV と INDEX を DROP

---

### 3. `20251104_163649629_manage_views_ref.py`

**作成日**: 2025-11-04  
**目的**: ref.* スキーマの VIEW 定義を作成

**参照ファイル** (upgrade):
- `sql/ref/v_calendar_classified.sql`
- `sql/ref/v_closure_days.sql`

**参照方法**:
```python
BASE = Path("/backend/migrations/alembic/sql/ref")

def _read_sql(fname: str) -> str:
    return (BASE / fname).read_text(encoding="utf-8")

def upgrade():
    for fname in sorted(p.name for p in BASE.glob("*.sql")):
        op.execute(_read_sql(fname))
```

**downgrade**: なし（コメントアウトされたDROP文あり）

---

### 4. `20251105_100819527_mart_canonicalize_receive__into_v_.py`

**作成日**: 2025-11-05  
**目的**: mart.receive_* を VIEW (v_receive_*) に正規化

**参照ファイル** (upgrade):
- `sql/mart/v_receive_daily.sql`
- `sql/mart/v_receive_weekly.sql`
- `sql/mart/v_receive_monthly.sql`

**参照方法**:
```python
SQL_BASE = Path("/backend/migrations/alembic/sql/mart")

def _run(fname: str):
    op.execute((SQL_BASE / fname).read_text(encoding="utf-8"))

def upgrade():
    _run("v_receive_daily.sql")
    _run("v_receive_weekly.sql")
    _run("v_receive_monthly.sql")
```

**downgrade**: なし

---

### 5. `20251105_115452784_mart_repoint_mv_view_definitions_to_v_.py`

**作成日**: 2025-11-05  
**目的**: Materialized VIEW の定義を v_receive_* を参照するように更新

**参照ファイル** (upgrade):
- `sql/mart/v_receive_daily.sql`
- `sql/mart/v_receive_weekly.sql`
- `sql/mart/v_receive_monthly.sql`
- `sql/mart/v_target_card_per_day.sql`
- `sql/mart/mv_inb5y_week_profile_min.sql`
- `sql/mart/mv_inb_avg5y_day_biz.sql`
- `sql/mart/mv_inb_avg5y_day_scope.sql`
- `sql/mart/mv_inb_avg5y_weeksum_biz.sql`

**参照方法**:
```python
SQL_FILES = [
    "v_receive_daily.sql",
    "v_receive_weekly.sql",
    # ... (リストで列挙)
]

def upgrade():
    for fname in SQL_FILES:
        op.execute(_read(fname))
```

**downgrade**: なし

---

### 6. `20251113_151556000_update_mart_receive_daily_view.py`

**作成日**: 2025-11-13  
**目的**: mart.v_receive_daily を stg.* テーブルを参照するように更新

**参照ファイル** (upgrade):
- `sql/mart/v_receive_daily.sql`

**参照方法**:
```python
sql_file = Path(__file__).parent.parent / "sql" / "mart" / "v_receive_daily.sql"
with open(sql_file, 'r', encoding='utf-8') as f:
    sql = f.read()
op.execute(sql)
```

**downgrade**: べた書きSQL（raw.* スキーマを参照する元のVIEW定義）

---

### 7. `20251117_135913797_create_mv_target_card_per_day.py`

**作成日**: 2025-11-17  
**目的**: mart.mv_target_card_per_day (Materialized VIEW) を作成

**参照ファイル** (upgrade):
- `sql/mart/mv_target_card_per_day.sql`

**参照方法**:
```python
BASE = Path("/backend/migrations/alembic/sql/mart")

def _read_sql(name_wo_ext: str) -> str:
    p = BASE / f"{name_wo_ext}.sql"
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def _ensure_mv(name: str, create_sql_name: str, indexes: list[str]) -> None:
    if not _exists(name):
        op.execute(_read_sql(create_sql_name))
        # ...
```

**downgrade**: MV と INDEX を DROP

---

## 参照されている SQL ファイル一覧

### `alembic/sql/mart/`

| ファイル名 | 参照している revision 数 | 用途 |
|-----------|----------------------|------|
| `receive_daily.sql` | 1 | VIEW 定義（廃止予定） |
| `receive_weekly.sql` | 1 | VIEW 定義（廃止予定） |
| `receive_monthly.sql` | 1 | VIEW 定義（廃止予定） |
| `v_daily_target_with_calendar.sql` | 2 | VIEW 定義 |
| `v_target_card_per_day.sql` | 2 | VIEW 定義 |
| `v_receive_daily.sql` | 4 | VIEW 定義（最新版） |
| `v_receive_weekly.sql` | 3 | VIEW 定義（最新版） |
| `v_receive_monthly.sql` | 3 | VIEW 定義（最新版） |
| `mv_inb5y_week_profile_min.sql` | 2 | Materialized VIEW 定義 |
| `mv_inb_avg5y_day_biz.sql` | 2 | Materialized VIEW 定義 |
| `mv_inb_avg5y_day_scope.sql` | 2 | Materialized VIEW 定義 |
| `mv_inb_avg5y_weeksum_biz.sql` | 2 | Materialized VIEW 定義 |
| `mv_target_card_per_day.sql` | 1 | Materialized VIEW 定義 |

### `alembic/sql/ref/`

| ファイル名 | 参照している revision 数 | 用途 |
|-----------|----------------------|------|
| `v_calendar_classified.sql` | 1 | VIEW 定義 |
| `v_closure_days.sql` | 1 | VIEW 定義 |

### `alembic/sql/stg/`

現在は空（将来的に追加予定）

---

## 今後の方針

### 既存ファイルの扱い

✅ **変更しない（互換性維持）**

- 上記 7 個の revision が正常に動作するよう、`sql/` ディレクトリとその内容は保持
- これらのファイルを削除・移動・変更すると、過去の revision が実行できなくなる

### 新規 revision の扱い

✅ **外部ファイルに依存しない（べた書き）**

```python
# ✅ 推奨パターン
def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_new_view AS
        SELECT ...
        FROM ...
    """)

# ❌ 非推奨パターン（今後は避ける）
def upgrade() -> None:
    sql = (Path("/backend/migrations/alembic/sql/mart") / "v_new_view.sql").read_text()
    op.execute(sql)
```

### 理由

1. **シンプル**: revision ファイル単体で完結
2. **可搬性**: ファイルパス依存がない
3. **IDE サポート**: SQL 補完・検証が効く
4. **デバッグ容易**: revision 内で直接 SQL を確認・編集できる

---

## 将来のリファクタリング候補

### オプション1: Baseline Revision でスカッシュ

- 現在の HEAD スキーマを 1 つの baseline revision にまとめる
- 古い revision（上記 7 個を含む）は `versions/_archive/` に移動
- 本番環境は `alembic stamp <baseline_revision_id>` で対応
- 詳細: [db_migration_policy.md - 将来のリファクタリング計画](./db_migration_policy.md#将来のリファクタリング計画)

### オプション2: SQL ファイルをべた書きに変換

各 revision を編集して、外部ファイル参照をべた書きに置き換える。

```python
# Before
op.execute((BASE / "v_receive_daily.sql").read_text())

# After
op.execute("""
    CREATE OR REPLACE VIEW mart.v_receive_daily AS
    ... (SQL 内容をべた書き)
""")
```

**注意**: 既存 revision の編集は原則禁止（今回の方針と矛盾）  
→ オプション1（Baseline でスカッシュ）を推奨

---

## まとめ

- **現状**: 7 個の revision が 15 個の SQL ファイルを参照
- **互換性**: これらのファイルと revision は変更せず保持
- **今後**: 新規 revision は SQL をべた書きする方針
- **リファクタリング**: 将来的に Baseline でスカッシュを検討

---

## 関連ドキュメント

- [DB Migration Policy](./db_migration_policy.md)
- [sql_current/ README](../app/backend/core_api/migrations/alembic/sql_current/README.md)
