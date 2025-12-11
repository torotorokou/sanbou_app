# DB オブジェクト名定数定義案

**作成日**: 2025年12月11日  
**対象**: PostgreSQL スキーマ・テーブル・VIEW・Materialized View  
**配置先**: `backend_shared/db/names.py`  

---

## 1. オブジェクト一覧（抽出結果）

### 1.1. ref スキーマ（参照データ）

| オブジェクト種別 | schema | name | usage | 依存関係 |
|----------------|---------|------|-------|---------|
| view | ref | v_closure_days | 作成対象 | ref.closure_periods |
| view | ref | v_calendar_classified | 作成対象 | ref.calendar_day, ref.holiday_jp, ref.v_closure_days, ref.calendar_exception |
| table | ref | closure_periods | 参照のみ | - |
| table | ref | calendar_day | 参照のみ | - |
| table | ref | holiday_jp | 参照のみ | - |
| table | ref | calendar_exception | 参照のみ | - |

### 1.2. stg スキーマ（ステージング）

| オブジェクト種別 | schema | name | usage | 備考 |
|----------------|---------|------|-------|------|
| table | stg | receive_shogun_final | 参照のみ | 将軍システム確定データ（ETL投入） |
| table | stg | receive_shogun_flash | 参照のみ | 将軍システム速報データ（ETL投入） |
| table | stg | receive_king_final | 参照のみ | KINGシステムデータ（ETL投入） |

### 1.3. mart スキーマ（データマート）

| オブジェクト種別 | schema | name | usage | 依存関係 |
|----------------|---------|------|-------|---------|
| materialized_view | mart | mv_receive_daily | 作成対象 | stg.receive_shogun_final, stg.receive_shogun_flash, stg.receive_king_final, ref.v_calendar_classified |
| materialized_view | mart | mv_target_card_per_day | 作成対象 | mart.v_daily_target_with_calendar, kpi.monthly_targets, mart.mv_receive_daily |
| materialized_view | mart | mv_inb5y_week_profile_min | 作成対象 | mart.mv_receive_daily |
| materialized_view | mart | mv_inb_avg5y_day_biz | 作成対象 | mart.mv_receive_daily |
| materialized_view | mart | mv_inb_avg5y_weeksum_biz | 作成対象 | mart.mv_receive_daily |
| materialized_view | mart | mv_inb_avg5y_day_scope | 作成対象 | mart.mv_receive_daily |
| view | mart | v_receive_daily | 作成対象 | stg.receive_shogun_final, stg.receive_shogun_flash, stg.receive_king_final, ref.v_calendar_classified |
| view | mart | v_receive_weekly | 作成対象 | mart.mv_receive_daily |
| view | mart | v_receive_monthly | 作成対象 | mart.mv_receive_daily |
| view | mart | v_daily_target_with_calendar | 作成対象 | ref.v_calendar_classified, mart.daily_target_plan |
| table | mart | daily_target_plan | 参照のみ | 日次目標計画マスタ |

### 1.4. kpi スキーマ（KPI管理）

| オブジェクト種別 | schema | name | usage | 備考 |
|----------------|---------|------|-------|------|
| table | kpi | monthly_targets | 参照のみ | 月次目標マスタ |

---

## 2. backend_shared/db/names.py 定数定義案

```python
"""
PostgreSQL database object names (schema, table, view, materialized view)

This module provides constants for all database object names used in the application.
All SQL identifiers should reference these constants to:
- Prevent typos
- Enable IDE autocomplete
- Simplify refactoring (change in one place)
- Document database structure

Usage:
    from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq
    
    sql = f"REFRESH MATERIALIZED VIEW {fq(SCHEMA_MART, MV_RECEIVE_DAILY)};"
"""

# ============================================================================
# Schema Names
# ============================================================================

SCHEMA_REF = "ref"      # Reference data (calendar, holidays, closures)
SCHEMA_STG = "stg"      # Staging tables (ETL source data)
SCHEMA_MART = "mart"    # Data mart (aggregated views and materialized views)
SCHEMA_KPI = "kpi"      # KPI management tables
SCHEMA_RAW = "raw"      # Raw data from external systems
SCHEMA_LOG = "log"      # Logging tables

# ============================================================================
# ref schema - Reference Tables and Views
# ============================================================================

# Tables
T_CLOSURE_PERIODS = "closure_periods"
T_CALENDAR_DAY = "calendar_day"
T_HOLIDAY_JP = "holiday_jp"
T_CALENDAR_EXCEPTION = "calendar_exception"

# Views
V_CLOSURE_DAYS = "v_closure_days"
V_CALENDAR_CLASSIFIED = "v_calendar_classified"

# ============================================================================
# stg schema - Staging Tables (ETL source)
# ============================================================================

T_RECEIVE_SHOGUN_FINAL = "receive_shogun_final"  # 将軍システム確定データ
T_RECEIVE_SHOGUN_FLASH = "receive_shogun_flash"  # 将軍システム速報データ
T_RECEIVE_KING_FINAL = "receive_king_final"      # KINGシステムデータ

# Note: stg schema tables are managed by ETL processes
# SQL definition files may not exist for these tables

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

# Views (computed on-demand)
V_RECEIVE_DAILY = "v_receive_daily"
V_RECEIVE_WEEKLY = "v_receive_weekly"
V_RECEIVE_MONTHLY = "v_receive_monthly"
V_DAILY_TARGET_WITH_CALENDAR = "v_daily_target_with_calendar"

# Tables
T_DAILY_TARGET_PLAN = "daily_target_plan"

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
    
    Note:
        - This function is safe for SQL construction (no user input)
        - All inputs should be constants defined in this module
        - Do not use this with user-provided strings (SQL injection risk)
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
```

---

## 3. Repository からの利用イメージ

### 3.1. 変更前（ハードコード）

```python
# app/infra/adapters/materialized_view/materialized_view_refresher.py

class MaterializedViewRefresher:
    MV_MAPPINGS = {
        "receive": [
            "mart.mv_receive_daily",
            "mart.mv_target_card_per_day",
        ],
    }
    
    def _refresh_single_mv(self, mv_name: str) -> None:
        sql = f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};"
        self.db.execute(text(sql))
```

```python
# app/infra/adapters/inbound/inbound_repository.py

class InboundRepository:
    def get_daily_data(self, start_date: date, end_date: date):
        sql = """
            SELECT * FROM mart.mv_receive_daily
            WHERE ddate BETWEEN :start_date AND :end_date
        """
        return self.db.execute(text(sql), {"start_date": start_date, "end_date": end_date})
```

### 3.2. 変更後（backend_shared.db.names 使用）

```python
# app/infra/adapters/materialized_view/materialized_view_refresher.py

from backend_shared.db.names import (
    SCHEMA_MART,
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
    fq,
)

class MaterializedViewRefresher:
    MV_MAPPINGS = {
        "receive": [
            fq(SCHEMA_MART, MV_RECEIVE_DAILY),
            fq(SCHEMA_MART, MV_TARGET_CARD_PER_DAY),
        ],
    }
    
    def _refresh_single_mv(self, mv_name: str) -> None:
        # mv_name already includes schema prefix from MV_MAPPINGS
        sql = f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};"
        self.db.execute(text(sql))
```

```python
# app/infra/adapters/inbound/inbound_repository.py

from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq

class InboundRepository:
    def get_daily_data(self, start_date: date, end_date: date):
        # SQLインジェクション対策:
        # - fq()は定数のみを使用（ユーザー入力なし）
        # - 日付はバインドパラメータで渡す
        sql = f"""
            SELECT * FROM {fq(SCHEMA_MART, MV_RECEIVE_DAILY)}
            WHERE ddate BETWEEN :start_date AND :end_date
        """
        return self.db.execute(text(sql), {"start_date": start_date, "end_date": end_date})
```

### 3.3. セキュリティに関するコメント

**✅ SQL インジェクションの懸念なし**

- `fq()` および `schema_qualified()` は**定数のみ**を受け取る設計
- 全ての引数は `backend_shared.db.names` モジュールで定義された定数
- ユーザー入力は一切含まれない
- バインドパラメータ（`:start_date`, `:end_date`）は別途 SQLAlchemy が安全に処理

**⚠️ 注意事項**

```python
# ❌ 危険: ユーザー入力を直接使用
user_table = request.args.get("table")  # ユーザー入力
sql = f"SELECT * FROM {fq(SCHEMA_MART, user_table)};"  # SQL injection!

# ✅ 安全: 定数のみ使用
sql = f"SELECT * FROM {fq(SCHEMA_MART, MV_RECEIVE_DAILY)};"
```

**設計方針**:
- スキーマ名・テーブル名は**固定の定数**として管理
- 動的に変わる値（日付、ID等）は必ずバインドパラメータで渡す
- `fq()` の引数には絶対にユーザー入力を渡さない

---

## 4. 抽出困難リスト & 手動メンテ用 docs ドラフト

### 4.1. 自動抽出が困難なケース

1. **重複SQLファイル**
   - `v_receive_weekly.sql` が2つ存在（一方は `mv_receive_daily` 参照、もう一方は `v_receive_daily` 参照）
   - **要確認**: どちらが最新版か、DB実態との整合性

2. **MV vs VIEW の混在**
   - `receive_daily`, `receive_weekly`, `receive_monthly` に対して:
     - SQL定義ファイルが存在
     - 実際のDB上には VIEW or MV or TABLE のいずれかが存在
   - **要調査**: DB実態と SQL定義の対応関係

3. **外部システム管理テーブル**
   - `stg.*` テーブル（ETL で投入されるデータ）
   - `kpi.monthly_targets`（別システムで管理？）
   - SQL定義ファイルが存在しないため、スキーマ定義は別途確認が必要

4. **コメント内にしか存在しない情報**
   - `mv_target_card_per_day.sql` のコメント:
     - 参照エンドポイント: `/core_api/dashboard/target`
     - 更新頻度: "1日1回（受入データのETL完了後）"
   - Python コード側との対応関係は手動確認が必要

5. **動的生成の可能性**
   - Alembic マイグレーション内で動的に SQL を生成している可能性
   - 例: `_read_sql()` 関数でファイルを読み込んで実行

### 4.2. 手動メンテ用 docs ドラフト

```markdown
# DBオブジェクト依存関係一覧（手動メンテ用）

**最終更新**: 2025年12月11日  
**目的**: SQL自動抽出で取得できない情報を手動で補完  
**対象スキーマ**: ref, stg, mart, kpi  

---

## 1. オブジェクト依存関係マップ

### 1.1. 中核オブジェクト: mart.mv_receive_daily

- **作成対象**: `mart.mv_receive_daily` (MATERIALIZED VIEW)
- **データソース**:
  - `stg.receive_shogun_final` (将軍システム確定データ)
  - `stg.receive_shogun_flash` (将軍システム速報データ)
  - `stg.receive_king_final` (KINGシステムデータ)
  - `ref.v_calendar_classified` (営業カレンダー)
- **依存先オブジェクト**（このMVを参照するもの）:
  - `mart.v_receive_weekly` (VIEW)
  - `mart.v_receive_monthly` (VIEW)
  - `mart.mv_target_card_per_day` (MATERIALIZED VIEW)
  - `mart.mv_inb5y_week_profile_min` (MATERIALIZED VIEW)
  - `mart.mv_inb_avg5y_day_biz` (MATERIALIZED VIEW)
  - `mart.mv_inb_avg5y_weeksum_biz` (MATERIALIZED VIEW)
  - `mart.mv_inb_avg5y_day_scope` (MATERIALIZED VIEW)
- **更新頻度**: CSV upload (receive type) 完了後に自動 REFRESH
- **参照 Python コード**: 
  - `app/infra/adapters/inbound/inbound_repository.py`
  - `app/infra/adapters/materialized_view/materialized_view_refresher.py`

### 1.2. ダッシュボード用MV: mart.mv_target_card_per_day

- **作成対象**: `mart.mv_target_card_per_day` (MATERIALIZED VIEW)
- **依存元**:
  - `mart.v_daily_target_with_calendar` (VIEW)
  - `kpi.monthly_targets` (TABLE)
  - `mart.mv_receive_daily` (MATERIALIZED VIEW)
- **更新頻度**: CSV upload (receive type) 完了後に自動 REFRESH
- **参照 API エンドポイント**: `/core_api/dashboard/target`
- **参照 Python コード**: `app/infra/adapters/dashboard/dashboard_repository.py`

### 1.3. 5年平均統計MV群

| MV名 | 用途 | 依存元 | 更新頻度 |
|------|------|--------|---------|
| `mv_inb5y_week_profile_min` | 5年間週次プロファイル | `mv_receive_daily` | 手動 |
| `mv_inb_avg5y_day_biz` | 5年間平日日次平均 | `mv_receive_daily` | 手動 |
| `mv_inb_avg5y_weeksum_biz` | 5年間週次合計（営業日） | `mv_receive_daily` | 手動 |
| `mv_inb_avg5y_day_scope` | 5年間日次平均（全/営業） | `mv_receive_daily` | 手動 |

**Note**: これらのMVは現在自動更新の対象外。予測モデルで使用される可能性がある。

---

## 2. 自動抽出が難しい項目（要確認リスト）

### 2.1. 重複SQLファイル

- [ ] **v_receive_weekly.sql の重複**
  - `sql/mart/v_receive_weekly.sql` (2ファイル)
  - 一方は `mv_receive_daily` 参照、もう一方は `v_receive_daily` 参照
  - **アクション**: DB実態を確認し、不要な方を削除

- [ ] **v_receive_daily vs mv_receive_daily**
  - SQLファイルに両方存在
  - **確認事項**: 
    - どちらが実運用で使用されているか
    - Python コードではどちらを参照しているか
    - 両方が共存している理由（移行期間？）

### 2.2. 外部システム管理オブジェクト

- [ ] **stg.receive_shogun_final, stg.receive_shogun_flash**
  - ETLプロセスで投入されるテーブル
  - **確認事項**: 
    - DDL定義の管理場所
    - データ投入頻度
    - データ保持期間

- [ ] **stg.receive_king_final**
  - KINGシステムから投入されるテーブル
  - **確認事項**: 
    - KINGシステムとの連携方法
    - データフォーマット

- [ ] **kpi.monthly_targets**
  - 月次目標マスタ
  - **確認事項**: 
    - データ登録方法（管理画面？CSV import？）
    - 更新頻度

### 2.3. コメント内情報の整合性

- [ ] **mv_target_card_per_day の API エンドポイント**
  - コメント: `/core_api/dashboard/target`
  - **確認事項**: 実際のエンドポイント定義と一致しているか

- [ ] **更新頻度の記述**
  - 各MVのコメントに記載されている更新頻度
  - **確認事項**: MaterializedViewRefresher の実装と一致しているか

### 2.4. 命名規則の一貫性

- [ ] **テーブル名の接頭辞**
  - MV: `mv_*`
  - VIEW: `v_*`
  - TABLE: 接頭辞なし
  - **確認事項**: 全オブジェクトがこのルールに従っているか

---

## 3. Python コード側との対応関係（要調査）

### 3.1. Repository 層での参照

- [ ] **InboundRepository**
  - 参照オブジェクト: `mart.mv_receive_daily` or `mart.v_receive_daily`?
  - ファイルパス: `app/infra/adapters/inbound/inbound_repository.py`

- [ ] **DashboardRepository**
  - 参照オブジェクト: `mart.mv_target_card_per_day`
  - ファイルパス: `app/infra/adapters/dashboard/dashboard_repository.py`

- [ ] **SalesTreeRepository**
  - 参照オブジェクト: `mart.v_sales_tree_detail_base`
  - ファイルパス: `app/infra/adapters/sales_tree/sales_tree_repository.py`

### 3.2. Alembic マイグレーション

- [ ] **動的SQL生成の確認**
  - `_read_sql()` 関数でSQLファイルを読み込んでいるマイグレーションをリストアップ
  - backend_shared.db.names への移行可否を判断

---

## 4. 次のアクション

### 短期（今週中）

1. [ ] DB実態調査（`\dm`, `\dv`, `\dt` でスキーマ一覧取得）
2. [ ] Python コードでの参照箇所を全検索（`grep -r "mart\." app/`）
3. [ ] 重複SQLファイルの整理方針決定

### 中期（今月中）

1. [ ] `backend_shared/db/names.py` の実装
2. [ ] Repository 層での段階的移行
3. [ ] Alembic マイグレーションでの利用開始

### 長期（来月以降）

1. [ ] 全Python コードでの定数使用徹底
2. [ ] CI/CDでのハードコード検出（lint rule追加）
3. [ ] ドキュメント自動生成（SQL定義 → Markdown）

---

## 5. メンテナンス履歴

| 日付 | 変更内容 | 担当者 |
|------|---------|--------|
| 2025-12-11 | 初版作成 | GitHub Copilot |

```

---

## 5. まとめ

### 5.1. 成果物

1. **オブジェクト一覧Markdownテーブル** ✅
   - 全15SQLファイルから依存関係を抽出
   - スキーマ別に整理（ref, stg, mart, kpi）

2. **backend_shared/db/names.py 定数定義案** ✅
   - 全スキーマ・テーブル・VIEW・MVの定数定義
   - `fq()` ヘルパー関数
   - オブジェクトコレクション（AUTO_REFRESH_MVS等）

3. **Repository 利用イメージ** ✅
   - 変更前後のコード比較
   - SQLインジェクション対策の説明

4. **手動メンテ用 docs ドラフト** ✅
   - `docs/db_object_dependencies.md` の骨組み
   - 要確認リスト（重複・外部システム・コメント情報）

### 5.2. 重要な発見事項

- **中核オブジェクト**: `mart.mv_receive_daily` が7つのMV/VIEWから参照される
- **重複定義**: `v_receive_weekly.sql` が2つ存在（要整理）
- **MV vs VIEW混在**: 実DB構成との整合性確認が必要
- **外部システム依存**: stg.* テーブルはETL管理

### 5.3. 次のステップ

1. DB実態調査でSQL定義ファイルとの整合性確認
2. Python コードでの参照パターン調査
3. `backend_shared/db/names.py` 実装と段階的移行
