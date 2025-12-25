# DB実態調査結果

**調査日**: 2025年12月11日  
**目的**: SQL定義ファイルと実際のDB状態の整合性確認  
**対象スキーマ**: ref, stg, mart, kpi

---

## 1. DB実態一覧（全41オブジェクト）

### 1.1. kpi スキーマ（1オブジェクト）

| name            | type  | SQL定義 | 用途                       |
| --------------- | ----- | ------- | -------------------------- |
| monthly_targets | table | ❌ なし | 月次目標マスタ（外部管理） |

### 1.2. mart スキーマ（16オブジェクト）

#### Materialized Views（6個）

| name                      | type    | SQL定義 | 自動更新 | サイズ         |
| ------------------------- | ------- | ------- | -------- | -------------- |
| mv_receive_daily          | matview | ✅ あり | ✅ Yes   | 320KB, 1,805行 |
| mv_target_card_per_day    | matview | ✅ あり | ✅ Yes   | 344KB, 2,191行 |
| mv_inb5y_week_profile_min | matview | ✅ あり | ❌ No    | 32KB, 53行     |
| mv_inb_avg5y_day_biz      | matview | ✅ あり | ❌ No    | 64KB, 312行    |
| mv_inb_avg5y_weeksum_biz  | matview | ✅ あり | ❌ No    | 40KB, 53行     |
| mv_inb_avg5y_day_scope    | matview | ✅ あり | ❌ No    | 184KB, 679行   |

#### Views（7個）

| name                         | type | SQL定義 | 用途                               |
| ---------------------------- | ---- | ------- | ---------------------------------- |
| v_receive_daily              | view | ✅ あり | 日次受入ビュー（MVとほぼ同じ定義） |
| v_receive_weekly             | view | ✅ あり | 週次集計ビュー                     |
| v_receive_monthly            | view | ✅ あり | 月次集計ビュー                     |
| v_daily_target_with_calendar | view | ✅ あり | カレンダー付き日次目標             |
| v_customer_sales_daily       | view | ❌ なし | 顧客別日次売上ビュー               |
| v_sales_tree_daily           | view | ❌ なし | 販売ツリー日次ビュー               |
| v_sales_tree_detail_base     | view | ❌ なし | 販売ツリー詳細ベース               |

#### Tables（3個）

| name                    | type  | SQL定義 | 用途                                     |
| ----------------------- | ----- | ------- | ---------------------------------------- |
| daily_target_plan       | table | ❌ なし | 日次目標計画マスタ                       |
| inb_profile_smooth_test | table | ❌ なし | 受入プロファイル平滑化テスト（実験用？） |

### 1.3. ref スキーマ（11オブジェクト）

#### Views（7個）

| name                  | type | SQL定義 | 用途                 |
| --------------------- | ---- | ------- | -------------------- |
| v_calendar_classified | view | ✅ あり | 営業カレンダー分類   |
| v_closure_days        | view | ✅ あり | 締め日一覧           |
| v_customer            | view | ❌ なし | 顧客マスタビュー     |
| v_item                | view | ❌ なし | 商品マスタビュー     |
| v_sales_rep           | view | ❌ なし | 営業担当マスタビュー |

#### Tables（6個）

| name               | type  | SQL定義 | 用途               |
| ------------------ | ----- | ------- | ------------------ |
| calendar_day       | table | ❌ なし | カレンダー日マスタ |
| calendar_exception | table | ❌ なし | カレンダー例外     |
| calendar_month     | table | ❌ なし | カレンダー月マスタ |
| closure_membership | table | ❌ なし | 締めグループ所属   |
| closure_periods    | table | ❌ なし | 締め期間マスタ     |
| holiday_jp         | table | ❌ なし | 日本の祝日マスタ   |

### 1.4. stg スキーマ（13オブジェクト）

#### Views（10個）

| name                           | type | SQL定義 | 用途                       |
| ------------------------------ | ---- | ------- | -------------------------- |
| v_active_shogun_final_receive  | view | ❌ なし | 確定受入（削除済を除外）   |
| v_active_shogun_final_shipment | view | ❌ なし | 確定出荷（削除済を除外）   |
| v_active_shogun_final_yard     | view | ❌ なし | 確定ヤード（削除済を除外） |
| v_active_shogun_flash_receive  | view | ❌ なし | 速報受入（削除済を除外）   |
| v_active_shogun_flash_shipment | view | ❌ なし | 速報出荷（削除済を除外）   |
| v_active_shogun_flash_yard     | view | ❌ なし | 速報ヤード（削除済を除外） |
| v_king_receive_clean           | view | ❌ なし | KING受入データクリーニング |

#### Tables（3個）

| name                  | type  | SQL定義 | 用途                              |
| --------------------- | ----- | ------- | --------------------------------- |
| receive_king_final    | table | ❌ なし | KINGシステム受入データ（ETL投入） |
| shogun_final_receive  | table | ❌ なし | 将軍確定受入（ETL投入）           |
| shogun_final_shipment | table | ❌ なし | 将軍確定出荷（ETL投入）           |
| shogun_final_yard     | table | ❌ なし | 将軍確定ヤード（ETL投入）         |
| shogun_flash_receive  | table | ❌ なし | 将軍速報受入（ETL投入）           |
| shogun_flash_shipment | table | ❌ なし | 将軍速報出荷（ETL投入）           |
| shogun_flash_yard     | table | ❌ なし | 将軍速報ヤード（ETL投入）         |

---

## 2. 重要な発見事項

### 2.1. ❗ テーブル名の誤認識

**以前の分析での誤り**:

```python
# ❌ 誤: receive_shogun_final（実際には存在しない）
T_RECEIVE_SHOGUN_FINAL = "receive_shogun_final"
```

**正しいテーブル名**:

```python
# ✅ 正: shogun_final_receive（実際のDB名）
T_SHOGUN_FINAL_RECEIVE = "shogun_final_receive"
```

この命名は、コードベース全体で一貫して使用されている：

- `app/core/domain/csv/csv_kind.py`: `SHOGUN_FINAL_RECEIVE = "shogun_final_receive"`
- `app/config/di_providers.py`: `"receive": "shogun_final_receive"`
- Alembic migrations: `stg.shogun_final_receive`

### 2.2. SQL定義ファイルの網羅性

**SQL定義が存在するオブジェクト**（10個）:

- mart: 6 MVs + 4 VIEWs（receive_daily/weekly/monthly, daily_target_with_calendar）
- ref: 2 VIEWs（v_calendar_classified, v_closure_days）

**SQL定義が存在しないオブジェクト**（31個）:

- stg: 全13オブジェクト（ETLで管理）
- ref: 9オブジェクト（マスタテーブル + 3 VIEWs）
- mart: 9オブジェクト（3 VIEWs + 2 TABLEs）
- kpi: 1オブジェクト（月次目標テーブル）

### 2.3. MV vs VIEW の共存パターン

**receive_daily の二重定義**:

- `mart.mv_receive_daily` (MATERIALIZED VIEW): 自動更新、クエリパフォーマンス最適化
- `mart.v_receive_daily` (VIEW): リアルタイムクエリ、SQL定義ファイルあり

**現在の使い分け**:

- MaterializedViewRefresher: `mv_receive_daily` を自動更新
- Repository層での参照: 要調査（どちらを使用しているか）

### 2.4. v*active*\* VIEWs の発見

stgスキーマに6個の `v_active_*` VIEWが存在:

- 削除フラグ（`is_deleted=false`）でフィルタリング
- SQL定義ファイルなし（どこで作成されたか不明）
- コードでの参照:
  - `upload_calendar_query_adapter.py`: `v_active_shogun_final_receive`
  - `sales_tree_repository.py`: コメントで言及

**要確認**: これらのVIEWは誰が作成したのか？（Alembic migration? 手動CREATE?）

### 2.5. 未使用/実験的オブジェクト

- `mart.inb_profile_smooth_test`: 実験用テーブル（本番使用されていない可能性）

---

## 3. backend_shared/db/names.py の修正案

以下、DB実態に基づいた正確な定数定義:

```python
"""
PostgreSQL database object names (schema, table, view, materialized view)

This module provides constants for all database object names used in the application.
All SQL identifiers should reference these constants to:
- Prevent typos
- Enable IDE autocomplete
- Simplify refactoring (change in one place)
- Document database structure

⚠️ SECURITY WARNING:
Do NOT use these constants with user-provided input.
All parameters to fq() and schema_qualified() must be constants defined here.

Usage:
    from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq

    sql = f"REFRESH MATERIALIZED VIEW {fq(SCHEMA_MART, MV_RECEIVE_DAILY)};"
"""

# ============================================================================
# Schema Names
# ============================================================================

SCHEMA_REF = "ref"      # Reference data (calendar, holidays, closures, masters)
SCHEMA_STG = "stg"      # Staging tables (ETL source data)
SCHEMA_MART = "mart"    # Data mart (aggregated views and materialized views)
SCHEMA_KPI = "kpi"      # KPI management tables
SCHEMA_RAW = "raw"      # Raw data from external systems
SCHEMA_LOG = "log"      # Logging tables

# ============================================================================
# ref schema - Reference Tables and Views
# ============================================================================

# Tables (マスタテーブル - SQL定義ファイルなし)
T_CALENDAR_DAY = "calendar_day"
T_CALENDAR_MONTH = "calendar_month"
T_CALENDAR_EXCEPTION = "calendar_exception"
T_CLOSURE_PERIODS = "closure_periods"
T_CLOSURE_MEMBERSHIP = "closure_membership"
T_HOLIDAY_JP = "holiday_jp"

# Views (SQL定義ファイルあり)
V_CALENDAR_CLASSIFIED = "v_calendar_classified"
V_CLOSURE_DAYS = "v_closure_days"

# Views (SQL定義ファイルなし - 要調査)
V_CUSTOMER = "v_customer"
V_ITEM = "v_item"
V_SALES_REP = "v_sales_rep"

# ============================================================================
# stg schema - Staging Tables (ETL source)
# ============================================================================

# 将軍システム - 確定データ (final)
T_SHOGUN_FINAL_RECEIVE = "shogun_final_receive"
T_SHOGUN_FINAL_SHIPMENT = "shogun_final_shipment"
T_SHOGUN_FINAL_YARD = "shogun_final_yard"

# 将軍システム - 速報データ (flash)
T_SHOGUN_FLASH_RECEIVE = "shogun_flash_receive"
T_SHOGUN_FLASH_SHIPMENT = "shogun_flash_shipment"
T_SHOGUN_FLASH_YARD = "shogun_flash_yard"

# KINGシステム
T_RECEIVE_KING_FINAL = "receive_king_final"

# Active Views (is_deleted=false でフィルタリング)
V_ACTIVE_SHOGUN_FINAL_RECEIVE = "v_active_shogun_final_receive"
V_ACTIVE_SHOGUN_FINAL_SHIPMENT = "v_active_shogun_final_shipment"
V_ACTIVE_SHOGUN_FINAL_YARD = "v_active_shogun_final_yard"
V_ACTIVE_SHOGUN_FLASH_RECEIVE = "v_active_shogun_flash_receive"
V_ACTIVE_SHOGUN_FLASH_SHIPMENT = "v_active_shogun_flash_shipment"
V_ACTIVE_SHOGUN_FLASH_YARD = "v_active_shogun_flash_yard"

# KING Cleaning View
V_KING_RECEIVE_CLEAN = "v_king_receive_clean"

# Note: stg schema tables are managed by ETL processes
# SQL definition files do not exist for these tables

# ============================================================================
# mart schema - Data Mart (Views and Materialized Views)
# ============================================================================

# Materialized Views (auto-refreshed)
MV_RECEIVE_DAILY = "mv_receive_daily"
MV_TARGET_CARD_PER_DAY = "mv_target_card_per_day"
MV_INB5Y_WEEK_PROFILE_MIN = "mv_inb5y_week_profile_min"
MV_INB_AVG5Y_DAY_BIZ = "mv_inb_avg5y_day_biz"
MV_INB_AVG5Y_WEEKSUM_BIZ = "mv_inb_avg5y_weeksum_biz"
MV_INB_AVG5Y_DAY_SCOPE = "mv_inb_avg5y_day_scope"

# Views (computed on-demand - SQL定義ファイルあり)
V_RECEIVE_DAILY = "v_receive_daily"
V_RECEIVE_WEEKLY = "v_receive_weekly"
V_RECEIVE_MONTHLY = "v_receive_monthly"
V_DAILY_TARGET_WITH_CALENDAR = "v_daily_target_with_calendar"

# Views (SQL定義ファイルなし)
V_CUSTOMER_SALES_DAILY = "v_customer_sales_daily"
V_SALES_TREE_DAILY = "v_sales_tree_daily"
V_SALES_TREE_DETAIL_BASE = "v_sales_tree_detail_base"

# Tables
T_DAILY_TARGET_PLAN = "daily_target_plan"
T_INB_PROFILE_SMOOTH_TEST = "inb_profile_smooth_test"  # 実験用

# ============================================================================
# kpi schema - KPI Management
# ============================================================================

T_MONTHLY_TARGETS = "monthly_targets"

# ============================================================================
# Helper Functions
# ============================================================================

def fq(schema: str, name: str) -> str:
    """
    Return fully-qualified PostgreSQL identifier: "schema"."name"

    Args:
        schema: Schema name (use SCHEMA_* constants)
        name: Object name (use T_*, V_*, MV_* constants)

    Returns:
        Quoted identifier: "schema"."name"

    Example:
        >>> fq(SCHEMA_MART, MV_RECEIVE_DAILY)
        '"mart"."mv_receive_daily"'

    Security:
        - This function is safe for SQL construction ONLY with constants
        - Do NOT use with user-provided strings (SQL injection risk)
        - All inputs MUST be constants defined in this module
    """
    return f'"{schema}"."{name}"'


def schema_qualified(schema: str, name: str) -> str:
    """
    Return schema-qualified identifier without quotes: schema.name

    Use this for contexts where quotes are not needed (e.g., psycopg3 Identifier)

    Args:
        schema: Schema name (use SCHEMA_* constants)
        name: Object name (use T_*, V_*, MV_* constants)

    Returns:
        Unquoted identifier: schema.name

    Example:
        >>> schema_qualified(SCHEMA_MART, MV_RECEIVE_DAILY)
        'mart.mv_receive_daily'
    """
    return f"{schema}.{name}"


# ============================================================================
# Object Collections (for batch operations)
# ============================================================================

# All materialized views in mart schema (for refresh operations)
ALL_MART_MVS = [
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
    MV_INB5Y_WEEK_PROFILE_MIN,
    MV_INB_AVG5Y_DAY_BIZ,
    MV_INB_AVG5Y_WEEKSUM_BIZ,
    MV_INB_AVG5Y_DAY_SCOPE,
]

# Auto-refreshed MVs (configured in MaterializedViewRefresher)
AUTO_REFRESH_MVS = [
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
]

# 5-year average MVs (statistical analysis)
FIVE_YEAR_AVG_MVS = [
    MV_INB5Y_WEEK_PROFILE_MIN,
    MV_INB_AVG5Y_DAY_BIZ,
    MV_INB_AVG5Y_WEEKSUM_BIZ,
    MV_INB_AVG5Y_DAY_SCOPE,
]

# 将軍システム全テーブル (shogun tables)
SHOGUN_FINAL_TABLES = [
    T_SHOGUN_FINAL_RECEIVE,
    T_SHOGUN_FINAL_SHIPMENT,
    T_SHOGUN_FINAL_YARD,
]

SHOGUN_FLASH_TABLES = [
    T_SHOGUN_FLASH_RECEIVE,
    T_SHOGUN_FLASH_SHIPMENT,
    T_SHOGUN_FLASH_YARD,
]

# Active views (is_deleted=false filtering)
SHOGUN_ACTIVE_VIEWS = [
    V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    V_ACTIVE_SHOGUN_FINAL_SHIPMENT,
    V_ACTIVE_SHOGUN_FINAL_YARD,
    V_ACTIVE_SHOGUN_FLASH_RECEIVE,
    V_ACTIVE_SHOGUN_FLASH_SHIPMENT,
    V_ACTIVE_SHOGUN_FLASH_YARD,
]
```

---

## 4. 次のアクション

### 4.1. 即座に対応すべき項目

1. ✅ **backend_shared/db/names.py を実装** - DB実態に基づいた正確な定数
2. ⏳ **MaterializedViewRefresher を更新** - 定数使用に移行
3. ⏳ **Repository層の段階的移行** - InboundRepository → DashboardRepository

### 4.2. 調査が必要な項目

1. ❓ **v*active*\* VIEWsの作成元**
   - SQL定義ファイルなし
   - Alembic migration で作成されたか？
   - 手動で CREATE されたか？
2. ❓ **v_customer, v_item, v_sales_rep の作成元**

   - ref スキーマの VIEW
   - SQL定義ファイルなし
   - マスタテーブルのラッパーと推測

3. ❓ **v*sales_tree*\* の作成元**

   - mart スキーマの VIEW
   - コードで積極的に使用（sales_tree_repository.py）
   - SQL定義ファイルがない理由

4. ❓ **inb_profile_smooth_test の用途**
   - 実験用テーブル？
   - 削除可能か？

### 4.3. 長期的な改善

1. SQL定義ファイルの完全化（31個のオブジェクトにSQL定義を追加）
2. v*active*\* VIEWsの自動生成（Alembic migrationで管理）
3. ドキュメント自動生成（DBスキーマ → Markdown）

---

## 5. まとめ

### ✅ 確認できたこと

- **41個のDBオブジェクト**を網羅的に把握
- **テーブル名の誤認識を修正**（receive_shogun_final → shogun_final_receive）
- **SQL定義ファイルの存在状況**（10個のみ、31個は未定義）

### ⚠️ 注意が必要な点

- stgスキーマの全テーブル（7個）はETL管理でSQL定義なし
- v*active*\* VIEWs（6個）の作成元が不明
- mv_receive_daily と v_receive_daily の使い分けルールが未明確

### 🎯 次のステップ

1. backend_shared/db/names.py を実装（正確な定数定義）
2. MaterializedViewRefresher で定数使用開始
3. v*active*\* VIEWsの作成元調査（Alembic history確認）
