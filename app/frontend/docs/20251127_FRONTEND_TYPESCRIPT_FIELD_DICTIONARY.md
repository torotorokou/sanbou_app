# Frontend TypeScript Field Name Dictionary

## Document Overview

**作成日**: 2025-11-27  
**目的**: フロントエンドTypeScriptコードの型定義とフィールド名の体系的な整理

このドキュメントは、`app/frontend/src` 配下の主要な型定義（interface, type）を抽出し、APIレスポンスとのマッピング、UIコンポーネントで使用されるプロパティ名を収集・分類したものです。

---

## 1. Sales Pivot (売上ピボット分析)

### 1.1 Core Domain Types

#### MetricEntry (集計結果のエントリ)

**ファイル**: `app/frontend/src/features/analytics/sales-pivot/shared/model/types.ts`

```typescript
interface MetricEntry {
  id: ID; // エンティティ識別子 (string)
  name: string; // 表示名（顧客名/品名/日付）
  amount: number; // 売上金額（円）
  qty: number; // 数量（kg）
  line_count: number; // 明細行数（件数） - COUNT(*)
  slip_count: number; // 伝票数（台数） - COUNT(DISTINCT slip_no)
  count: number; // 表示用カウント値（軸によって意味が変わる）
  unit_price: number | null; // 単価（円/kg） - 数量=0の場合null
  dateKey?: YYYYMMDD; // 日付モード時のソート用キー
}
```

**フィールド解説**:

- `count`: 商品軸=`line_count`、それ以外=`slip_count`
- `unit_price`: 計算式 `Σ金額 / Σ数量`（数量=0の場合はnull）

#### SummaryRow (営業ごとのTopNメトリクス)

```typescript
interface SummaryRow {
  repId: ID; // 営業担当者ID
  repName: string; // 営業担当者名
  topN: MetricEntry[]; // TopNメトリクス配列
}
```

#### DailyPoint (日次推移データ)

```typescript
interface DailyPoint {
  date: YYYYMMDD; // 日付 (YYYY-MM-DD)
  amount: number; // 売上金額
  qty: number; // 数量
  line_count: number; // 明細行数
  slip_count: number; // 伝票数
  count: number; // 表示用カウント値
  unit_price: number | null; // 平均単価
}
```

#### DetailLine (詳細明細行)

```typescript
interface DetailLine {
  mode: DetailMode; // 'item_lines' | 'slip_summary'
  salesDate: string; // 売上日
  slipNo: number; // 伝票No
  repName: string; // 営業担当者名
  customerName: string; // 顧客名
  itemId: number | null; // 品目ID (item_lines時のみ)
  itemName: string; // 品目名
  lineCount: number | null; // 明細行数 (slip_summary時のみ)
  qtyKg: number; // 数量（kg）
  unitPriceYenPerKg: number | null; // 単価（円/kg）
  amountYen: number; // 金額（円）
}
```

### 1.2 Master Data Types

#### SalesRep (営業担当者)

```typescript
interface SalesRep {
  id: ID; // 営業担当者ID
  name: string; // 営業担当者名
}
```

#### UniverseEntry (汎用マスタエントリ)

```typescript
interface UniverseEntry {
  id: ID; // エンティティID
  name: string; // 表示名
  dateKey?: YYYYMMDD; // 日付モード時のソート用
}
```

**用途**: 顧客マスタ、品名マスタ、日付リストで共通使用

### 1.3 Query Types (API呼び出しパラメータ)

#### SummaryQuery

```typescript
interface SummaryQuery {
  month?: YYYYMM; // 単月指定 ('2025-11')
  monthRange?: { from: YYYYMM; to: YYYYMM }; // 期間指定
  dateFrom?: YYYYMMDD; // 日付範囲開始
  dateTo?: YYYYMMDD; // 日付範囲終了
  mode: Mode; // 集約軸 ('customer' | 'item' | 'date')
  categoryKind: CategoryKind; // カテゴリ種別 ('waste' | 'valuable')
  repIds: ID[]; // 営業IDフィルタ
  filterIds: ID[]; // エンティティIDフィルタ（軸に依存）
  sortBy: SortKey; // ソートキー
  order: SortOrder; // ソート順 ('asc' | 'desc')
  topN: 10 | 20 | 50 | "all"; // 取得件数
}
```

#### PivotQuery (ドリルダウン用)

```typescript
interface PivotQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  dateFrom?: YYYYMMDD;
  dateTo?: YYYYMMDD;
  baseAxis: Mode; // 固定軸
  baseId: ID; // 固定エンティティID
  categoryKind: CategoryKind;
  repIds: ID[];
  targetAxis: Mode; // 展開軸
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | "all";
  cursor?: string | null; // ページネーション用カーソル
}
```

#### DailySeriesQuery (日次推移用)

```typescript
interface DailySeriesQuery {
  month?: YYYYMM;
  monthRange?: { from: YYYYMM; to: YYYYMM };
  dateFrom?: YYYYMMDD;
  dateTo?: YYYYMMDD;
  categoryKind: CategoryKind;
  repId?: ID; // 営業IDフィルタ
  customerId?: ID; // 顧客IDフィルタ
  itemId?: ID; // 品名IDフィルタ
}
```

#### DetailLinesFilter (詳細明細行取得用)

```typescript
interface DetailLinesFilter {
  dateFrom: string; // 集計開始日 (YYYY-MM-DD)
  dateTo: string; // 集計終了日 (YYYY-MM-DD)
  lastGroupBy: GroupBy; // 最後の集計軸 ('rep' | 'customer' | 'date' | 'item')
  categoryKind: CategoryKind; // カテゴリ種別
  repId?: number; // 営業IDフィルタ
  customerId?: string; // 顧客IDフィルタ
  itemId?: number; // 品目IDフィルタ
  dateValue?: string; // 日付フィルタ (YYYY-MM-DD)
}
```

### 1.4 UI State Types

#### DrawerState (Pivotドロワー状態)

```typescript
type DrawerState =
  | { open: false }
  | {
      open: true;
      baseAxis: Mode;
      baseId: ID;
      baseName: string;
      month?: YYYYMM;
      monthRange?: { from: YYYYMM; to: YYYYMM };
      repIds: ID[];
      targets: { axis: Mode; label: string }[];
      activeAxis: Mode;
      sortBy: SortKey;
      order: SortOrder;
      topN: 10 | 20 | 50 | "all";
    };
```

#### PeriodState (期間選択状態)

```typescript
interface PeriodState {
  granularity: Granularity; // 'month' | 'date'
  mode: PeriodMode; // 'single' | 'range'
  // ... その他の期間関連プロパティ
}
```

#### FilterState (フィルタ状態)

```typescript
interface FilterState {
  mode: Mode;
  categoryKind: CategoryKind;
  repIds: ID[];
  filterIds: ID[];
  sortBy: SortKey;
  order: SortOrder;
  topN: 10 | 20 | 50 | "all";
}
```

---

## 2. Customer Churn (顧客離脱分析)

### 2.1 Domain Types

#### LostCustomer (離脱顧客)

**ファイル**: `app/frontend/src/features/analytics/customer-list/shared/domain/types.ts`

```typescript
type LostCustomer = {
  customerId: string; // 顧客ID
  customerName: string; // 顧客名
  salesRepId: string | null; // 営業担当者ID
  salesRepName: string | null; // 営業担当者名
  lastVisitDate: string; // 前期間の最終訪問日 (YYYY-MM-DD)
  prevVisitDays: number; // 前期間の訪問日数
  prevTotalAmountYen: number; // 前期間の合計金額（円）
  prevTotalQtyKg: number; // 前期間の合計重量（kg）
};
```

#### CustomerData (顧客データ)

```typescript
type CustomerData = {
  key: string; // 顧客キー（一意識別子）
  name: string; // 顧客名
  weight: number; // 合計重量 (kg)
  amount: number; // 合計金額 (円)
  sales: string; // 担当営業者
  lastDeliveryDate?: string; // 最終搬入日 (YYYY-MM-DD)
};
```

#### SalesRep (営業担当者 - Customer List版)

```typescript
type SalesRep = {
  salesRepId: string; // 営業担当者ID
  salesRepName: string; // 営業担当者名
};
```

### 2.2 Request/Response Types

#### CustomerChurnAnalyzeParams

```typescript
type CustomerChurnAnalyzeParams = {
  currentStart: string; // 今期間の開始日 (YYYY-MM-DD)
  currentEnd: string; // 今期間の終了日 (YYYY-MM-DD)
  previousStart: string; // 前期間の開始日 (YYYY-MM-DD)
  previousEnd: string; // 前期間の終了日 (YYYY-MM-DD)
};
```

#### CustomerComparisonResult

```typescript
interface CustomerComparisonResult {
  currentCustomers: CustomerData[]; // 今期の顧客
  previousCustomers: CustomerData[]; // 前期の顧客
  lostCustomers: CustomerData[]; // 離脱顧客
  newCustomers: CustomerData[]; // 新規顧客
  retainedCustomers: CustomerData[]; // 継続顧客
}
```

### 2.3 Period Types

#### PeriodRange (期間範囲)

**ファイル**: `app/frontend/src/features/analytics/customer-list/period-selector/domain/types.ts`

```typescript
interface PeriodRange {
  start: Dayjs | null; // 開始日
  end: Dayjs | null; // 終了日
}
```

#### ComparisonPeriods (比較期間)

```typescript
interface ComparisonPeriods {
  current: PeriodRange; // 今期
  previous: PeriodRange; // 前期
}
```

---

## 3. Dashboard Ukeire (受入ダッシュボード)

### 3.1 Domain Types

**ファイル**: `app/frontend/src/features/dashboard/ukeire/domain/types.ts`

#### MonthPayloadDTO (月次データペイロード)

```typescript
type MonthPayloadDTO = {
  header: HeaderDTO;
  targets: TargetsDTO;
  calendar: { days: CalendarDay[] };
  progress: ProgressDTO;
  forecast: ForecastDTO;
  daily_curve: DailyCurveDTO[];
  weeks: WeekRowDTO[];
  history: HistoryDTO;
  prev_month_daily?: Record<IsoDate, number>;
  prev_year_daily?: Record<IsoDate, number>;
};
```

#### HeaderDTO (ヘッダー情報)

```typescript
type HeaderDTO = {
  month: IsoMonth; // 'YYYY-MM'
  business_days: {
    total: number;
    mon_sat: number;
    sun_holiday: number;
    non_business: number;
  };
  rules: {
    week_def: string;
    week_to_month: string;
    alignment: string;
  };
};
```

#### ProgressDTO (進捗情報)

```typescript
type ProgressDTO = {
  mtd_actual: number; // 月累計実績
  remaining_business_days: number; // 残り営業日数
};
```

#### ForecastDTO (予測情報)

```typescript
type ForecastDTO = {
  today: { p50: number; p10: number; p90: number };
  week: { p50: number; p10: number; p90: number; target: number };
  month_landing: { p50: number; p10: number; p90: number };
};
```

#### DailyCurveDTO (日次カーブデータ)

```typescript
type DailyCurveDTO = {
  date: IsoDate; // 'YYYY-MM-DD'
  from_7wk: number; // 7週平均からの値
  from_month_share: number; // 月シェアからの値
  bookings: number; // 予約
  actual?: number; // 実績
};
```

#### WeekRowDTO (週次データ)

```typescript
type WeekRowDTO = {
  week_id: IsoDate;
  week_start: IsoDate;
  week_end: IsoDate;
  business_week_index_in_month: number;
  ton_in_month: number;
  in_month_business_days: number;
  portion_in_month: number;
  targets: { week: number };
  comparisons: {
    vs_prev_week: {
      delta_ton: number | null;
      delta_pct: number | null;
      align_note: string;
    };
    vs_prev_month_same_idx: {
      delta_ton: number | null;
      delta_pct: number | null;
      align_note: string;
    };
    vs_prev_year_same_idx: {
      delta_ton: number | null;
      delta_pct: number | null;
      align_note: string;
    };
  };
};
```

#### CalendarDay (カレンダー日付)

```typescript
type CalendarDay = {
  date: IsoDate; // 'YYYY-MM-DD'
  is_business_day: 0 | 1;
  is_holiday: 0 | 1;
  week_id: IsoDate; // 週の月曜日
};
```

### 3.2 Inbound Daily Types

**ファイル**: `app/frontend/src/features/dashboard/ukeire/inbound-monthly/ports/InboundDailyRepository.ts`

#### InboundDailyRow (日次受入行)

```typescript
type InboundDailyRow = {
  date: string; // 'YYYY-MM-DD'
  value: number; // 受入量
  cumulative: number; // 累積値
  // ... その他
};
```

---

## 4. Calendar (カレンダー)

### 4.1 Domain Types

**ファイル**: `app/frontend/src/features/calendar/domain/types.ts`

#### CalendarDayDTO

```typescript
type CalendarDayDTO = {
  ddate: string; // 'YYYY-MM-DD'
  y: number; // 年
  m: number; // 月
  iso_year: number; // ISO年
  iso_week: number; // ISO週番号
  iso_dow: number; // ISO曜日（1=月, 7=日）
  is_holiday: boolean; // 祝日フラグ
  is_second_sunday: boolean; // 第2日曜日フラグ
  is_company_closed: boolean; // 会社休業日フラグ
  day_type: string; // 日タイプ (NORMAL, RESERVATION, CLOSED)
  is_business: boolean; // 営業日フラグ
  date?: string; // 後方互換性のため
  isHoliday?: boolean; // 後方互換性のため
};
```

#### CalendarCell (描画セル)

```typescript
interface CalendarCell {
  date: string; // ISO 'YYYY-MM-DD'
  inMonth: boolean; // 月内かどうか
  [key: string]: unknown; // 任意のプロパティ拡張可能
}
```

---

## 5. Notification (通知)

### 5.1 Domain Types

**ファイル**: `app/frontend/src/features/notification/domain/types/notification.types.ts`

#### Notification

```typescript
interface Notification {
  id: string;
  type: NotificationType; // 'success' | 'error' | 'warning' | 'info'
  title: string;
  message?: string;
  createdAt: Date;
  duration?: number | null;
}
```

#### CreateNotificationData

```typescript
interface CreateNotificationData {
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number | null;
}
```

### 5.2 Job Status Types

**ファイル**: `app/frontend/src/features/notification/infrastructure/jobService.ts`

#### JobStatus

```typescript
interface JobStatus {
  jobId: string;
  status: JobStatusType; // 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress?: number; // 進捗率 (0-100)
  message?: string;
  result?: unknown;
  error?: string;
}
```

---

## 6. Shared Types (共通型)

### 6.1 API Types

**ファイル**: `app/frontend/src/shared/types/api.ts`

#### ApiResponse<T>

```typescript
type ApiResponse<T> = {
  status: "success" | "error"; // レスポンスステータス
  code: string; // エラーコード（大文字スネークケース）
  detail: string; // ユーザー向け詳細メッセージ
  result?: T | null; // 成功時の結果データ
  hint?: string | null; // ヒント（任意）
};
```

#### ApiError

```typescript
class ApiError extends Error {
  code: string; // エラーコード
  httpStatus: number; // HTTPステータスコード
  userMessage: string; // ユーザー向けメッセージ
  title?: string; // エラータイトル
  traceId?: string; // トレースID
}
```

---

## 7. API Client Layer (Repository実装)

### 7.1 Customer Churn Repository

**ファイル**: `app/frontend/src/features/analytics/customer-list/shared/infrastructure/customerChurnRepository.ts`

#### API呼び出し時のフィールドマッピング

**getSalesReps():**

```typescript
// APIレスポンス (snake_case)
{
  sales_reps: [{
    sales_rep_id: string,
    sales_rep_name: string
  }]
}

// フロントエンド型 (camelCase)
{
  salesRepId: string,
  salesRepName: string
}
```

**analyze():**

```typescript
// APIリクエスト (snake_case)
{
  current_start: string,
  current_end: string,
  previous_start: string,
  previous_end: string
}

// APIレスポンス (snake_case)
{
  lost_customers: [{
    customer_id: string,
    customer_name: string,
    sales_rep_id: string | null,
    sales_rep_name: string | null,
    last_visit_date: string,
    prev_visit_days: number,
    prev_total_amount_yen: number,
    prev_total_qty_kg: number
  }]
}

// フロントエンド型 (camelCase)
{
  customerId: string,
  customerName: string,
  salesRepId: string | null,
  salesRepName: string | null,
  lastVisitDate: string,
  prevVisitDays: number,
  prevTotalAmountYen: number,
  prevTotalQtyKg: number
}
```

---

## 8. Concept Clustering (概念別グルーピング)

### 8.1 営業担当 (Sales Representative)

#### フロントエンド型フィールド名

- `repId` (Sales Pivot)
- `repName` (Sales Pivot)
- `salesRepId` (Customer Churn)
- `salesRepName` (Customer Churn)

#### APIレスポンスフィールド名 (snake_case)

- `rep_id`
- `rep_name`
- `sales_rep_id`
- `sales_rep_name`

**命名パターン**:

- Sales Pivot: `rep` プレフィックス
- Customer Churn: `salesRep` プレフィックス
- 変換規則: camelCase (FE) ⇔ snake_case (API)

### 8.2 顧客 (Customer)

#### フロントエンド型フィールド名

- `customerId` (共通)
- `customerName` (共通)
- `key` (CustomerData専用 - 一意識別子)
- `name` (CustomerData専用)

#### APIレスポンスフィールド名

- `customer_id`
- `customer_name`

**命名パターン**:

- 一貫して `customer` プレフィックス
- 変換規則: camelCase (FE) ⇔ snake_case (API)

### 8.3 金額 (Amount)

#### フロントエンド型フィールド名

- `amount` (MetricEntry, CustomerData - 単位なし)
- `amountYen` (DetailLine - 単位明示)
- `prevTotalAmountYen` (LostCustomer - 前期間・単位明示)
- `totalAmountYen` (仮想 - 使用例あり)

#### APIレスポンスフィールド名

- `amount`
- `amount_yen`
- `prev_total_amount_yen`
- `total_amount_yen`

**命名パターン**:

- 基本: `amount` （単位なし）
- 単位明示: `amountYen` / `amount_yen`
- 前期間: `prevTotal` プレフィックス

### 8.4 数量 (Quantity)

#### フロントエンド型フィールド名

- `qty` (MetricEntry, DailyPoint - 単位なし・略記)
- `qtyKg` (DetailLine - 単位明示)
- `prevTotalQtyKg` (LostCustomer - 前期間・単位明示)
- `weight` (CustomerData - 別名)

#### APIレスポンスフィールド名

- `qty`
- `qty_kg`
- `prev_total_qty_kg`
- `weight`

**命名パターン**:

- 略記: `qty` （単位なし）
- 単位明示: `qtyKg` / `qty_kg`
- 別名: `weight`（CustomerDataで使用）

### 8.5 件数・カウント (Count)

#### フロントエンド型フィールド名

- `count` (MetricEntry - 表示用カウント値)
- `line_count` (MetricEntry, DailyPoint - 明細行数)
- `slip_count` (MetricEntry, DailyPoint - 伝票数)
- `lineCount` (DetailLine - 明細行数)
- `totalCount` (DetailLinesResponse - 総行数)

#### APIレスポンスフィールド名

- `count`
- `line_count`
- `slip_count`
- `total_count`

**命名パターン**:

- 汎用: `count`
- 明細行: `line_count` / `lineCount`
- 伝票: `slip_count` / `slipCount`
- snake_case (API) ⇔ camelCase (FE)

### 8.6 単価 (Unit Price)

#### フロントエンド型フィールド名

- `unit_price` (MetricEntry, DailyPoint - snake_case残存)
- `unitPriceYenPerKg` (DetailLine - 単位完全明示)

#### APIレスポンスフィールド名

- `unit_price`
- `unit_price_yen_per_kg`

**命名パターン**:

- 基本: `unit_price` （snake_caseがFEにも残存）
- 単位完全明示: `unitPriceYenPerKg`

### 8.7 日付 (Date)

#### フロントエンド型フィールド名

- `date` (DailyPoint, CalendarDay, CalendarDayDTO - ISO形式)
- `ddate` (CalendarDayDTO - DBカラム名そのまま)
- `salesDate` (DetailLine - 売上日)
- `lastVisitDate` (LostCustomer - 最終訪問日)
- `lastDeliveryDate` (CustomerData - 最終搬入日)
- `dateKey` (MetricEntry - ソート用)
- `dateFrom` / `dateTo` (Query系 - 範囲指定)
- `currentStart` / `currentEnd` (CustomerChurnAnalyzeParams)
- `previousStart` / `previousEnd` (CustomerChurnAnalyzeParams)

#### APIレスポンスフィールド名

- `date`
- `ddate`
- `sales_date`
- `last_visit_date`
- `last_delivery_date`
- `date_from` / `date_to`
- `current_start` / `current_end`
- `previous_start` / `previous_end`

**命名パターン**:

- 基本: `date` (ISO形式 YYYY-MM-DD)
- 目的別接頭辞: `sales`, `last`, `delivery`
- 範囲: `from` / `to`, `start` / `end`

### 8.8 識別子 (ID)

#### フロントエンド型フィールド名

- `id` (汎用 - MetricEntry, UniverseEntry, SalesRep)
- `repId` (Sales Pivot)
- `salesRepId` (Customer Churn)
- `customerId` (共通)
- `itemId` (DetailLine, Query系)
- `slipNo` (DetailLine - 伝票番号)
- `key` (CustomerData - 一意識別子)
- `jobId` (JobStatus)

#### APIレスポンスフィールド名

- `id`
- `rep_id`
- `sales_rep_id`
- `customer_id`
- `item_id`
- `slip_no`
- `key`
- `job_id`

**命名パターン**:

- 汎用: `id`
- エンティティ別: `{entity}Id` (camelCase)
- API: `{entity}_id` (snake_case)

### 8.9 名称 (Name)

#### フロントエンド型フィールド名

- `name` (汎用 - UniverseEntry, SalesRep)
- `repName` (Sales Pivot)
- `salesRepName` (Customer Churn)
- `customerName` (共通)
- `itemName` (DetailLine)
- `baseName` (DrawerState)

#### APIレスポンスフィールド名

- `name`
- `rep_name`
- `sales_rep_name`
- `customer_name`
- `item_name`
- `base_name`

**命名パターン**:

- 汎用: `name`
- エンティティ別: `{entity}Name` (camelCase)
- API: `{entity}_name` (snake_case)

---

## 9. Naming Convention Issues (命名規則の課題)

### 9.1 snake_case と camelCase の混在

**問題点**:

- APIレスポンスは snake_case
- フロントエンドドメイン型は camelCase
- 一部のフィールドで変換漏れ（例: `unit_price`, `line_count`, `slip_count`）

**影響範囲**:

- `MetricEntry` の `unit_price`, `line_count`, `slip_count`
- `DailyPoint` の `unit_price`, `line_count`, `slip_count`

**推奨対応**:

```typescript
// 現状（変換漏れ）
interface MetricEntry {
  unit_price: number | null; // ❌ snake_case
  line_count: number; // ❌ snake_case
  slip_count: number; // ❌ snake_case
}

// 推奨（統一）
interface MetricEntry {
  unitPrice: number | null; // ✅ camelCase
  lineCount: number; // ✅ camelCase
  slipCount: number; // ✅ camelCase
}
```

### 9.2 同じ概念で異なるプレフィックス

**問題点**:

- 営業担当: `rep` (Sales Pivot) vs `salesRep` (Customer Churn)
- 顧客: 一貫して `customer` だが、`key` という別名も存在

**影響範囲**:

- Sales Pivot: `repId`, `repName`
- Customer Churn: `salesRepId`, `salesRepName`

**推奨対応**:

- プロジェクト全体で統一プレフィックスを採用
- 例: `salesRepId`, `salesRepName` に統一

### 9.3 単位の明示

**問題点**:

- 単位なし: `amount`, `qty`
- 単位あり: `amountYen`, `qtyKg`, `unitPriceYenPerKg`
- 一貫性なし

**推奨対応**:

```typescript
// 基本方針: 金額・重量・単価は単位を明示
interface MetricEntry {
  amountYen: number; // ✅ 金額は常に単位明示
  qtyKg: number; // ✅ 重量は常に単位明示
  unitPriceYenPerKg: number | null; // ✅ 単価は完全明示
}
```

### 9.4 オプショナルプロパティの不一致

**問題点**:

- `dateKey?: YYYYMMDD` (オプショナル)
- `lastDeliveryDate?: string` (オプショナル)
- `message?: string` (オプショナル)
- API側とフロントエンド側でオプショナル性が不一致の場合あり

**推奨対応**:

- API仕様と完全一致させる
- null許容型とオプショナルを明確に区別

---

## 10. Best Practices (ベストプラクティス)

### 10.1 命名規則の統一

1. **camelCase 徹底**:

   - フロントエンド型は全て camelCase
   - API変換レイヤーで snake_case → camelCase 変換

2. **単位の明示**:

   - 金額: `amountYen`
   - 重量: `qtyKg`, `weightKg`
   - 単価: `unitPriceYenPerKg`

3. **プレフィックスの統一**:
   - 営業: `salesRep` で統一
   - 顧客: `customer` で統一
   - 品目: `item` で統一

### 10.2 型定義の配置

1. **ドメイン型**: `features/{feature}/domain/types.ts`
2. **API型**: `features/{feature}/infrastructure/*.ts`
3. **共通型**: `shared/types/*.ts`

### 10.3 API変換レイヤー

```typescript
// Repository実装で明示的に変換
async analyze(params: CustomerChurnAnalyzeParams): Promise<LostCustomer[]> {
  const response = await coreApi.post('/api/customer-churn', {
    // camelCase → snake_case
    current_start: params.currentStart,
    current_end: params.currentEnd,
    previous_start: params.previousStart,
    previous_end: params.previousEnd,
  });

  // snake_case → camelCase
  return response.lost_customers.map((c) => ({
    customerId: c.customer_id,
    customerName: c.customer_name,
    salesRepId: c.sales_rep_id,
    salesRepName: c.sales_rep_name,
    lastVisitDate: c.last_visit_date,
    prevVisitDays: c.prev_visit_days,
    prevTotalAmountYen: c.prev_total_amount_yen,
    prevTotalQtyKg: c.prev_total_qty_kg,
  }));
}
```

---

## 11. Type Alias Reference (型エイリアス参照)

```typescript
// 基本型
type YYYYMM = string; // "2025-11"
type YYYYMMDD = string; // "2025-11-21"
type ID = string; // エンティティ識別子
type IsoMonth = string; // "YYYY-MM"
type IsoDate = string; // "YYYY-MM-DD"

// 列挙型
type Mode = "customer" | "item" | "date";
type SortKey = "amount" | "qty" | "count" | "unit_price" | "date" | "name";
type SortOrder = "asc" | "desc";
type CategoryKind = "waste" | "valuable";
type Granularity = "month" | "date";
type PeriodMode = "single" | "range";
type DetailMode = "item_lines" | "slip_summary";
type GroupBy = "rep" | "customer" | "date" | "item";
type NotificationType = "success" | "error" | "warning" | "info";
type JobStatusType =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";
type CumScope = "range" | "month" | "week" | "none";
```

---

## 12. Summary (まとめ)

### 12.1 主要な型定義の配置

| 機能             | 型定義ファイル                                             |
| ---------------- | ---------------------------------------------------------- |
| Sales Pivot      | `features/analytics/sales-pivot/shared/model/types.ts`     |
| Customer Churn   | `features/analytics/customer-list/shared/domain/types.ts`  |
| Dashboard Ukeire | `features/dashboard/ukeire/domain/types.ts`                |
| Calendar         | `features/calendar/domain/types.ts`                        |
| Notification     | `features/notification/domain/types/notification.types.ts` |
| API共通          | `shared/types/api.ts`                                      |

### 12.2 命名規則サマリ

| 概念     | FE型                                 | API型                                   | 注意点               |
| -------- | ------------------------------------ | --------------------------------------- | -------------------- |
| 営業担当 | `repId`, `salesRepId`                | `rep_id`, `sales_rep_id`                | プレフィックス不統一 |
| 顧客     | `customerId`                         | `customer_id`                           | 統一                 |
| 金額     | `amount`, `amountYen`                | `amount`, `amount_yen`                  | 単位明示推奨         |
| 数量     | `qty`, `qtyKg`, `weight`             | `qty`, `qty_kg`, `weight`               | 別名あり             |
| 件数     | `count`, `lineCount`, `slipCount`    | `count`, `line_count`, `slip_count`     | snake_case混在       |
| 単価     | `unit_price`, `unitPriceYenPerKg`    | `unit_price`, `unit_price_yen_per_kg`   | snake_case混在       |
| 日付     | `date`, `salesDate`, `lastVisitDate` | `date`, `sales_date`, `last_visit_date` | 目的別接頭辞         |

### 12.3 改善推奨事項

1. **snake_case残存の解消**: `unit_price`, `line_count`, `slip_count` を camelCase に統一
2. **プレフィックス統一**: `rep` → `salesRep` に統一
3. **単位明示の徹底**: `amount` → `amountYen`, `qty` → `qtyKg`
4. **型定義の集約**: 共通型は `shared/types` に集約

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-11-27
