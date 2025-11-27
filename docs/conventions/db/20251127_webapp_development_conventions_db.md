# Webアプリ開発 共通ルール（DB・マイグレーション版）
- ファイル名: 20251127_webapp_development_conventions_db.md
- 日付: 2025-11-27
- 対象: PostgreSQL / スキーマ設計 / Alembic マイグレーション / docs 命名

---

## 1. DB 設計の基本方針

- RDBMS: **PostgreSQL**
- スキーマは用途ごとに分割する
  - 例: `raw`, `stg`, `mart`, `forecast`, `kpi`, `log`, `sandbox` など
- **すべてのスキーマ変更は Alembic 経由**で行う（直接 DDL は原則禁止）

---

## 2. スキーマごとの役割

- **raw**  
  - 外部システム / CSV からの取り込みテーブル
  - 元データのカラム名を尊重し、基本的に名称変更しない
- **stg**  
  - 型変換・簡易クレンジング・コード変換などを行う中間層
  - `raw` の構造を大きく変えない
- **mart**  
  - 分析・アプリケーションで利用する最終データ
  - カラム名は canonical 名（ドメイン寄り）に揃える
  - VIEW / MATERIALIZED VIEW を積極的に活用
- **forecast / kpi / log**  
  - それぞれ用途（予測・KPI・ログ）に応じて設計
  - 命名規約は mart と同じルールを適用

---

## 3. カラム命名ルール

### 3-1. 全体ルール

- 全て **snake_case** で命名する
- `column_naming_dictionary.md` を基準とし、以下を守る
  - ID: `<concept>_id`
    - 例: `rep_id`, `customer_id`, `item_id`
  - 名称: `<concept>_name`
    - 例: `customer_name`, `item_name`
  - 日付: `<purpose>_date`
    - 例: `sales_date`, `slip_date`, `payment_date`
  - タイムスタンプ: `<event>_at`
    - 例: `created_at`, `updated_at`, `deleted_at`
  - 論理削除フラグ: `is_deleted`
  - カウント: `<target>_count`
    - 例: `slip_count`, `line_count`, `visit_count`
  - 合計値: `total_<metric>`
    - 例: `total_amount`, `total_net_weight`

### 3-2. 単位の扱い

- 可能な限りカラム名に単位（`_yen`, `_kg`）を含めない
- 既存の `amount_yen`, `qty_kg` などは段階的にリファクタリング
- 単位は:
  - COMMENT
  - `docs/conventions/column_naming_dictionary.md`
  などで明示する

### 3-3. 生データと mart の対応

- raw/stg:  
  - 外部システムのカラム名（`sales_staff_cd`, `client_cd`, `receive_no` 等）を維持
- mart:  
  - 上記を canonical 名へマッピング
  - 例:  
    - `sales_staff_cd AS rep_id`  
    - `client_cd AS customer_id`  
    - `receive_no AS slip_no`
- このマッピングは VIEW 定義や `column_naming_dictionary.md` に明記する

## 4. 論理削除・監査カラム

- 論理削除:
  - `is_deleted`（boolean）
  - `deleted_at`（timestamp）
  - `deleted_by`（text or user_id）
- 監査（重要テーブル）:
  - `created_at`, `created_by`
  - `updated_at`, `updated_by`
- 業務ロジックで利用する VIEW は `is_deleted = false` を条件に含める

---

## 5. ドキュメント（docs）の命名ルール

### 5-1. ファイル名

- 基本形式: `YYYYMMDD_タイトル.md`
  - 例: `20251127_db_naming_conventions.md`
- タイトル部分は英数字 + スネークケースまたはケバブケース
  - 例: `20251127_webapp_development_conventions_db.md`

### 5-2. 配置場所

```text
repo-root/
  docs/
    architecture/
      ...
    conventions/
      20251127_webapp_development_conventions_frontend.md
      20251127_webapp_development_conventions_backend.md
      20251127_webapp_development_conventions_db.md
      column_naming_dictionary.md
    howto/
      ...
    specs/
      ...
```

- DB 命名規約・カラム辞書は `docs/conventions/` に置く
- アプリ仕様書や画面仕様は `docs/specs/` に分離する

### 5-3. ドキュメント構成

各ドキュメントの冒頭に以下を記載する：

- タイトル
- 日付（作成日/最終更新日）
- 対象範囲（例: 「DB全般」「inbound_forecast関連テーブルのみ」）
- 必要に応じて作成者

---

## 6. Alembic（マイグレーション）のルール

### 6-1. 原則

- DB スキーマ変更は **必ず Alembic 経由**で行う
- 既存のリビジョンファイルは履歴として保存し、**過去リビジョンの内容を直接編集しない**
- 緊急で DB を直接変更した場合は、必ず後追いで Alembic リビジョンを作成する

### 6-2. Makefile 経由の運用

- 新規リビジョン作成：

```bash
make al-rev msg="add_mv_sales_tree_daily"
```

- マイグレーション適用（最新まで）：

```bash
make al-up
```

- 必要に応じて環境別ターゲットを定義（例: `make al-up-dev`, `make al-up-stg`）

### 6-3. リビジョンの書き方

- `upgrade()` / `downgrade()` を必ず定義する
- テーブル作成・カラム追加などの DDL は Alembic の `op` API を利用

```py
def upgrade():
    op.add_column(
        "inbound_forecast_daily",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
    )

def downgrade():
    op.drop_column("inbound_forecast_daily", "is_deleted")
```

- View / Materialized View は以下の方針とする：
  - SQL を別ファイル（例: `sql/views/mart_v_sales_tree_daily.sql`）に管理し、
    `op.execute(open(...).read())` で適用する
  - 変更時は新しいリビジョンで `DROP VIEW` → `CREATE VIEW` 等を記述する

### 6-4. 運用フロー

1. ローカル dev 環境でリビジョン作成 (`make al-rev`)
2. dev DB で `make al-up` を実行し、エラーがないことを確認
3. stg 環境で `make al-up` を実行し、アプリケーションの動作確認
4. 本番適用前にバックアップを取得したうえで、同じリビジョンを適用

---

## 7. 今後の方針

- カラム命名・スキーマ設計は `column_naming_dictionary.md` と本ドキュメントに従う
- 既存テーブル／ビューの命名揺れは、新リビジョンを追加して段階的に解消する
- 新規機能の DB 設計では、ここで定めたルールを必ず前提とする
