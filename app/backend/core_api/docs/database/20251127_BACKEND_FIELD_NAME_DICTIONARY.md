# Backend API Field Name Dictionary

バックエンドAPIのフィールド名辞書（Pydantic Schema / Domain Model / SQL Column）

## 目的

- Presentation層（Pydantic）、Domain層、Infra層（SQL）の各レイヤーで使われるフィールド名を一覧化
- フィールド名の揺れ（naming inconsistency）を明示し、統一化の参考資料とする
- フロントエンドとの連携時に、どのフィールドがどのDB列に対応するかを明確化

---

## 1. Pydantic Response Schemas

### ForecastJobResponse (予測ジョブ)

- id: int
- job_type: str
- target_from: date
- target_to: date
- status: str
- attempts: int
- scheduled_for: Optional[datetime]
- actor: Optional[str]
- payload_json: Optional[dict]
- error_message: Optional[str]
- created_at: datetime
- updated_at: datetime

### PredictionDTO (予測結果)

- date: date
- y_hat: float
- y_lo: Optional[float]
- y_hi: Optional[float]
- model_version: Optional[str]
- generated_at: Optional[datetime]

### KPIOverview (KPIダッシュボード)

- total_jobs: int
- completed_jobs: int
- failed_jobs: int
- latest_prediction_date: Optional[date]
- last_updated: datetime

### LostCustomerDTO (離脱顧客)

- customer_id: str
- customer_name: str
- sales_rep_id: Optional[str]
- sales_rep_name: Optional[str]
- last_visit_date: date
- prev_visit_days: int
- prev_total_amount_yen: float
- prev_total_qty_kg: float

### SalesRepDTO (営業担当)

- sales_rep_id: str
- sales_rep_name: str

### TargetMetricsResponse (ダッシュボードターゲット)

- ddate: Optional[date]
- month_target_ton: Optional[float]
- week_target_ton: Optional[float]
- day_target_ton: Optional[float]
- month_actual_ton: Optional[float]
- week_actual_ton: Optional[float]
- day_actual_ton_prev: Optional[float]
- iso_year: Optional[int]
- iso_week: Optional[int]
- iso_dow: Optional[int]
- day_type: Optional[str]
- is_business: Optional[bool]
- month_target_to_date_ton: Optional[float]
- month_target_total_ton: Optional[float]
- week_target_to_date_ton: Optional[float]
- week_target_total_ton: Optional[float]
- month_actual_to_date_ton: Optional[float]
- week_actual_to_date_ton: Optional[float]

### InboundDailyRow (日次搬入量)

- ddate: date
- iso_year: int
- iso_week: int
- iso_dow: int
- is_business: bool
- segment: Optional[str]
- ton: float
- cum_ton: Optional[float]
- prev_month_ton: Optional[float]
- prev_year_ton: Optional[float]
- prev_month_cum_ton: Optional[float]
- prev_year_cum_ton: Optional[float]

### MetricEntry (売上メトリクス)

- id: str
- name: str
- amount: float
- qty: float
- line_count: int
- slip_count: int
- count: int
- unit_price: Optional[float]
- date_key: Optional[str]

### SummaryRow (営業別サマリ)

- rep_id: int (serialization_alias: repId)
- rep_name: str (serialization_alias: repName)
- metrics: list[MetricEntry] (serialization_alias: topN)

### DailyPoint (日次推移)

- date: date
- amount: float
- qty: float
- line_count: int
- slip_count: int
- count: int
- unit_price: Optional[float]

### DetailLine (詳細明細行)

- mode: DetailMode
- sales_date: date (serialization_alias: salesDate)
- slip_no: int (serialization_alias: slipNo)
- rep_name: str (serialization_alias: repName)
- customer_name: str (serialization_alias: customerName)
- item_id: Optional[int] (serialization_alias: itemId)
- item_name: str (serialization_alias: itemName)
- line_count: Optional[int] (serialization_alias: lineCount)
- qty_kg: float (serialization_alias: qtyKg)
- unit_price_yen_per_kg: Optional[float] (serialization_alias: unitPriceYenPerKg)
- amount_yen: float (serialization_alias: amountYen)

---

## 2. Domain Models (Entities / Value Objects)

### LostCustomer (顧客離脱エンティティ)

- customer_id: str
- customer_name: str
- sales_rep_id: Optional[str]
- sales_rep_name: Optional[str]
- last_visit_date: date
- prev_visit_days: int
- prev_total_amount_yen: float
- prev_total_qty_kg: float

### SummaryRequest (売上ツリーサマリリクエスト)

- date_from: date
- date_to: date
- mode: AxisMode
- category_kind: CategoryKind
- rep_ids: list[int]
- filter_ids: list[str]
- top_n: int
- sort_by: SortKey
- order: SortOrder

### DailySeriesRequest (日次推移リクエスト)

- date_from: date
- date_to: date
- category_kind: CategoryKind
- rep_id: Optional[int]
- customer_id: Optional[str]
- item_id: Optional[int]

### PivotRequest (ピボットリクエスト)

- date_from: date
- date_to: date
- base_axis: AxisMode
- base_id: str
- category_kind: CategoryKind
- rep_ids: list[int]
- target_axis: AxisMode
- top_n: int
- sort_by: SortKey
- order: SortOrder
- cursor: Optional[str]

### DetailLinesRequest (詳細明細リクエスト)

- date_from: date
- date_to: date
- last_group_by: GroupBy
- category_kind: CategoryKind
- rep_id: Optional[int]
- customer_id: Optional[str]
- item_id: Optional[int]
- date_value: Optional[date]

---

## 3. SQL Column Names (Repository層)

### mart.v_sales_tree_detail_base

**SELECT時に使用される列:**

- sales_date: 売上日
- rep_id: 営業ID (integer)
- rep_name: 営業名
- customer_id: 顧客ID (text)
- customer_name: 顧客名
- item_id: 品目ID (integer)
- item_name: 品目名
- amount_yen: 金額（円）
- qty_kg: 数量（kg）
- slip_no: 伝票番号（receive_no）
- category_cd: カテゴリコード（'W'=waste, 'V'=valuable）

**集計時に計算される列:**

- line_count: COUNT(\*) - 明細行数
- slip_count: COUNT(DISTINCT slip_no) - 伝票数（台数）
- unit_price: amount_yen / qty_kg - 単価

### mart.v_customer_sales_daily

**SELECT時に使用される列:**

- customer_id: 顧客ID
- customer_name: 顧客名
- sales_date: 売上日
- sales_rep_id: 営業担当ID
- sales_rep_name: 営業担当名
- total_amount_yen: 日次売上金額
- total_qty_kg: 日次売上重量

**集計時に計算される列:**

- prev_visit_days: COUNT(\*) - 前期間訪問日数
- prev_total_amount_yen: SUM(total_amount_yen) - 前期間合計金額
- prev_total_qty_kg: SUM(total_qty_kg) - 前期間合計重量
- last_visit_date: MAX(sales_date) - 最終訪問日

### mart.mv_target_card_per_day (Materialized View)

**SELECT時に使用される列:**

- ddate: 日付
- month_target_ton: 月目標トン数
- week_target_ton: 週目標トン数
- day_target_ton: 日目標トン数
- month_actual_ton: 月実績トン数
- week_actual_ton: 週実績トン数
- day_actual_ton_prev: 前日実績トン数
- iso_year: ISO年
- iso_week: ISO週番号
- iso_dow: ISO曜日（1=月, 7=日）
- day_type: 日付種別（weekday/sat/sun_hol）
- is_business: 営業日フラグ
- month_target_to_date_ton: 月累計目標（月初～昨日）
- month_target_total_ton: 月全体目標
- week_target_to_date_ton: 週累計目標（週初～昨日）
- week_target_total_ton: 週全体目標
- month_actual_to_date_ton: 月累計実績（月初～昨日）
- week_actual_to_date_ton: 週累計実績（週初～昨日）

### mart.v_receive_daily

**SELECT時に使用される列:**

- ddate: 日付
- receive_net_ton: 日次搬入量（トン）

**LEFT JOIN + 0埋め処理:**

- mart.v_calendar と LEFT JOIN して連続日を保証
- NULLの場合は0として扱う

### mart.v_calendar

**SELECT時に使用される列:**

- ddate: 日付
- y: 年
- m: 月
- d: 日
- iso_year: ISO年
- iso_week: ISO週番号
- iso_dow: ISO曜日
- day_type: 日付種別
- is_business: 営業日フラグ

---

## 4. Concept Mapping (概念ごとの名称の揺れ)

### 営業担当

**Pydantic:**

- rep_id: int (SummaryRow, MetricEntry)
- rep_name: str (SummaryRow, DetailLine)
- sales_rep_id: Optional[str] (LostCustomerDTO, SalesRepDTO)
- sales_rep_name: Optional[str] (LostCustomerDTO, SalesRepDTO)

**Domain:**

- rep_id: Optional[int] (DailySeriesRequest)
- rep_ids: list[int] (SummaryRequest, PivotRequest)
- sales_rep_id: Optional[str] (LostCustomer)
- sales_rep_name: Optional[str] (LostCustomer)

**SQL:**

- rep_id: integer (mart.v_sales_tree_detail_base)
- sales_rep_id: text (mart.v_customer_sales_daily)
- sales_rep_name: text (mart.v_customer_sales_daily)

**揺れの種類:**

- `rep_id` vs `sales_rep_id`（名前）
- `int` vs `str`（型）

---

### 顧客

**Pydantic:**

- customer_id: str (LostCustomerDTO, DetailLine)
- customer_name: str (LostCustomerDTO, DetailLine)

**Domain:**

- customer_id: Optional[str] (DailySeriesRequest, DetailLinesRequest)

**SQL:**

- customer_id: text (mart.v_sales_tree_detail_base, mart.v_customer_sales_daily)
- customer_name: text (mart.v_sales_tree_detail_base, mart.v_customer_sales_daily)

**揺れ:**

- なし（統一されている）

---

### 品目

**Pydantic:**

- item_id: Optional[int] (DetailLine)
- item_name: str (DetailLine)

**Domain:**

- item_id: Optional[int] (DailySeriesRequest, DetailLinesRequest)

**SQL:**

- item_id: integer (mart.v_sales_tree_detail_base)
- item_name: text (mart.v_sales_tree_detail_base)

**揺れ:**

- なし（統一されている）

---

### 金額

**Pydantic:**

- amount: float (MetricEntry, DailyPoint)
- amount_yen: float (DetailLine)
- prev_total_amount_yen: float (LostCustomerDTO)
- total_amount_yen: float (implicit in CustomerChurnQueryAdapter)

**Domain:**

- N/A（フィールド名なし）

**SQL:**

- amount_yen: numeric (mart.v_sales_tree_detail_base)
- total_amount_yen: numeric (mart.v_customer_sales_daily)

**揺れの種類:**

- `amount` vs `amount_yen` vs `total_amount_yen` vs `prev_total_amount_yen`（接頭辞・接尾辞）

---

### 重量

**Pydantic:**

- qty: float (MetricEntry, DailyPoint)
- qty_kg: float (DetailLine)
- prev_total_qty_kg: float (LostCustomerDTO)
- ton: float (InboundDailyRow)
- month_target_ton: Optional[float] (TargetMetricsResponse)
- week_target_ton: Optional[float] (TargetMetricsResponse)

**Domain:**

- N/A（フィールド名なし）

**SQL:**

- qty_kg: numeric (mart.v_sales_tree_detail_base)
- total_qty_kg: numeric (mart.v_customer_sales_daily)
- receive_net_ton: numeric (mart.v_receive_daily)
- month_target_ton: numeric (mart.mv_target_card_per_day)

**揺れの種類:**

- `qty` vs `qty_kg` vs `total_qty_kg` vs `prev_total_qty_kg`（単位接尾辞）
- `ton` vs `kg`（単位の違い）

---

### 伝票番号

**Pydantic:**

- slip_no: int (DetailLine)

**Domain:**

- N/A

**SQL:**

- slip_no: integer (mart.v_sales_tree_detail_base, receive_no の別名)

**揺れ:**

- なし（統一されている）

---

### 日付

**Pydantic:**

- date: date (PredictionDTO, DailyPoint)
- ddate: Optional[date] (TargetMetricsResponse, InboundDailyRow)
- sales_date: date (DetailLine)
- last_visit_date: date (LostCustomerDTO)
- target_from: date (ForecastJobCreate)
- target_to: date (ForecastJobCreate)
- date_from: date (SummaryRequest)
- date_to: date (SummaryRequest)

**Domain:**

- date_from: date (SummaryRequest, DailySeriesRequest, PivotRequest, DetailLinesRequest)
- date_to: date (SummaryRequest, DailySeriesRequest, PivotRequest, DetailLinesRequest)
- date_value: Optional[date] (DetailLinesRequest)

**SQL:**

- ddate: date (mart.v_calendar, mart.mv_target_card_per_day)
- sales_date: date (mart.v_sales_tree_detail_base, mart.v_customer_sales_daily)

**揺れの種類:**

- `date` vs `ddate` vs `sales_date` vs `last_visit_date`（接頭辞）
- `date_from` / `date_to` vs `target_from` / `target_to`（期間表現）

---

### カウント

**Pydantic:**

- count: int (MetricEntry, DailyPoint) - 表示用カウント値
- line_count: int (MetricEntry, DailyPoint, DetailLine) - 明細行数
- slip_count: int (MetricEntry, DailyPoint) - 伝票数（台数）
- prev_visit_days: int (LostCustomerDTO) - 前期間訪問日数

**Domain:**

- N/A

**SQL:**

- COUNT(\*) AS line_count
- COUNT(DISTINCT slip_no) AS slip_count

**揺れの種類:**

- `count` vs `line_count` vs `slip_count`（粒度の違い）
- ビジネスルール: 商品軸=line_count、それ以外=slip_count

---

### 単価

**Pydantic:**

- unit_price: Optional[float] (MetricEntry, DailyPoint)
- unit_price_yen_per_kg: Optional[float] (DetailLine)

**Domain:**

- N/A

**SQL:**

- CASE WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg) ELSE NULL END AS unit_price

**揺れの種類:**

- `unit_price` vs `unit_price_yen_per_kg`（単位明示）

---

### カテゴリ

**Pydantic:**

- category_kind: CategoryKind = Literal["waste", "valuable"]

**Domain:**

- category_kind: CategoryKind = Literal["waste", "valuable"] (SummaryRequest, etc.)

**SQL:**

- category_cd: text = 'W' | 'V'

**揺れの種類:**

- `category_kind` (waste/valuable) vs `category_cd` (W/V)（人間可読 vs DB略称）

---

### ISO週情報

**Pydantic:**

- iso_year: int (TargetMetricsResponse, InboundDailyRow)
- iso_week: int (TargetMetricsResponse, InboundDailyRow)
- iso_dow: int (TargetMetricsResponse, InboundDailyRow)

**Domain:**

- N/A

**SQL:**

- iso_year: integer (mart.v_calendar, mart.mv_target_card_per_day)
- iso_week: integer (mart.v_calendar, mart.mv_target_card_per_day)
- iso_dow: integer (mart.v_calendar, mart.mv_target_card_per_day)

**揺れ:**

- なし（統一されている）

---

### 営業日フラグ

**Pydantic:**

- is_business: bool (TargetMetricsResponse, InboundDailyRow)

**Domain:**

- N/A

**SQL:**

- is_business: boolean (mart.v_calendar, mart.mv_target_card_per_day)

**揺れ:**

- なし（統一されている）

---

## 5. 命名規則の推奨方針

### 統一化の提案

1. **営業担当ID:**

   - 推奨: `rep_id: int`（一貫性のため）
   - 既存: `sales_rep_id: str`（互換性維持が必要な場合のみ）

2. **金額:**

   - 推奨: `amount_yen: float`（単位を明示）
   - 既存: `amount: float`（軽量表現）

3. **重量:**

   - 推奨: `qty_kg: float`（単位を明示）
   - 既存: `qty: float`（軽量表現）

4. **日付:**

   - 推奨: `date: date`（汎用フィールド）
   - 推奨: `sales_date: date`（売上日特定）
   - 推奨: `ddate: date`（カレンダーマスタ）

5. **カウント:**
   - 推奨: `line_count: int`（明細行数）
   - 推奨: `slip_count: int`（伝票数＝台数）
   - 推奨: `count: int`（表示用カウント値）

### camelCase vs snake_case

- **Pydantic (内部):** snake_case
- **JSON (API Response):** camelCase (serialization_alias使用)
- **SQL:** snake_case

---

## 6. まとめ

- **統一性が高い領域:** 顧客、品目、伝票番号、ISO週情報、営業日フラグ
- **揺れが大きい領域:** 営業担当ID、金額、重量、日付、カウント
- **型の不一致:** `rep_id` (int vs str)、`sales_rep_id` (int vs str)

今後のリファクタリングでは、上記の推奨方針に従って段階的に統一化を進めることを推奨します。

---

最終更新: 2025-11-27
