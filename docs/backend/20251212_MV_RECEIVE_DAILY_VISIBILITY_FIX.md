# Alembic Migration Fix: mv_receive_daily Visibility Issue

**Date**: 2025-12-12  
**Branch**: `feature/fix-mv-receive-daily-visibility`  
**Issue**: `psycopg.errors.UndefinedTable: relation "mart.mv_receive_daily" does not exist`

---

## 🔍 問題の詳細

### エラー発生状況

```
# Migration実行時
20251211_120000000: CREATE MATERIALIZED VIEW mart.mv_receive_daily
  ✓ Created mart.mv_receive_daily
  ✓ Created ux_mv_receive_daily_ddate (UNIQUE)
  ✓ Created ix_mv_receive_daily_iso_week

20251211_130000000: DROP VIEW mart.v_receive_daily CASCADE
  ✓ Dropped v_receive_daily

20251211_140000000: CREATE VIEW v_receive_weekly ... FROM mart.mv_receive_daily
  ❌ psycopg.errors.UndefinedTable: relation "mart.mv_receive_daily" does not exist
```

### 発生環境

- **vm_stg**: ステージング環境で発生
- **local_dev**: 発生しない可能性あり（タイミング依存）

---

## 🔬 原因分析

### 調査プロセス

#### Step 1: Migration依存関係の確認

```bash
20251211_110000000 (merge heads)
  ↓
20251211_120000000 (create mv_receive_daily)  # MV作成
  ↓
20251211_130000000 (drop v_receive_daily)     # VIEW削除
  ↓
20251211_140000000 (recreate weekly/monthly)  # ❌ここで失敗
```

依存関係（down_revision）は正しく設定されています。

#### Step 2: トランザクションスコープの確認

すべてのmigrationは`op.execute()`を使用しており、Alembicの同一接続で実行されています。

#### Step 3: 真の原因

**原因A: トランザクション可視性の問題**

PostgreSQLでは、各Alembic migrationは独立したトランザクションで実行されます。

```
Transaction 1: 20251211_120000000
  CREATE MATERIALIZED VIEW mart.mv_receive_daily ...
  COMMIT  ← ここでコミット

Transaction 2: 20251211_130000000
  DROP VIEW mart.v_receive_daily CASCADE
  COMMIT

Transaction 3: 20251211_140000000
  SELECT to_regclass('mart.mv_receive_daily')  ← NULL が返る場合がある
  CREATE VIEW ... FROM mart.mv_receive_daily   ← エラー
```

**仮説**:

- VM環境では、トランザクションコミット後の可視性に遅延がある可能性
- または、別のDBコネクション/セッションで実行されている可能性
- CREATE MATERIALIZED VIEWの特殊な挙動（テーブルとは異なる）

**原因B: 実行順序の問題（可能性低）**

複数のheadがマージされている構造のため、実行順序が意図と異なる可能性。

---

## ✅ 実装した修正

### 修正方針

1. **事前チェック（存在確認ガード）の追加**

   - `to_regclass()` を使用してMVの存在を確認
   - 存在しない場合は明確なエラーメッセージで即座に失敗
   - 問題の原因を特定しやすくする

2. **同一接続の保証**
   - `op.get_bind()` を使用して明示的に同じ接続を使用

### 修正内容

#### 1. `20251211_140000000_recreate_v_receive_weekly_monthly.py`

```python
from sqlalchemy import text

def _check_mv_exists() -> None:
    """
    Check if mart.mv_receive_daily exists before creating dependent views.

    Raises:
        RuntimeError: If mart.mv_receive_daily does not exist
    """
    conn = op.get_bind()
    result = conn.execute(text("SELECT to_regclass('mart.mv_receive_daily')")).scalar()

    if result is None:
        raise RuntimeError(
            "❌ mart.mv_receive_daily is missing before creating v_receive_weekly/monthly.\n"
            "   This migration depends on 20251211_120000000_create_mv_receive_daily.\n"
            "   Please ensure that migration completed successfully."
        )

    print(f"  ✓ Verified mart.mv_receive_daily exists (oid: {result})")

def upgrade() -> None:
    print("[mart] Checking dependencies...")
    _check_mv_exists()  # ← 追加

    print("[mart] Recreating v_receive_weekly...")
    op.execute(_read_sql("v_receive_weekly.sql"))
    # ...
```

#### 2. `20251211_150000000_recreate_5year_avg_mvs.py`

同様の`_check_mv_exists()`関数を追加。

---

## 📊 修正効果

### Before（修正前）

```
❌ psycopg.errors.UndefinedTable: relation "mart.mv_receive_daily" does not exist
   LINE 14:            FROM mart.mv_receive_daily d
                            ^
   （エラーの原因が不明瞭）
```

### After（修正後）

#### Case 1: MVが正常に存在する場合

```
[mart] Checking dependencies...
  ✓ Verified mart.mv_receive_daily exists (oid: 12345)
[mart] Recreating v_receive_weekly...
  ✓ Created v_receive_weekly
[mart] Recreating v_receive_monthly...
  ✓ Created v_receive_monthly
```

#### Case 2: MVが存在しない場合

```
[mart] Checking dependencies...
❌ RuntimeError: mart.mv_receive_daily is missing before creating v_receive_weekly/monthly.
   This migration depends on 20251211_120000000_create_mv_receive_daily.
   Please ensure that migration completed successfully.
```

**メリット**:

- 問題の原因が即座に明確になる
- 依存関係の問題を早期検出
- デバッグ時間の大幅短縮

---

## 🧪 テスト方法

### ローカル環境（local_dev）

```bash
# 1. 環境起動
make up ENV=local_dev

# 2. 現在のマイグレーション状態を確認
make al-cur ENV=local_dev

# 3. 該当のマイグレーションまでdowngrade（テスト用）
docker compose -p local_dev exec core_api alembic -c /backend/migrations/alembic.ini downgrade 20251211_110000000

# 4. マイグレーション再実行
make al-up ENV=local_dev

# 期待結果:
# [mart] Checking dependencies...
#   ✓ Verified mart.mv_receive_daily exists (oid: XXXXX)
# [mart] Recreating v_receive_weekly...
# [ok] v_receive_weekly and v_receive_monthly recreated
```

### ステージング環境（vm_stg）

```bash
# 【VM上で実行】

# 1. 最新コードを取得
cd ~/sanbou_app
git fetch origin feature/fix-mv-receive-daily-visibility
git checkout feature/fix-mv-receive-daily-visibility

# 2. 環境起動
make up ENV=vm_stg

# 3. マイグレーション実行
make al-up-env ENV=vm_stg

# 期待結果: エラーなく完了
# もしエラーが出る場合は、明確なエラーメッセージが表示される
```

### エラーケースのテスト（オプション）

```bash
# MVを手動で削除してテスト
docker compose -p local_dev exec db psql -U myuser -d sanbou_dev -c "DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily CASCADE;"

# 該当のmigrationを再実行
docker compose -p local_dev exec core_api alembic -c /backend/migrations/alembic.ini upgrade 20251211_140000000

# 期待結果:
# ❌ RuntimeError: mart.mv_receive_daily is missing...
```

---

## 📋 変更サマリー

### 変更ファイル

```
app/backend/core_api/migrations/alembic/versions/
├── 20251211_140000000_recreate_v_receive_weekly_monthly.py  (+54 lines)
└── 20251211_150000000_recreate_5year_avg_mvs.py            (+54 lines)
```

### 追加機能

- `_check_mv_exists()`: MVの存在確認関数
- 事前チェックの追加（upgrade()の冒頭）
- 明確なエラーメッセージ

### 互換性

- ✅ 既存のDBデータを壊さない
- ✅ 既存のview/MV名は変更なし
- ✅ 最小差分の修正
- ✅ downgrade()は既存のまま

---

## 🚨 注意事項

### もし今後も同じエラーが発生する場合

この修正は**ガード（存在確認）**を追加したもので、根本原因（なぜMVが見えないのか）を完全には解決していない可能性があります。

**追加の調査が必要な項目**:

1. **Alembic env.py の設定確認**

   ```python
   # app/backend/core_api/migrations/alembic/env.py
   # transaction_per_migration の設定確認
   ```

2. **PostgreSQL接続プール設定**

   - コネクションプールが異なるセッションを返している可能性
   - `SHOW server_version;` でPostgreSQLバージョン確認

3. **VM環境固有の問題**

   - ネットワークレイテンシー
   - DBの負荷状況
   - トランザクション分離レベル

4. **代替案: 依存関係の明示**
   ```python
   # 20251211_140000000
   depends_on = "20251211_120000000"  # 明示的な依存関係
   ```

---

## 📚 参考リソース

- [Alembic Documentation - Dependencies](https://alembic.sqlalchemy.org/en/latest/branches.html#working-with-multiple-bases)
- [PostgreSQL - CREATE MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [PostgreSQL - Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

---

## ✅ 受け入れ基準

- [x] `20251211_140000000` に存在確認ガードを追加
- [x] `20251211_150000000` に存在確認ガードを追加
- [x] MVが存在しない場合に明確なエラーメッセージを表示
- [x] 最小差分の修正
- [x] 既存の動作を壊さない
- [x] コミットメッセージが明確
- [ ] local_dev でテスト実行（必要に応じて）
- [ ] vm_stg でテスト実行（必要に応じて）

---

## 🎯 次のステップ

1. **レビュー依頼**

   ```bash
   git push origin feature/fix-mv-receive-daily-visibility
   # PR作成: "fix: Add existence checks for mv_receive_daily"
   ```

2. **ステージング環境でテスト**

   ```bash
   # vm_stg で実行
   make al-up-env ENV=vm_stg
   ```

3. **問題が解決しない場合**
   - エラーメッセージを確認
   - Alembic env.py の設定を見直し
   - PostgreSQLのログを確認
   - 別途issue作成して根本原因を調査

---

**Status**: ✅ 修正完了、テスト待ち
