# カラム名辞書 (Column Naming Dictionary)

**作成日**: 2025-11-27  
**目的**: プロジェクト全体のカラム名を体系的に整理し、命名規則の一貫性を向上させる

---

## 📖 概要

このドキュメントは、sanbou_app プロジェクト全体で使用されるカラム名を「概念」ごとに分類し、レイヤー間（DB / バックエンド / フロントエンド）での名称の揺れを可視化したものです。

**調査範囲**:

- **データベース**: PostgreSQL (raw/stg/mart/ref/kpi/forecast/log スキーマ)
- **バックエンド**: FastAPI + Pydantic (Python)
- **フロントエンド**: React + TypeScript

---

## 🎯 Concept Clustering (概念別カラム名グループ)

### 1. 営業担当 (Sales Representative)

| 概念       | Canonical候補 | レイヤー別の使用状況                                                                                                                                                                                    |
| ---------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **営業ID** | `rep_id`      | **raw/stg**: `sales_staff_cd` (integer)<br>**mart**: `rep_id` (integer AS)<br>**API (Pydantic)**: `rep_id` (int), `sales_rep_id` (str \| int)<br>**FE (TypeScript)**: `repId` (camelCase), `salesRepId` |
| **営業名** | `rep_name`    | **raw/stg**: `sales_staff_name` (text)<br>**mart**: `rep_name` (text AS)<br>**API**: `rep_name`, `sales_rep_name`<br>**FE**: `repName`, `salesRepName`                                                  |

**問題点**:

- raw/stg では `sales_staff_cd` だが、mart 以降は `rep_id` に変換
- Customer Churn API では `sales_rep_id` を使用（接頭辞の不統一）
- TypeScript では `repId` と `salesRepId` が混在

**推奨**:

- **Canonical**: `rep_id` (integer), `rep_name` (text)
- **理由**: 簡潔で、すでに mart 層とメイン API で採用済み
- **raw/stg 互換**: 辞書マッピングで `sales_staff_cd` → `rep_id` を管理

---

### 2. 顧客 (Customer)

| 概念       | Canonical候補   | レイヤー別の使用状況                                                                                                                     |
| ---------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **顧客ID** | `customer_id`   | **raw/stg**: `client_cd` (text)<br>**mart**: `customer_id` (text AS)<br>**API**: `customer_id` (str)<br>**FE**: `customerId` (camelCase) |
| **顧客名** | `customer_name` | **raw/stg**: `client_name` (text)<br>**mart**: `customer_name` (text AS)<br>**API**: `customer_name` (str)<br>**FE**: `customerName`     |

**問題点**:

- raw/stg では `client_cd` だが、mart 以降は `customer_id` に変換
- ドメイン用語として「customer」の方が一般的だが、元データは「client」

**推奨**:

- **Canonical**: `customer_id` (text), `customer_name` (text)
- **理由**: ビジネスドメインでは「customer」が標準的。API/FEですでに統一済み
- **raw/stg 互換**: `client_cd` → `customer_id` のマッピングを維持

---

### 3. 品目 (Item)

| 概念       | Canonical候補 | レイヤー別の使用状況                                                                                                         |
| ---------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **品目ID** | `item_id`     | **raw/stg**: `item_cd` (integer)<br>**mart**: `item_id` (integer AS)<br>**API**: `item_id` (int)<br>**FE**: `itemId`         |
| **品目名** | `item_name`   | **raw/stg**: `item_name` (text)<br>**mart**: `item_name` (text、AS なし)<br>**API**: `item_name` (str)<br>**FE**: `itemName` |

**問題点**:

- `item_cd` → `item_id` の変換があるが、統一性は比較的良好

**推奨**:

- **Canonical**: `item_id` (integer), `item_name` (text)
- **理由**: ID サフィックスの方が直感的で、すでに採用済み

---

### 4. 金額 (Amount)

| 概念           | Canonical候補 | レイヤー別の使用状況                                                                                                                                                                                                                                  |
| -------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **金額（円）** | `amount`      | **raw/stg**: `amount` (numeric)<br>**mart**: `amount_yen` (numeric AS) または `amount`<br>**API**: `amount` (float), `total_amount_yen` (float), `prev_total_amount_yen` (float)<br>**FE**: `amount` (number), `totalAmountYen`, `prevTotalAmountYen` |

**問題点**:

- **単位の明示が不統一**: `amount` vs `amount_yen` vs `total_amount_yen`
- 集計値には `total_` プレフィックスが付くが、基本値は付かない

**推奨**:

- **基本値**: `amount` (単位: 円)
- **集計値**: `total_amount` (単位明示は文脈・ドキュメントで管理)
- **理由**:
  - 単位を毎回カラム名に含めると冗長になる
  - `_yen` サフィックスは日本市場特有で、国際化時に問題
  - ドキュメントやコメントで単位を明示する方が柔軟

**段階的移行案**:

1. 短期: `amount` vs `amount_yen` の混在を許容（文脈で判断）
2. 中期: 新規実装では `amount` に統一し、ドキュメントで単位を明記
3. 長期: 既存の `amount_yen` を段階的に `amount` に統一

---

### 5. 数量・重量 (Quantity / Weight)

| 概念               | Canonical候補 | レイヤー別の使用状況                                                                                                                                                                                                                |
| ------------------ | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **正味重量（kg）** | `net_weight`  | **raw/stg**: `net_weight` (numeric)<br>**mart**: `qty_kg` (numeric AS) または `net_weight`<br>**API**: `qty` (float), `total_qty_kg` (float), `prev_total_qty_kg` (float)<br>**FE**: `qty` (number), `totalQtyKg`, `prevTotalQtyKg` |

**問題点**:

- **3つの呼び方が混在**: `net_weight` vs `qty_kg` vs `qty`
- 単位の明示が不統一（`kg` サフィックス）

**推奨**:

- **基本値**: `net_weight` (単位: kg)
- **集計値**: `total_net_weight` (単位: kg)
- **理由**:
  - `net_weight` が元データの正式名称
  - `qty` は抽象的すぎて単位が不明
  - `_kg` サフィックスは金額と同様の理由で冗長
  - ドキュメントで「net_weight の単位は kg」を明記

**段階的移行案**:

1. 短期: `qty_kg` / `qty` / `net_weight` の混在を許容
2. 中期: 新規実装では `net_weight` に統一
3. 長期: 既存の `qty_kg` を `net_weight` に統一

---

### 6. 伝票番号 (Slip Number)

| 概念         | Canonical候補 | レイヤー別の使用状況                                                                                                         |
| ------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **伝票番号** | `slip_no`     | **raw/stg**: `receive_no` (integer/text)<br>**mart**: `slip_no` (AS)<br>**API**: `slip_no` (str/int混在)<br>**FE**: `slipNo` |

**問題点**:

- raw/stg では `receive_no` だが、mart 以降は `slip_no` に変換
- 伝票の種類（受入・出荷・ヤード）で異なる列名を使用

**推奨**:

- **Canonical**: `slip_no` (text/integer)
- **理由**: 「伝票番号」として一般的な用語
- **raw/stg 互換**: `receive_no` → `slip_no` のマッピングを維持

---

### 7. 日付 (Date)

| 概念             | Canonical候補 | レイヤー別の使用状況                                                                                                                                             |
| ---------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **売上日**       | `sales_date`  | **raw/stg**: `sales_date` (date)<br>**mart**: `sales_date` (date、AS ありの場合も)<br>**API**: `sales_date` (date_type)<br>**FE**: `salesDate` (YYYYMMDD string) |
| **伝票日**       | `slip_date`   | **raw/stg**: `slip_date` (date)<br>**mart**: fallback として使用<br>**API**: 使用頻度低<br>**FE**: 使用頻度低                                                    |
| **日付（汎用）** | `ddate`       | **ref/mart**: `ddate` (date、カレンダービュー)<br>**API**: `date` (date_type)<br>**FE**: `date` (YYYYMMDD string)                                                |

**問題点**:

- `sales_date` vs `date` vs `ddate` の使い分けが曖昧
- `COALESCE(sales_date, slip_date)` のような複合ロジックが多い

**推奨**:

- **業務日付**: `sales_date` (date)
- **カレンダー日付**: `ddate` (date、ref.v_calendar_classified 等)
- **汎用日付**: `date` (date、集計結果等)
- **理由**: 用途に応じて使い分ける現状が妥当

---

### 8. 件数・カウント (Count)

| 概念               | Canonical候補 | レイヤー別の使用状況                                                                                                             |
| ------------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **明細行数**       | `line_count`  | **mart**: `line_count` (COUNT(\*) の結果)<br>**API**: `line_count` (int)<br>**FE**: `line_count` (number、snake_case残存)        |
| **伝票数（台数）** | `slip_count`  | **mart**: `slip_count` (COUNT(DISTINCT slip_no))<br>**API**: `slip_count` (int)<br>**FE**: `slip_count` (number、snake_case残存) |
| **訪問回数**       | `visit_count` | **mart**: `visit_count` (COUNT(DISTINCT slip_no) AS)<br>**API**: `visit_count` (int)<br>**FE**: `visitCount` (number)            |

**問題点**:

- `count` の意味が文脈によって異なる（明細 vs 伝票）
- TypeScript で `line_count`, `slip_count` がsnake_caseのまま残存

**推奨**:

- **明細行数**: `line_count` (integer)
- **伝票数**: `slip_count` (integer)
- **訪問回数**: `visit_count` (integer)
- **汎用カウント**: `count` (integer、表示用の柔軟な値）
- **理由**: 既存の命名が概念を明確に区別しており、変更不要

**FE改善案**:

- TypeScript型で `lineCount`, `slipCount` に変換（APIレスポンス受信時）

---

### 9. 単価 (Unit Price)

| 概念              | Canonical候補 | レイヤー別の使用状況                                                                                                                                                                   |
| ----------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **単価（円/kg）** | `unit_price`  | **raw/stg**: `unit_price` (numeric)<br>**mart**: `unit_price` (計算: amount / qty)<br>**API**: `unit_price` (Optional[float])<br>**FE**: `unit_price` (number \| null、snake_case残存) |

**問題点**:

- TypeScript で `unit_price` がsnake_caseのまま残存

**推奨**:

- **Canonical**: `unit_price` (numeric, nullable)
- **理由**: すでに全レイヤーで統一されており、変更不要

**FE改善案**:

- TypeScript型で `unitPrice` に変換

---

### 10. カテゴリ (Category)

| 概念               | Canonical候補   | レイヤー別の使用状況                                                                                                                                    |
| ------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **カテゴリコード** | `category_cd`   | **raw/stg**: `category_cd` (integer)<br>**mart**: `category_cd` (integer)<br>**API**: `category_kind` ('waste' \| 'valuable')<br>**FE**: `categoryKind` |
| **カテゴリ名**     | `category_name` | **raw/stg**: `category_name` (text)<br>**mart**: `category_name` (text)                                                                                 |
| **カテゴリ種別**   | `category_kind` | **mart**: `category_kind` (CASE式、'waste'/'valuable'/'other')<br>**API**: `category_kind` (CategoryKind型)<br>**FE**: `categoryKind`                   |

**問題点**:

- コード（`category_cd`）と種別（`category_kind`）が混在

**推奨**:

- **内部処理**: `category_cd` (integer、1=廃棄物, 3=有価物)
- **外部公開**: `category_kind` (enum string、'waste'/'valuable')
- **理由**: 数値コードは内部管理用、文字列enumは可読性の高いAPI用

---

### 11. タイムスタンプ (Timestamps)

| 概念         | Canonical候補 | レイヤー別の使用状況                                                                                                                   |
| ------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **作成日時** | `created_at`  | **全テーブル**: `created_at` (timestamp with time zone)<br>**API**: `created_at` (datetime)<br>**FE**: `createdAt`                     |
| **更新日時** | `updated_at`  | **全テーブル**: `updated_at` (timestamp with time zone)<br>**API**: `updated_at` (datetime)<br>**FE**: `updatedAt`                     |
| **削除日時** | `deleted_at`  | **全テーブル**: `deleted_at` (timestamp with time zone, nullable)<br>**API**: `deleted_at` (Optional[datetime])<br>**FE**: `deletedAt` |

**問題点**:

- なし。全レイヤーで統一されている

**推奨**:

- **Canonical**: `created_at`, `updated_at`, `deleted_at`
- **理由**: Rails規約に準拠し、業界標準

---

### 12. 論理削除フラグ (Soft Delete)

| 概念           | Canonical候補 | レイヤー別の使用状況                                                                                       |
| -------------- | ------------- | ---------------------------------------------------------------------------------------------------------- |
| **削除フラグ** | `is_deleted`  | **全テーブル**: `is_deleted` (boolean, default false)<br>**API**: クエリ条件で使用<br>**FE**: 直接使用せず |
| **削除実行者** | `deleted_by`  | **全テーブル**: `deleted_by` (text, nullable)<br>**API**: 使用頻度低<br>**FE**: 使用頻度低                 |

**問題点**:

- なし

**推奨**:

- **Canonical**: `is_deleted` (boolean), `deleted_by` (text)
- **理由**: 標準的なsoft delete実装パターン

---

### 13. アップロード追跡 (Upload Tracking)

| 概念                       | Canonical候補    | レイヤー別の使用状況                                                                                                         |
| -------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **アップロードファイルID** | `upload_file_id` | **stg**: `upload_file_id` (integer, FK)<br>**mart**: `upload_file_id` (integer)<br>**API**: 使用頻度低<br>**FE**: 使用頻度低 |
| **元行番号**               | `source_row_no`  | **stg**: `source_row_no` (integer)<br>**mart**: `source_row_no` (integer)<br>**API**: 使用頻度低<br>**FE**: 使用頻度低       |
| **ソースID**               | `source_id`      | **mart**: `source_id` (integer AS id)<br>**API**: 使用頻度低<br>**FE**: 使用頻度低                                           |

**問題点**:

- `id` → `source_id` への別名付けの意図が不明瞭

**推奨**:

- **Canonical**: `upload_file_id` (integer), `source_row_no` (integer)
- **source_id**: 明確な用途がない場合は削除を検討

---

## 📐 レイヤー別命名方針

### 1. raw / stg 層（データソース層）

**方針**: 外部システム・CSV由来の名前をそのまま維持

- **理由**:
  - データの出所が明確になる
  - 元データとの対応関係が分かりやすい
  - 変換ロジックの追跡が容易

**例**:

- `sales_staff_cd`, `client_cd`, `item_cd`, `receive_no`, `amount`, `net_weight`

**ルール**:

- 型変換のみ実施（text → integer/numeric/date）
- カラム名の変更は行わない
- 必要に応じて計算列を追加（元カラムは維持）

---

### 2. mart 層（ビジネスロジック層）

**方針**: ドメイン駆動のcanonical名に統一

- **理由**:
  - ビジネスドメインの用語に合わせる
  - API/FEとの一貫性を保つ
  - 簡潔で分かりやすい名前にする

**例**:

- `rep_id`, `customer_id`, `item_id`, `slip_no`

**ルール**:

- IDは `<concept>_id` 形式
- 名称は `<concept>_name` 形式
- 日付は `<purpose>_date` 形式（例: `sales_date`, `slip_date`）
- タイムスタンプは `<event>_at` 形式（例: `created_at`, `updated_at`）
- 論理フラグは `is_<state>` 形式（例: `is_deleted`, `is_business`）
- 集計値は `total_<metric>` 形式（例: `total_amount`, `total_net_weight`）

---

### 3. API層（Pydantic / FastAPI）

**方針**: mart層のカラム名を踏襲し、snake_caseで統一

- **理由**:
  - Python規約（PEP 8）に準拠
  - SQLと1対1対応で変換不要
  - 型安全性を最大化

**例**:

```python
class MetricEntry(BaseModel):
    id: str
    name: str
    amount: float
    net_weight: float
    line_count: int
    slip_count: int
    unit_price: Optional[float]
```

**ルール**:

- **snake_case** で統一（例: `rep_id`, `customer_name`）
- DB列名と完全一致させる（変換レイヤーを最小化）
- オプショナル値は `Optional[T]` で明示
- 列挙型は `Literal` または `Enum` で定義

---

### 4. FE層（TypeScript / React）

**方針**: camelCaseに変換し、JavaScript規約に準拠

- **理由**:
  - JavaScript/TypeScript標準規約
  - React/Vue等のエコシステムとの一貫性
  - フロントエンドコードの可読性

**例**:

```typescript
interface MetricEntry {
  id: string;
  name: string;
  amount: number;
  netWeight: number;
  lineCount: number;
  slipCount: number;
  unitPrice: number | null;
}
```

**ルール**:

- **camelCase** で統一（例: `repId`, `customerName`）
- APIレスポンス受信時に snake_case → camelCase 変換
- API送信時に camelCase → snake_case 変換
- 変換はRepository層で実施（UIコンポーネントは変換を意識しない）

---

## 🔧 今後守るべき命名ルール

新規実装・リファクタリング時に適用すべきルールです。

### 基本ルール

1. **IDカラム**: `<concept>_id`

   - 例: `rep_id`, `customer_id`, `item_id`, `upload_file_id`

2. **名称カラム**: `<concept>_name`

   - 例: `rep_name`, `customer_name`, `item_name`, `category_name`

3. **日付カラム**: `<purpose>_date`

   - 例: `sales_date`, `slip_date`, `target_from`, `target_to`

4. **タイムスタンプ**: `<event>_at`

   - 例: `created_at`, `updated_at`, `deleted_at`, `scheduled_for`

5. **boolean フラグ**: `is_<state>` / `has_<attribute>` / `can_<action>`

   - 例: `is_deleted`, `is_business`, `has_error`, `can_edit`

6. **集計値**: `total_<metric>` / `avg_<metric>` / `sum_<metric>`

   - 例: `total_amount`, `total_net_weight`, `avg_unit_price`

7. **カウント**: `<target>_count`
   - 例: `line_count`, `slip_count`, `visit_count`, `item_count`

---

### 単位の扱い

**原則**: 単位はカラム名に含めず、ドキュメント・コメントで明記

- **理由**:
  - 国際化対応（`_yen` は日本特有）
  - カラム名の簡潔性
  - 単位変換の柔軟性

**例外**:

- 同じ概念で異なる単位がある場合は明示
  - 例: `weight_kg` vs `weight_ton`、`amount_yen` vs `amount_usd`

**推奨表記**:

```sql
-- Good: ドキュメント化
CREATE TABLE sales (
  amount numeric NOT NULL,  -- 単位: 円
  net_weight numeric NOT NULL  -- 単位: kg
);
COMMENT ON COLUMN sales.amount IS '売上金額（円）';
COMMENT ON COLUMN sales.net_weight IS '正味重量（kg）';

-- Avoid: 単位をカラム名に含める（冗長）
CREATE TABLE sales (
  amount_yen numeric NOT NULL,
  qty_kg numeric NOT NULL
);
```

---

### レイヤー間の命名規則

| レイヤー            | 命名規約     | 例                                      |
| ------------------- | ------------ | --------------------------------------- |
| **DB (PostgreSQL)** | `snake_case` | `rep_id`, `customer_name`, `created_at` |
| **API (Pydantic)**  | `snake_case` | `rep_id`, `customer_name`, `created_at` |
| **FE (TypeScript)** | `camelCase`  | `repId`, `customerName`, `createdAt`    |

**変換ポイント**:

- API → FE: Repository層で snake_case → camelCase
- FE → API: Repository層で camelCase → snake_case

---

## 🚨 最小限の修正候補

現在のコードベースで「最優先で直すべき」箇所を抽出しました。

### 優先度 High: 同一ビュー内での命名不統一

#### 1. TypeScript の snake_case 残存

**問題**: Sales Pivot の MetricEntry で `line_count`, `slip_count`, `unit_price` がsnake_caseのまま

**対象ファイル**:

- `app/frontend/src/features/analytics/sales-pivot/shared/model/types.ts`

**修正内容**:

```typescript
// Before
export interface MetricEntry {
  id: ID;
  name: string;
  amount: number;
  qty: number;
  line_count: number; // ← snake_case
  slip_count: number; // ← snake_case
  count: number;
  unit_price: number | null; // ← snake_case
  dateKey?: YYYYMMDD;
}

// After
export interface MetricEntry {
  id: ID;
  name: string;
  amount: number;
  qty: number;
  lineCount: number; // ← camelCase
  slipCount: number; // ← camelCase
  count: number;
  unitPrice: number | null; // ← camelCase
  dateKey?: YYYYMMDD;
}
```

**影響範囲**:

- `sales-pivot/shared/api/salesPivot.repository.ts` (変換ロジック)
- `sales-pivot/features/**/ui/*.tsx` (UIコンポーネント)
- `sales-pivot/features/**/model/*.ts` (ViewModel)

**推定工数**: 2-3時間

---

#### 2. 営業担当の接頭辞不統一（rep vs salesRep）

**問題**: Sales Pivot は `rep_`, Customer Churn は `salesRep_`

**対象ファイル**:

- `app/backend/core_api/app/presentation/schemas/__init__.py` (LostCustomer)
- `app/backend/core_api/app/infra/adapters/customer_churn/__init__.py`
- `app/backend/core_api/migrations/alembic/versions/20251125_150000000_create_mart_sales_tree_views_v_sales_.py` (v_customer_sales_daily)

**修正内容**:

```python
# Before (Customer Churn API)
class LostCustomer(BaseModel):
    customer_id: str
    customer_name: str
    sales_rep_id: Optional[str]  # ← salesRep
    sales_rep_name: Optional[str]

# After (統一)
class LostCustomer(BaseModel):
    customer_id: str
    customer_name: str
    rep_id: Optional[str]  # ← rep に統一
    rep_name: Optional[str]
```

**SQL修正**:

```sql
-- Before
CREATE OR REPLACE VIEW mart.v_customer_sales_daily AS
SELECT
    sales_date,
    customer_id,
    MAX(customer_name) AS customer_name,
    MAX(rep_id) AS sales_rep_id,  -- ← salesRep
    MAX(rep_name) AS sales_rep_name,
    ...

-- After
CREATE OR REPLACE VIEW mart.v_customer_sales_daily AS
SELECT
    sales_date,
    customer_id,
    MAX(customer_name) AS customer_name,
    MAX(rep_id) AS rep_id,  -- ← rep に統一
    MAX(rep_name) AS rep_name,
    ...
```

**影響範囲**:

- バックエンド: CustomerChurnQueryAdapter, LostCustomer DTO
- フロントエンド: customer-list/shared/infrastructure/customerChurnRepository.ts, UIコンポーネント

**推定工数**: 3-4時間

---

### 優先度 Medium: 金額・重量の単位明示不統一

#### 3. `amount_yen` vs `amount` の混在

**問題**: mart.v_sales_tree_detail_base では `amount_yen` だが、v_customer_sales_daily では `total_amount_yen`

**対象ファイル**:

- `app/backend/core_api/migrations/alembic/versions/7e3d1c5e0036_fix_category_mapping_waste_1_valuable_3.py`
- `app/backend/core_api/migrations/alembic/versions/20251125_150000000_create_mart_sales_tree_views_v_sales_.py`

**修正内容**:

```sql
-- Before (不統一)
CREATE VIEW mart.v_sales_tree_detail_base AS
SELECT
    amount AS amount_yen,  -- ← _yen サフィックス
    ...

CREATE VIEW mart.v_customer_sales_daily AS
SELECT
    SUM(amount_yen) AS total_amount_yen,  -- ← _yen サフィックス
    ...

-- After (統一案1: サフィックス削除)
CREATE VIEW mart.v_sales_tree_detail_base AS
SELECT
    amount,  -- ← サフィックス削除、ドキュメントで単位を明記
    ...

CREATE VIEW mart.v_customer_sales_daily AS
SELECT
    SUM(amount) AS total_amount,  -- ← サフィックス削除
    ...
```

**影響範囲**:

- 全ての売上系API（SalesTree, CustomerChurn）
- フロントエンド全体

**推定工数**: **破壊的変更のため慎重に検討**（1週間以上）

**代替案**: 段階的移行

1. 短期: 新規ビューでは `amount` に統一
2. 中期: 既存ビューは `amount_yen` を維持しつつ、ドキュメント整備
3. 長期: API v2 で `amount` に統一

---

#### 4. `qty_kg` vs `net_weight` の混在

**問題**: 同様に重量カラムの命名が不統一

**修正内容**:

```sql
-- Before
CREATE VIEW mart.v_sales_tree_detail_base AS
SELECT
    net_weight AS qty_kg,  -- ← qty_kg
    ...

-- After
CREATE VIEW mart.v_sales_tree_detail_base AS
SELECT
    net_weight,  -- ← 元カラム名のまま
    ...
```

**影響範囲**: 金額と同様

**推定工数**: 破壊的変更のため慎重に検討

---

### 優先度 Low: ドキュメント整備

#### 5. カラム名の単位をCOMMENTで明記

**対象**: 全テーブル・ビュー

**修正内容**:

```sql
-- テーブル定義にCOMMENT追加
COMMENT ON COLUMN stg.shogun_flash_receive.amount IS '売上金額（単位: 円）';
COMMENT ON COLUMN stg.shogun_flash_receive.net_weight IS '正味重量（単位: kg）';
COMMENT ON COLUMN stg.shogun_flash_receive.unit_price IS '単価（単位: 円/kg）';
```

**推定工数**: 1-2日（Alembicリビジョンとして実装）

---

## 📝 まとめ

### 統一性が高い領域

以下の領域は既に高い統一性を保っています：

- ✅ 顧客ID/名前 (`customer_id`, `customer_name`)
- ✅ 品目ID/名前 (`item_id`, `item_name`)
- ✅ タイムスタンプ (`created_at`, `updated_at`, `deleted_at`)
- ✅ 論理削除 (`is_deleted`, `deleted_by`)
- ✅ ISO週情報 (`iso_year`, `iso_week`, `iso_dow`)
- ✅ 営業日フラグ (`is_business`, `is_holiday`)

### 揺れが大きい領域

以下の領域で命名の揺れが見られます：

- ⚠️ 営業担当: `rep_id` vs `sales_rep_id` (接頭辞の不統一)
- ⚠️ 金額: `amount` vs `amount_yen` vs `total_amount_yen` (単位明示の不統一)
- ⚠️ 重量: `net_weight` vs `qty_kg` vs `qty` (概念の混在)
- ⚠️ 伝票番号: `receive_no` vs `slip_no` (用語の変換)
- ⚠️ TypeScript: snake_case残存 (`line_count`, `slip_count`, `unit_price`)

### 推奨アクション

**即座に実施可能**:

1. TypeScript の snake_case を camelCase に変換
2. Customer Churn API の `sales_rep_*` を `rep_*` に統一
3. 新規実装では本ドキュメントの命名ルールを厳守

**慎重に検討すべき**:

1. `amount_yen` → `amount` の統一（破壊的変更）
2. `qty_kg` → `net_weight` の統一（破壊的変更）
3. API v2 での大規模リファクタリング

**長期的な改善**:

1. 全テーブル・ビューへのCOMMENT追加
2. 命名規約ドキュメントのチーム共有
3. Linter/Pre-commit hookでの命名規約チェック

---

## 🔗 関連ドキュメント

- `docs/db_migration_policy.md` - Alembic マイグレーション方針
- `docs/FSD_ARCHITECTURE_GUIDE.md` - フロントエンドアーキテクチャ
- `docs/SOFT_DELETE_QUICKSTART.md` - 論理削除の実装方針

---

**最終更新**: 2025-11-27  
**更新者**: GitHub Copilot (AI Assistant)
