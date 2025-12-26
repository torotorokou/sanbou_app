# Database Column Dictionary

データベーススキーマから抽出した全カラム名の辞書。

**生成日**: 2025-11-27  
**ソース**:

- `app/backend/core_api/migrations/alembic/sql_current/schema_head.sql`
- `app/backend/core_api/migrations/alembic/versions/*.py`

---

## Tables

### raw schema (生データ：全カラムtext型)

#### raw.shogun_flash_receive (受入速報 生データ)

- slip_date, sales_date, payment_date
- vendor_cd, vendor_name
- slip_type_cd, slip_type_name
- item_cd, item_name
- net_weight, quantity
- unit_cd, unit_name
- unit_price, amount
- receive_no
- aggregate_item_cd, aggregate_item_name
- category_cd, category_name
- weighing_time_gross, weighing_time_empty
- site_cd, site_name
- unload_vendor_cd, unload_vendor_name
- unload_site_cd, unload_site_name
- transport_vendor_cd, transport_vendor_name
- client_cd, client_name
- manifest_type_cd, manifest_type_name
- sales_staff_cd, sales_staff_name
- manifest_no
- upload_file_id, source_row_no

#### raw.shogun_final_receive (受入確定 生データ)

- slip_date, sales_date, payment_date
- vendor_cd, vendor_name
- slip_type_cd, slip_type_name
- item_cd, item_name
- net_weight, quantity
- unit_cd, unit_name
- unit_price, amount
- receive_no
- aggregate_item_cd, aggregate_item_name
- category_cd, category_name
- weighing_time_gross, weighing_time_empty
- site_cd, site_name
- unload_vendor_cd, unload_vendor_name
- unload_site_cd, unload_site_name
- transport_vendor_cd, transport_vendor_name
- client_cd, client_name
- manifest_type_cd, manifest_type_name
- sales_staff_cd, sales_staff_name
- manifest_no
- column38, column39 (未使用カラム)
- upload_file_id, source_row_no

#### raw.shogun_flash_shipment (出荷速報 生データ)

- slip_date
- client_name
- item_name
- net_weight, quantity
- unit_name
- unit_price, amount
- transport_vendor_name
- vendor_cd, vendor_name
- site_cd, site_name
- slip_type_name
- shipment_no
- detail_note
- id, created_at
- category_cd, category_name
- upload_file_id, source_row_no

#### raw.shogun_final_shipment (出荷確定 生データ)

- slip_date
- client_name
- item_name
- net_weight, quantity
- unit_name
- unit_price, amount
- transport_vendor_name
- vendor_cd, vendor_name
- site_cd, site_name
- slip_type_name
- shipment_no
- detail_note
- id, created_at
- category_cd, category_name
- upload_file_id, source_row_no

#### raw.shogun_flash_yard (ヤード速報 生データ)

- slip_date
- client_name
- item_name
- net_weight, quantity
- unit_name
- unit_price, amount
- sales_staff_name
- vendor_cd, vendor_name
- category_cd, category_name
- item_cd
- slip_no
- upload_file_id, source_row_no

#### raw.shogun_final_yard (ヤード確定 生データ)

- slip_date
- client_name
- item_name
- net_weight, quantity
- unit_name
- unit_price, amount
- sales_staff_name
- vendor_cd, vendor_name
- category_cd, category_name
- item_cd
- slip_no
- upload_file_id, source_row_no

---

### stg schema (型変換済み・クリーンデータ)

#### stg.shogun_flash_receive (受入速報)

- id (bigint, PK)
- slip_date, sales_date, payment_date (date)
- vendor_cd (integer), vendor_name (text)
- slip_type_cd (integer), slip_type_name (text)
- item_cd (integer), item_name (text)
- net_weight (numeric), quantity (numeric)
- unit_cd (integer), unit_name (text)
- unit_price (numeric), amount (numeric)
- receive_no (integer)
- aggregate_item_cd (integer), aggregate_item_name (text)
- category_cd (integer), category_name (text)
- weighing_time_gross, weighing_time_empty (time)
- site_cd (integer), site_name (text)
- unload_vendor_cd (integer), unload_vendor_name (text)
- unload_site_cd (integer), unload_site_name (text)
- transport_vendor_cd (integer), transport_vendor_name (text)
- client_cd (text), client_name (text)
- manifest_type_cd (integer), manifest_type_name (text)
- manifest_no (text)
- sales_staff_cd (integer), sales_staff_name (text)
- upload_file_id (integer), source_row_no (integer)
- is_deleted (boolean), deleted_at (timestamptz), deleted_by (text)
- created_at (timestamptz)

#### stg.shogun_final_receive (受入確定)

- 同上（shogun_flash_receiveと同じカラム構成）

#### stg.shogun_flash_shipment (出荷速報)

- id (bigint, PK)
- slip_date (date)
- client_name (text)
- item_name (text)
- net_weight (numeric), quantity (numeric)
- unit_name (text)
- unit_price (numeric), amount (numeric)
- transport_vendor_name (text)
- vendor_cd (integer), vendor_name (text)
- site_cd (integer), site_name (text)
- slip_type_name (text)
- shipment_no (text)
- detail_note (text)
- category_cd (integer), category_name (text)
- upload_file_id (integer), source_row_no (integer)
- is_deleted (boolean), deleted_at (timestamptz), deleted_by (text)
- created_at (timestamptz)

#### stg.shogun_final_shipment (出荷確定)

- 同上（shogun_flash_shipmentと同じカラム構成）

#### stg.shogun_flash_yard (ヤード速報)

- id (bigint, PK)
- slip_date (date)
- client_name (text)
- item_name (text)
- net_weight (numeric), quantity (numeric)
- unit_name (text)
- unit_price (numeric), amount (numeric)
- sales_staff_name (text)
- vendor_cd (integer), vendor_name (text)
- category_cd (integer), category_name (text)
- item_cd (integer)
- slip_no (text)
- upload_file_id (integer), source_row_no (integer)
- is_deleted (boolean), deleted_at (timestamptz), deleted_by (text)
- created_at (timestamptz)

#### stg.shogun_final_yard (ヤード確定)

- 同上（shogun_flash_yardと同じカラム構成）

#### stg.receive_king_final (KING受入データ)

- invoice_no (integer), invoice_date (varchar)
- weighing_location_code (integer), weighing_location (varchar)
- sales_purchase_type_code (integer), sales_purchase_type (varchar)
- document_type_code (integer), document_type (varchar)
- delivery_no (bigint)
- vehicle_type_code (integer), vehicle_type (varchar)
- customer_code (integer), customer (varchar)
- site_code (integer), site (varchar)
- discharge_company_code (integer), discharge_company (varchar)
- discharge_site_code (integer), discharge_site (varchar)
- carrier_code (integer), carrier (varchar)
- disposal_company_code (integer), disposal_contractor (varchar)
- disposal_site_code (integer), disposal_site (varchar)
- gross_weight, tare_weight, adjusted_weight, net_weight (integer)
- counterparty_measured_weight (integer)
- observed_quantity (real)
- weighing_time_gross, weighing_time_tare (varchar)
- weighing_location_code1 (integer), weighing_location1 (varchar)
- vehicle_no (integer), vehicle_kind (varchar)
- driver (varchar)
- sales_person_code (integer), sales_person (varchar)
- admin_person_code (integer), admin_person (varchar)
- sales_amount, sales_tax (integer)
- purchase_amount, purchase_tax (integer)
- aggregate_ton (real), aggregate_kg (integer), aggregate_m3 (real)
- remarks (varchar)
- item_category_code (integer), item_category (varchar)
- item_code (integer), item_name (varchar)
- quantity (real)
- unit_code (integer), unit (varchar)
- unit_price (real), amount (integer)
- aggregation_type_code (integer), aggregation_type (varchar)
- unit_price_calc (real), amount_calc (integer), tax_amount (integer)
- gross_weight_detail, tare_weight_detail, net_weight_detail (integer)
- scale_ratio, scale (integer)
- remarks_customer, remarks_internal (varchar)
- param\_\* (各種パラメータ: varchar)

---

### log schema (メタデータ・ログ)

#### log.upload_file (CSVアップロードファイル情報)

- id (integer, PK)
- file_name (text): 元のファイル名
- file_hash (varchar): SHA-256ハッシュ
- file_type (varchar): 'FLASH' / 'FINAL'
- csv_type (varchar): 'receive' / 'yard' / 'shipment'
- file_size_bytes (bigint)
- row_count (integer): データ行数（ヘッダー除く）
- uploaded_at (timestamptz)
- uploaded_by (varchar): アップロードユーザー
- processing_status (varchar): 'pending' / 'processing' / 'completed' / 'failed'
- error_message (text)
- metadata (jsonb)
- env (text): 'local_dev' / 'stg' / 'prod'
- is_deleted (boolean): 論理削除フラグ
- deleted_at (timestamptz)
- deleted_by (text)

---

### ref schema (マスタ・参照データ)

#### ref.calendar_day (日付マスタ)

- ddate (date, PK)
- y (integer, generated): 年
- m (integer, generated): 月
- iso_year (integer, generated): ISO年
- iso_week (integer, generated): ISO週番号
- iso_dow (integer, generated): ISO曜日 (1=月, 7=日)

#### ref.calendar_month (月マスタ)

- month_date (date, PK): 月初日

#### ref.holiday_jp (日本の祝日)

- hdate (date, PK)
- name (text): 祝日名

#### ref.calendar_exception (カレンダー例外設定)

- ddate (date, PK)
- override_type (text): 'FORCE_CLOSED' / 'FORCE_OPEN' / 'FORCE_RESERVATION'
- reason (text)
- updated_by (text)
- updated_at (timestamp)

#### ref.closure_periods (休業期間)

- start_date (date, PK)
- end_date (date)
- closure_name (text): 休業名（例: 正月休み）

#### ref.closure_membership (日付と休業期間の紐付け)

- ddate (date, PK)
- start_date (date)
- end_date (date)
- closure_name (text)

---

### kpi schema (KPI・目標管理)

#### kpi.monthly_targets (月次目標)

- month_date (date, PK): 月初日
- segment (text, PK): セグメント
- metric (text, PK): メトリック名
- value (numeric): 目標値
- unit (text): 単位
- label (text): ラベル
- updated_at (timestamptz)
- note (text)

---

### mart schema (分析用マート)

#### mart.daily_target_plan (日次目標計画)

- ddate (timestamp)
- target_ton (double precision)
- scope_used (text)
- created_at (timestamp)

#### mart.inb_profile_smooth_test (入荷プロファイル平滑化テスト)

- scope (text, PK)
- iso_week (integer, PK)
- iso_dow (integer, PK)
- day_mean_smooth (numeric)
- method (text, PK)
- params (jsonb, PK)
- updated_at (timestamptz)

---

### forecast schema (予測データ)

#### forecast.inbound_forecast_run (予測実行メタデータ)

- run_id (bigint, PK)
- factory_id (text)
- target_month (date)
- model_name (text): モデル名
- run_type (text): 実行タイプ
- run_datetime (timestamptz)
- horizon_start, horizon_end (date): 予測期間
- allocation_method (text)
- train_from, train_to (date): 訓練期間
- notes (text)

#### forecast.inbound_forecast_daily (日次予測結果)

- run_id (bigint, FK → inbound_forecast_run)
- target_date (date, PK)
- horizon_days (integer): 予測日数先
- p50_ton (numeric): P50予測値
- p10_ton, p90_ton (numeric): P10/P90予測値
- scenario (text): シナリオ名 (default: 'base')

#### forecast.inbound_forecast_weekly_raw (週次予測 生データ)

- run_id (bigint, FK)
- target_week_start (date, PK)
- p50_ton, p10_ton, p90_ton (numeric)
- scenario (text)

#### forecast.inbound_forecast_monthly_raw (月次予測 生データ)

- run_id (bigint, FK)
- target_month (date, PK)
- p50_ton, p10_ton, p90_ton (numeric)
- scenario (text)

---

## Views & Materialized Views

### stg schema

#### stg.v_active_shogun_final_receive

- **SELECT列**: stg.shogun_final_receiveの全カラム
- **条件**: `is_deleted = false`
- **説明**: 論理削除されていない受入確定データ

#### stg.v_active_shogun_flash_receive

- **SELECT列**: stg.shogun_flash_receiveの全カラム
- **条件**: `is_deleted = false`
- **説明**: 論理削除されていない受入速報データ

#### stg.v_active_shogun_final_shipment

- **SELECT列**: stg.shogun_final_shipmentの全カラム
- **条件**: `is_deleted = false`

#### stg.v_active_shogun_flash_shipment

- **SELECT列**: stg.shogun_flash_shipmentの全カラム
- **条件**: `is_deleted = false`

#### stg.v_active_shogun_final_yard

- **SELECT列**: stg.shogun_final_yardの全カラム
- **条件**: `is_deleted = false`

#### stg.v_active_shogun_flash_yard

- **SELECT列**: stg.shogun_flash_yardの全カラム
- **条件**: `is_deleted = false`

#### stg.v_king_receive_clean

- **SELECT列**:
  - invoice_d (AS: invoice_dateをdate型に変換)
  - invoice_no
  - net_weight_detail
  - amount
- **ソース**: stg.receive_king_final
- **条件**: 日付フォーマット検証済み、vehicle_type_code=1、net_weight_detail<>0
- **説明**: KING受入データのクリーンビュー（日付変換済み）

---

### ref schema (マスタビュー)

#### ref.v_closure_days

- **SELECT列**:
  - ddate (date): 休業日
  - closure_name (text): 休業名
- **ソース**: ref.closure_periods (generate_seriesで日付展開)

#### ref.v_calendar_classified

- **SELECT列**:
  - ddate, y, m, iso_year, iso_week, iso_dow
  - is_holiday (boolean): 祝日フラグ
  - is_second_sunday (boolean): 第2日曜日フラグ
  - is_company_closed (boolean): 会社休業フラグ
  - day_type (text): 'NORMAL' / 'CLOSED' / 'RESERVATION'
  - is_business (boolean): 営業日フラグ
- **ソース**: ref.calendar_day + holiday_jp + closure_periods + calendar_exception
- **説明**: カレンダー分類マスタ（祝日・休業日・営業日判定）

#### ref.v_customer (顧客マスタビュー)

- **SELECT列**:
  - customer_id (AS: client_cd)
  - customer_name (AS: max(client_name))
  - sales_rep_id (AS: max(sales_staff_cd))
  - sales_rep_name (AS: max(sales_staff_name))
- **ソース**: stg.shogun_flash_receive
- **条件**: is_deleted = false
- **グループ**: client_cd

#### ref.v_item (品目マスタビュー)

- **SELECT列**:
  - item_id (AS: item_cd)
  - item_name (AS: max(item_name))
  - unit_cd (AS: max(unit_cd))
  - unit_name (AS: max(unit_name))
  - category_cd (AS: max(category_cd))
  - category_name (AS: max(category_name))
- **ソース**: stg.shogun_flash_receive
- **条件**: is_deleted = false
- **グループ**: item_cd

#### ref.v_sales_rep (営業担当マスタビュー)

- **SELECT列**:
  - sales_rep_id (AS: sales_staff_cd)
  - sales_rep_name (AS: max(sales_staff_name))
- **ソース**: stg.shogun_flash_receive
- **条件**: is_deleted = false
- **グループ**: sales_staff_cd

---

### mart schema

#### mart.v_receive_daily (日次受入集計ビュー)

- **SELECT列**:
  - ddate, y, m, iso_year, iso_week, iso_dow
  - is_business, is_holiday, day_type
  - receive_net_ton (numeric): 受入純重量（トン）
  - receive_vehicle_count (integer): 受入台数
  - avg_weight_kg_per_vehicle (numeric): 1台あたり平均重量（kg）
  - sales_yen (numeric): 売上金額（円）
  - unit_price_yen_per_kg (numeric): kg単価（円/kg）
  - source_system (text): 'shogun_final' / 'shogun_flash' / 'king'
- **ソース**:
  - stg.v_active_shogun_final_receive
  - stg.v_active_shogun_flash_receive
  - stg.v_king_receive_clean
  - ref.v_calendar_classified
- **優先順位**: shogun_final > shogun_flash > king
- **説明**: 将軍・KING統合の日次受入集計

#### mart.v_receive_monthly (月次受入集計ビュー)

- **SELECT列**:
  - month_date (date): 月初日
  - y, m (integer): 年、月
  - biz_days (bigint): 営業日数
  - total_receive_net_ton (numeric): 月間受入純重量（トン）
  - total_receive_vehicle_count (bigint): 月間受入台数
  - avg_weight_kg_per_vehicle (numeric): 月間平均重量（kg/台）
  - total_sales_yen (numeric): 月間売上金額（円）
  - avg_unit_price_yen_per_kg (numeric): 月間平均単価（円/kg）
  - avg_daily_receive_ton (numeric): 営業日平均受入トン
- **ソース**: mart.v_receive_daily
- **グループ**: year, month

#### mart.v_receive_weekly (週次受入集計ビュー)

- **SELECT列**:
  - iso_year, iso_week (integer): ISO年、週番号
  - week_start_date, week_end_date (date): 週開始・終了日
  - biz_days (bigint): 営業日数
  - total_receive_net_ton (numeric): 週間受入純重量（トン）
  - total_receive_vehicle_count (bigint): 週間受入台数
  - avg_weight_kg_per_vehicle (numeric): 週間平均重量（kg/台）
  - total_sales_yen (numeric): 週間売上金額（円）
  - avg_unit_price_yen_per_kg (numeric): 週間平均単価（円/kg）
  - avg_daily_receive_ton (numeric): 営業日平均受入トン
- **ソース**: mart.v_receive_daily
- **グループ**: iso_year, iso_week

#### mart.v_daily_target_with_calendar (日次目標とカレンダー)

- **SELECT列**:
  - ddate, iso_year, iso_week, iso_dow
  - day_type, is_business
  - target_ton (double precision): 目標トン
  - scope_used (text)
  - created_at (timestamp)
- **ソース**: ref.v_calendar_classified LEFT JOIN mart.daily_target_plan

#### mart.mv_sales_tree_daily (売上ツリー日次 マテビュー)

- **SELECT列**:
  - sales_date (date): 売上日（sales_date ?? slip_date）
  - rep_id (AS: sales_staff_cd)
  - rep_name (AS: sales_staff_name)
  - customer_id (AS: client_cd)
  - customer_name (AS: client_name)
  - item_id (AS: item_cd)
  - item_name
  - amount_yen (AS: amount)
  - qty_kg (AS: net_weight)
  - slip_no (AS: receive_no)
  - slip_count (固定値: 1)
- **ソース**: stg.shogun_flash_receive
- **条件**: category_cd = 1 (廃棄物のみ), is_deleted = false
- **インデックス**:
  - idx_mv_sales_tree_daily_composite: (sales_date, rep_id, customer_id, item_id)
  - idx_mv_sales_tree_daily_slip: (sales_date, customer_id, slip_no)

#### mart.v_sales_tree_daily (売上ツリー日次ビュー)

- **SELECT列**: mart.mv_sales_tree_dailyの全カラム
- **説明**: マテリアライズドビューのラッパー

#### mart.v_customer_sales_daily (顧客別日次売上ビュー)

- **SELECT列**:
  - sales_date
  - customer_id
  - customer_name (AS: MAX(customer_name))
  - sales_rep_id (AS: MAX(rep_id))
  - sales_rep_name (AS: MAX(rep_name))
  - visit_count (AS: COUNT(DISTINCT slip_no)): 訪問回数
  - total_amount_yen (AS: SUM(amount_yen)): 合計売上金額
  - total_qty_kg (AS: SUM(qty_kg)): 合計数量
- **ソース**: mart.v_sales_tree_daily
- **グループ**: sales_date, customer_id

#### mart.v_sales_tree_detail_base (売上ツリー詳細ベースビュー)

- **SELECT列**:
  - sales_date (AS: COALESCE(sales_date, slip_date))
  - rep_id (AS: sales_staff_cd)
  - rep_name (AS: sales_staff_name)
  - customer_id (AS: client_cd)
  - customer_name (AS: client_name)
  - item_id (AS: item_cd)
  - item_name
  - amount_yen (AS: amount)
  - qty_kg (AS: net_weight)
  - slip_no (AS: receive_no)
  - category_cd, category_name
  - category_kind (AS: CASE WHEN category_cd=1 THEN 'waste' WHEN category_cd=3 THEN 'valuable' ELSE 'other')
  - aggregate_item_cd, aggregate_item_name
  - source_id (AS: id)
  - upload_file_id, source_row_no
- **ソース**: stg.shogun_flash_receive
- **条件**: category_cd IN (1, 3), is_deleted = false
- **説明**: 廃棄物(1)と有価物(3)の詳細データ

#### mart.mv_target_card_per_day (日次目標カード マテビュー)

- **SELECT列**:
  - ddate, iso_year, iso_week, iso_dow, is_business
  - target_ton (double precision)
  - receive_net_ton (numeric)
  - diff_ton (numeric): receive - target
  - achievement_rate (numeric): receive / target
- **ソース**: mart.v_daily_target_with_calendar LEFT JOIN mart.v_receive_daily
- **条件**: ddate >= '2024-01-01'
- **インデックス**: idx_mv_target_card_per_day_ddate (ddate DESC)

#### mart.mv_inb5y_week_profile_min (5年入荷週プロファイル)

- 省略（複雑な集計ビュー）

#### mart.mv_inb_avg5y_day_biz (5年平均日次入荷 営業日)

- 省略（複雑な集計ビュー）

#### mart.mv_inb_avg5y_day_scope (5年平均日次入荷 スコープ別)

- 省略（複雑な集計ビュー）

#### mart.mv_inb_avg5y_weeksum_biz (5年平均週間合計入荷 営業日)

- 省略（複雑な集計ビュー）

---

## Concept Clustering (概念ごとのカラム名グループ)

### Concept: 営業担当 (Sales Representative)

**Variants**:

- `sales_staff_cd` (stg.shogun*\*\_receive, raw.shogun*\*\_receive)
- `sales_staff_name` (stg.shogun*\*\_receive, raw.shogun*\*\_receive)
- `rep_id` (mart.mv*sales_tree_daily, mart.v_sales_tree*\*) ← **別名**: sales_staff_cd
- `rep_name` (mart.mv_sales_tree_daily) ← **別名**: sales_staff_name
- `sales_rep_id` (ref.v_customer, mart.v_customer_sales_daily) ← **別名**: sales_staff_cd
- `sales_rep_name` (ref.v_customer, mart.v_customer_sales_daily) ← **別名**: sales_staff_name
- `sales_person_code`, `sales_person` (stg.receive_king_final)

**Used in**:

- rawテーブル: `raw.shogun_flash_receive`, `raw.shogun_final_receive`, `raw.shogun_flash_yard`, `raw.shogun_final_yard`
- stgテーブル: `stg.shogun_flash_receive`, `stg.shogun_final_receive`, `stg.shogun_flash_yard`, `stg.shogun_final_yard`, `stg.receive_king_final`
- マートビュー: `mart.mv_sales_tree_daily`, `mart.v_sales_tree_daily`, `mart.v_customer_sales_daily`, `mart.v_sales_tree_detail_base`
- マスタビュー: `ref.v_sales_rep`, `ref.v_customer`
- API responses: sales_rep_id, sales_rep_name

**マッピング**:

```
sales_staff_cd → rep_id → sales_rep_id (コード)
sales_staff_name → rep_name → sales_rep_name (名前)
```

---

### Concept: 顧客 (Customer)

**Variants**:

- `client_cd` (stg.shogun*\*\_receive, raw.shogun*\*\_receive)
- `client_name` (stg.shogun*\*\_receive/shipment/yard, raw.shogun*\*\_receive/shipment/yard)
- `customer_id` (mart.mv*sales_tree_daily, mart.v_sales_tree*\*, ref.v_customer) ← **別名**: client_cd
- `customer_name` (mart.mv_sales_tree_daily, mart.v_customer_sales_daily, ref.v_customer) ← **別名**: client_name
- `customer_code`, `customer` (stg.receive_king_final)

**Used in**:

- rawテーブル: 全shogun系テーブル
- stgテーブル: 全shogun系テーブル、receive_king_final
- マートビュー: `mart.mv_sales_tree_daily`, `mart.v_sales_tree_*`, `mart.v_customer_sales_daily`
- マスタビュー: `ref.v_customer`
- API responses: customer_id, customer_name

**マッピング**:

```
client_cd → customer_id (コード)
client_name → customer_name (名前)
```

---

### Concept: 品目 (Item)

**Variants**:

- `item_cd` (stg.shogun*flash_receive, stg.shogun_final_receive, stg.shogun*\*\_yard)
- `item_name` (全shogun系テーブル)
- `item_id` (mart.mv_sales_tree_daily, ref.v_item) ← **別名**: item_cd
- `item_code` (stg.receive_king_final)
- `aggregate_item_cd`, `aggregate_item_name` (shogun\_\*\_receive系)

**Used in**:

- rawテーブル: 全shogun系テーブル
- stgテーブル: 全shogun系テーブル、receive_king_final
- マートビュー: `mart.mv_sales_tree_daily`, `mart.v_sales_tree_*`
- マスタビュー: `ref.v_item`

**マッピング**:

```
item_cd → item_id (コード)
item_name (名前)
aggregate_item_cd, aggregate_item_name (集計品目)
```

---

### Concept: 伝票番号 (Slip/Receipt Number)

**Variants**:

- `receive_no` (stg.shogun*\*\_receive, raw.shogun*\*\_receive)
- `slip_no` (mart.mv*sales_tree_daily, stg.shogun*\*\_yard) ← **別名**: receive_no
- `shipment_no` (stg.shogun\_\*\_shipment)
- `invoice_no` (stg.receive_king_final)
- `manifest_no` (stg.shogun\_\*\_receive)

**Used in**:

- 受入系: receive_no → slip_no
- 出荷系: shipment_no
- ヤード系: slip_no
- KING系: invoice_no

**マッピング**:

```
receive_no → slip_no (受入)
shipment_no (出荷)
slip_no (ヤード)
invoice_no (KING)
```

---

### Concept: 日付 (Date)

**Variants**:

- `slip_date` (全shogun系テーブル): 伝票日付
- `sales_date` (shogun\_\*\_receive): 売上日付
- `payment_date` (shogun\_\*\_receive): 支払日付
- `invoice_date`, `invoice_d` (stg.receive_king_final, stg.v_king_receive_clean): 請求日
- `ddate` (ref.calendar_day, mart.v_receive_daily): 日付
- `month_date` (kpi.monthly_targets, ref.calendar_month): 月初日
- `target_date` (forecast.inbound_forecast_daily): 予測対象日
- `uploaded_at` (log.upload_file): アップロード日時
- `deleted_at` (stg.shogun\_\*, log.upload_file): 削除日時
- `created_at` (stg.shogun\_\*, log.upload_file): 作成日時

**マッピング**:

```
slip_date: 伝票日（物理的な日付）
sales_date: 売上日（会計上の日付）
COALESCE(sales_date, slip_date) → sales_date (martビューで統一)
```

---

### Concept: 重量 (Weight)

**Variants**:

- `net_weight` (全shogun系テーブル): 正味重量（kg）
- `qty_kg` (mart.mv_sales_tree_daily) ← **別名**: net_weight
- `net_weight_detail` (stg.receive_king_final, stg.v_king_receive_clean): KING正味重量詳細
- `gross_weight` (stg.receive_king_final): 総重量
- `tare_weight` (stg.receive_king_final): 風袋重量
- `adjusted_weight` (stg.receive_king_final): 調整重量
- `receive_net_ton` (mart.v_receive_daily): 受入純重量（トン）
- `total_qty_kg` (mart.v_customer_sales_daily): 合計数量（kg）

**Used in**:

- 元データ: net_weight (kg単位)
- マート: receive_net_ton (トン単位), qty_kg (kg単位)

**マッピング**:

```
net_weight → qty_kg (キログラム)
net_weight / 1000 → receive_net_ton (トン)
```

---

### Concept: 金額 (Amount)

**Variants**:

- `amount` (全shogun系テーブル): 金額
- `amount_yen` (mart.mv_sales_tree_daily) ← **別名**: amount
- `sales_yen` (mart.v_receive_daily): 売上金額
- `total_amount_yen` (mart.v_customer_sales_daily): 合計売上金額
- `unit_price` (shogun系テーブル): 単価
- `unit_price_yen_per_kg` (mart.v_receive_daily): kg単価（円/kg）

**マッピング**:

```
amount → amount_yen → sales_yen (金額)
unit_price → unit_price_yen_per_kg (単価)
```

---

### Concept: カテゴリ (Category)

**Variants**:

- `category_cd` (全shogun系テーブル): カテゴリコード
- `category_name` (全shogun系テーブル): カテゴリ名
- `category_kind` (mart.v_sales_tree_detail_base): カテゴリ種別（'waste' / 'valuable' / 'other'）
- `item_category_code`, `item_category` (stg.receive_king_final)

**マッピング**:

```
category_cd = 1 → category_kind = 'waste' (廃棄物)
category_cd = 3 → category_kind = 'valuable' (有価物)
その他 → category_kind = 'other'
```

---

### Concept: ベンダー/業者 (Vendor)

**Variants**:

- `vendor_cd`, `vendor_name` (shogun*\*\_receive, shogun*_*shipment, shogun*_\_yard)
- `unload_vendor_cd`, `unload_vendor_name` (shogun\_\*\_receive): 荷卸し業者
- `transport_vendor_cd`, `transport_vendor_name` (shogun\_\*\_receive): 運搬業者
- `discharge_company_code`, `discharge_company` (stg.receive_king_final): 排出業者
- `disposal_company_code`, `disposal_contractor` (stg.receive_king_final): 処分業者
- `carrier_code`, `carrier` (stg.receive_king_final): 運搬業者

**Used in**:

- 受入: vendor (仕入先), unload_vendor (荷卸し), transport_vendor (運搬)
- 出荷: vendor (出荷先), transport_vendor_name (運搬)
- ヤード: vendor (仕入先)

---

### Concept: サイト/場所 (Site/Location)

**Variants**:

- `site_cd`, `site_name` (shogun系テーブル)
- `unload_site_cd`, `unload_site_name` (shogun\_\*\_receive)
- `weighing_location_code`, `weighing_location` (stg.receive_king_final)
- `disposal_site_code`, `disposal_site` (stg.receive_king_final)

---

### Concept: 単位 (Unit)

**Variants**:

- `unit_cd`, `unit_name` (shogun\_\*\_receive)
- `unit_name` (shogun*\*\_shipment, shogun*\*\_yard)
- `unit_code`, `unit` (stg.receive_king_final)
- `quantity` (全shogun系テーブル): 数量

---

### Concept: 論理削除 (Soft Delete)

**Variants**:

- `is_deleted` (stg.shogun\_\*, log.upload_file): 削除フラグ（true=削除済み）
- `deleted_at` (stg.shogun\_\*, log.upload_file): 削除日時
- `deleted_by` (stg.shogun\_\*, log.upload_file): 削除実行者

**Used in**:

- 全stg.shogun\_\*テーブル
- log.upload_file
- ビュー: stg.v*active*\* (is_deleted = false でフィルタ)

---

### Concept: アップロード追跡 (Upload Tracking)

**Variants**:

- `upload_file_id` (全raw/stgテーブル): FK → log.upload_file.id
- `source_row_no` (全raw/stgテーブル): CSVの元行番号
- `file_name`, `file_hash`, `file_type`, `csv_type` (log.upload_file)
- `processing_status` (log.upload_file): 'pending' / 'processing' / 'completed' / 'failed'

**マッピング**:

```
log.upload_file.id ← upload_file_id (FK)
元CSVの行番号 → source_row_no
```

---

### Concept: カレンダー分類 (Calendar Classification)

**Variants**:

- `is_business` (ref.v_calendar_classified, mart.v_receive_daily): 営業日フラグ
- `is_holiday` (ref.v_calendar_classified, mart.v_receive_daily): 祝日フラグ
- `day_type` (ref.v_calendar_classified, mart.v_receive_daily): 'NORMAL' / 'CLOSED' / 'RESERVATION'
- `is_second_sunday` (ref.v_calendar_classified): 第2日曜日フラグ
- `is_company_closed` (ref.v_calendar_classified): 会社休業フラグ
- `iso_year`, `iso_week`, `iso_dow` (ref.calendar_day, 各種ビュー): ISO年・週・曜日

---

### Concept: 目標・実績 (Target & Achievement)

**Variants**:

- `target_ton` (mart.daily_target_plan, mart.mv_target_card_per_day): 目標トン数
- `receive_net_ton` (mart.v_receive_daily, mart.mv_target_card_per_day): 受入純重量（トン）
- `diff_ton` (mart.mv_target_card_per_day): 差異（実績 - 目標）
- `achievement_rate` (mart.mv_target_card_per_day): 達成率（実績 / 目標）

---

### Concept: 集計単位 (Aggregation Level)

**Variants**:

- 日次: `ddate`, `sales_date`, `slip_date`
- 週次: `iso_year`, `iso_week`, `week_start_date`, `week_end_date`
- 月次: `y`, `m`, `month_date`
- 年次: `y`, `iso_year`

---

## Summary

### スキーマ構成

- **raw**: 生データ（全カラムtext型）
- **stg**: 型変換済みクリーンデータ
- **mart**: 分析用マート（集計ビュー・マテビュー）
- **ref**: マスタ・参照データ
- **log**: メタデータ・ログ
- **kpi**: KPI・目標管理
- **forecast**: 予測データ

### 命名規則パターン

1. **コード・名前ペア**: `xxx_cd` + `xxx_name` (例: item_cd, item_name)
2. **マート別名**:
   - `sales_staff_cd` → `rep_id`
   - `client_cd` → `customer_id`
   - `item_cd` → `item_id`
   - `receive_no` → `slip_no`
   - `amount` → `amount_yen`
   - `net_weight` → `qty_kg`
3. **日付系**: `*_date`, `*_at`, `ddate`
4. **論理削除**: `is_deleted`, `deleted_at`, `deleted_by`
5. **アップロード追跡**: `upload_file_id`, `source_row_no`
6. **カレンダー**: `is_*` (boolean), `day_type` (enum)

### 主要な変換ルール

```sql
-- 営業担当
sales_staff_cd → rep_id (mart層)
sales_staff_name → rep_name (mart層)

-- 顧客
client_cd → customer_id (mart層)
client_name → customer_name (mart層)

-- 品目
item_cd → item_id (mart層)

-- 伝票番号
receive_no → slip_no (mart層)

-- 日付統一
COALESCE(sales_date, slip_date) AS sales_date (mart層)

-- 重量単位変換
net_weight (kg) → receive_net_ton (ton) = net_weight / 1000

-- 金額
amount → amount_yen (mart層)

-- カテゴリ種別
category_cd = 1 → 'waste' (廃棄物)
category_cd = 3 → 'valuable' (有価物)
```

---

**End of Dictionary**
