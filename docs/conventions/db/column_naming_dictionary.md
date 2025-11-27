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

**重要**: 本ドキュメントでは、以下の2つのカラム名マッピングを区別します：
1. **Canonical マッピング** - 今後のmart層で標準とすべき理想的な命名
2. **現行スキーマ** - 既存のmart層で実際に使われている命名（移行前の状態）

---

## 📐 Canonical 命名ルール（今後の標準）

### 基本原則

新規実装・リファクタリング時に適用すべき **canonical（正統的）** な命名ルールです。

1. **IDカラム**: `<concept>_id`
   - 例: `rep_id`, `customer_id`, `item_id`, `vendor_id`
   - **推奨**: `_cd` → `_id` に統一（段階的に移行）

2. **名称カラム**: `<concept>_name`
   - 例: `rep_name`, `customer_name`, `item_name`, `vendor_name`

3. **日付カラム**: `<purpose>_date`
   - 例: `sales_date`, `slip_date`, `payment_date`

4. **タイムスタンプ**: `<event>_at`
   - 例: `created_at`, `updated_at`, `deleted_at`

5. **boolean フラグ**: `is_<state>`
   - 例: `is_deleted`, `is_business`

6. **集計値**: `total_<metric>_<unit>`
   - 例: `total_amount_yen`, `total_net_weight_kg`
   - **必須**: 単位サフィックスを付与（`_yen`, `_kg`）

7. **カウント**: `<target>_count`
   - 例: `line_count`, `slip_count`, `visit_count`

8. **単位の扱い**:
   - **原則**: カラム名に単位サフィックスを付与する（`_yen`, `_kg`, `_yen_per_kg`）
   - **例**: `amount_yen`, `net_weight_kg`, `unit_price_yen_per_kg`
   - **理由**: 
     - BI ツール・CSV などで単位が一目で分かる
     - 複数通貨・複数単位の併用時に拡張しやすい
   - **補足**: PostgreSQL COMMENT、ドキュメントでも単位を明記

---

## 📋 カラム名マッピング辞書（raw/stg → mart canonical）

以下の表は、**今後の mart 層で標準とすべき canonical（正統的）な命名**を示します。

| 概念 | raw/stg カラム名 | mart canonical カラム名 | 単位 | 説明 |
|------|-----------------|------------------------|------|------|
| **営業担当者ID** | `sales_staff_cd` | `rep_id` | - | 営業担当者の識別子 |
| **営業担当者名** | `sales_staff_name` | `rep_name` | - | 営業担当者の氏名 |
| **顧客ID** | `client_cd` | `customer_id` | - | 顧客の識別子 |
| **顧客名** | `client_name` | `customer_name` | - | 顧客の正式名称 |
| **仕入先ID** | `vendor_cd` | `vendor_id` | - | 仕入先の識別子（顧客とは独立した vendor 概念として扱う） |
| **仕入先名** | `vendor_name` | `vendor_name` | - | 仕入先の正式名称 |
| **品目ID** | `item_cd` | `item_id` | - | 品目コード |
| **品目名** | `item_name` | `item_name` | - | 品目名（変更なし） |
| **集計品目ID** | `aggregate_item_cd` | `aggregate_item_id` | - | 集計品目コード |
| **集計品目名** | `aggregate_item_name` | `aggregate_item_name` | - | 集計品目名（変更なし） |
| **伝票番号** | `receive_no` | `slip_no` | - | 伝票番号（受入番号→汎用伝票番号） |
| **伝票区分CD** | `slip_type_cd` | `slip_type_cd` | - | 伝票区分コード（変更なし） |
| **伝票区分名** | `slip_type_name` | `slip_type_name` | - | 伝票区分名（変更なし） |
| **伝票日** | `slip_date` | `slip_date` | - | 伝票日付（変更なし） |
| **売上日** | `sales_date` | `sales_date` | - | 売上日（変更なし） |
| **入金日** | `payment_date` | `payment_date` | - | 入金日（変更なし） |
| **金額** | `amount` | `amount_yen` | 円 | 売上金額（単位：円） |
| **正味重量** | `net_weight` | `net_weight_kg` | kg | 正味重量（単位：kg） |
| **単価** | `unit_price` | `unit_price_yen_per_kg` | 円/kg | 単価（単位：円/kg） |
| **カテゴリCD** | `category_cd` | `category_cd` | - | カテゴリコード（1=廃棄物, 3=有価物） |
| **カテゴリ名** | `category_name` | `category_name` | - | カテゴリ名 |
| **カテゴリ種別** | (CASE式) | `category_kind` | - | enum string（'waste'/'valuable'） |
| **is_deleted** | `is_deleted` | `is_deleted` | - | 論理削除フラグ |
| **deleted_at** | `deleted_at` | `deleted_at` | - | 削除日時（UTC） |
| **deleted_by** | `deleted_by` | `deleted_by` | - | 削除実行者 |
| **created_at** | `created_at` | `created_at` | - | 作成日時（UTC） |

**方針コメント**:

1. **仕入先（vendor）の扱い**:
   - raw/stg 層の `vendor_cd` / `vendor_name` は、mart 層でも `vendor_id` / `vendor_name` にマッピングする
   - 顧客（customer）とは別の概念として「仕入先（vendor）」を保持し、customer_* に統合しない
   - 取引先全体をひとまとめで扱いたい場合は、ビュー側で以下のように対応する：
     - customer_* と vendor_* を UNION して `partner_id` / `partner_name` を生成する
     - 派生レイヤーで対応する方針とし、canonical カラム名としては vendor_* / customer_* を維持する

2. **金額・重量の単位**:
   - canonical では、金額・重量・単価に **単位サフィックスを付与** する
     - 例: `amount_yen`, `net_weight_kg`, `unit_price_yen_per_kg`
   - 理由:
     - COMMENT が見えない BI ツール・CSV などでも、単位が一目で分かるようにするため
     - 将来、複数通貨・複数単位（例: `amount_usd`, `net_weight_ton`）を併用する際に拡張しやすくするため
   - PostgreSQL の COMMENT および本ドキュメントでも、正式な単位を明示して管理する

3. **カテゴリの扱い**:
   - `category_cd`: 内部処理用の数値コード（1, 3）
   - `category_kind`: API公開用のenum string（'waste', 'valuable'）
   - 両方を維持する現状が妥当

---

## 📊 現行DBスキーマとcanonical命名のギャップ一覧

以下は、**現行のmart層で実際に使われているカラム名** vs **canonical推奨名** のギャップです。

| スキーマ | テーブル/ビュー | 現行カラム名 | canonical推奨名 | ギャップ種別 | 対応方針 |
|----------|----------------|-------------|----------------|------------|---------|
| **mart** | **v_sales_tree_detail_base** | `amount_yen` | `amount_yen` | ✅ canonical準拠 | 対応不要 |
| mart | v_sales_tree_detail_base | `qty_kg` | `net_weight_kg` | カラム名の用語統一 | 中期: `qty_kg` → `net_weight_kg` に統一 |
| mart | v_customer_sales_daily | `total_amount_yen` | `total_amount_yen` | ✅ canonical準拠 | 対応不要 |
| mart | v_customer_sales_daily | `total_qty_kg` | `total_net_weight_kg` | カラム名の用語統一 | 中期: `total_qty_kg` → `total_net_weight_kg` に統一 |
| **mart** | **v_receive_daily** | `unit_price_yen_per_kg` | `unit_price_yen_per_kg` | ✅ canonical準拠 | 対応不要 |
| mart | v_receive_weekly | `unit_price_yen_per_kg` | `unit_price_yen_per_kg` | ✅ canonical準拠 | 対応不要 |
| mart | v_receive_monthly | `unit_price_yen_per_kg` | `unit_price_yen_per_kg` | ✅ canonical準拠 | 対応不要 |
| **stg** | **shogun_flash_receive** | `vendor_id` | `vendor_id` | ✅ canonical準拠 | 対応済み（2025-11-27） |
| stg | shogun_flash_receive | `vendor_name` | `vendor_name` | ✅ canonical準拠 | 対応不要 |
| stg | shogun_final_receive | `vendor_id` | `vendor_id` | ✅ canonical準拠 | 対応済み（2025-11-27） |
| stg | shogun_final_receive | `vendor_name` | `vendor_name` | ✅ canonical準拠 | 対応不要 |
| **ref** | **v_sales_rep** | `rep_id` | `rep_id` | ✅ canonical準拠 | 対応済み（2025-11-27） |
| **mart** | **v_customer_sales_daily** | `rep_id` | `rep_id` | ✅ canonical準拠 | 対応済み（2025-11-27） |

**ギャップ種別の凡例**:
- **✅ canonical準拠**: 既に理想的な命名になっている
- **カラム名の用語統一**: 概念は同じだがカラム名の用語が異なる（例: `qty` vs `net_weight`）
- **カラム名サフィックス統一**: `_cd` → `_id` への統一

**対応の優先度**:

1. **Priority High（既対応）**: 
   - ✅ `rep_id`/`rep_name` への統一（2025-11-27完了）
   - ✅ `vendor_cd` → `vendor_id` への統一（2025-11-27完了）
   - ✅ カラムCOMMENTでの単位明記（2025-11-27完了）
   - ✅ 金額・重量・単価の単位サフィックス付き命名（canonical と現行が一致）

2. **Priority Medium（段階的対応）**: 
   - `qty_kg` → `net_weight_kg` への統一（用語の統一、優先度: 低）
   - **推奨**: 新規ビューでは canonical 採用、既存ビューは段階的に移行

3. **Priority Low（長期課題）**: 
   - 追加のビュー・テーブルへのCOMMENT追加
   - ドキュメントの継続的な更新

---

## 🎯 Concept Clustering（概念別カラム名グループ - 現行スキーマ）

以下のセクションは、**現行の実装で実際に使われているカラム名**を示します。canonical との差異は上記の「ギャップ一覧」を参照してください。

### 1. 営業担当 (Sales Representative)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **営業ID** | **raw/stg**: `sales_staff_cd` (integer)<br>**mart**: `rep_id` (✅ canonical準拠)<br>**API**: `rep_id` (int)<br>**FE**: `repId` (camelCase) | `rep_id` |
| **営業名** | **raw/stg**: `sales_staff_name` (text)<br>**mart**: `rep_name` (✅ canonical準拠)<br>**API**: `rep_name` (str)<br>**FE**: `repName` | `rep_name` |

**ステータス**: ✅ **2025-11-27にcanonical準拠へ移行完了**

---

### 2. 顧客 (Customer)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **顧客ID** | **raw/stg**: `client_cd` (text)<br>**mart**: `customer_id` (✅ canonical準拠)<br>**API**: `customer_id` (str)<br>**FE**: `customerId` | `customer_id` |
| **顧客名** | **raw/stg**: `client_name` (text)<br>**mart**: `customer_name` (✅ canonical準拠)<br>**API**: `customer_name` (str)<br>**FE**: `customerName` | `customer_name` |

**ステータス**: ✅ **canonical準拠**

---

### 3. 品目 (Item)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **品目ID** | **raw/stg**: `item_cd` (integer)<br>**mart**: `item_id` (✅ canonical準拠)<br>**API**: `item_id` (int)<br>**FE**: `itemId` | `item_id` |
| **品目名** | **全レイヤー**: `item_name` (✅ canonical準拠) | `item_name` |

**ステータス**: ✅ **canonical準拠**

---

### 4. 金額 (Amount)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **金額（円）** | **raw/stg**: `amount` (numeric)<br>**mart**: `amount_yen` (✅ canonical準拠)<br>**API**: `amount` (float)<br>**FE**: `amount` (number) | `amount_yen` |
| **合計金額** | **mart**: `total_amount_yen` (✅ canonical準拠)<br>**API/FE**: 変換済み | `total_amount_yen` |

**ステータス**: ✅ **mart層はcanonical準拠**（API/FEでは単位サフィックス省略）

**補足**:
- mart層では単位を明示した `amount_yen` を使用（canonical準拠）
- API/FE層では簡潔性のため `amount` に変換（ドメイン層での用途に応じて柔軟に対応）

---

### 5. 数量・重量 (Quantity / Weight)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **正味重量（kg）** | **raw/stg**: `net_weight` (numeric)<br>**mart**: `qty_kg` (⚠️ 用語の違い)<br>**API**: `qty` (float)<br>**FE**: `qty` (number) | `net_weight_kg` |
| **合計正味重量** | **mart**: `total_qty_kg` (⚠️ 用語の違い)<br>**API/FE**: 変換済み | `total_net_weight_kg` |

**ステータス**: ⚠️ **mart層で用語のギャップあり**（`qty` vs `net_weight`）

**段階的移行案**:
1. 短期: 現状維持（`qty_kg` は実質 net_weight を指す、COMMENT で明記済み）
2. 中期: 新規ビューでは `net_weight_kg` を採用
3. 長期: 既存ビューを `net_weight_kg` に統一（用語の一貫性向上）

---

### 6. 伝票番号 (Slip Number)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **伝票番号** | **raw/stg**: `receive_no` (integer)<br>**mart**: `slip_no` (✅ canonical準拠)<br>**API/FE**: `slipNo` | `slip_no` |

**ステータス**: ✅ **canonical準拠**

---

### 7. 日付 (Date)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **売上日** | **全レイヤー**: `sales_date` (✅ canonical準拠) | `sales_date` |
| **伝票日** | **全レイヤー**: `slip_date` (✅ canonical準拠) | `slip_date` |
| **入金日** | **全レイヤー**: `payment_date` (✅ canonical準拠) | `payment_date` |

**ステータス**: ✅ **canonical準拠**

**補足**:
- **業務日付**: `sales_date` (売上日)、`slip_date` (伝票日)、`payment_date` (入金日)
- **カレンダー日付**: `ddate` (ref.v_calendar_classified 等で使用)
- **汎用日付**: `date` (集計結果等で使用)
- **注意**: `COALESCE(sales_date, slip_date)` のような複合ロジックが存在するため、用途に応じて使い分けが必要

---

### 8. 件数・カウント (Count)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **明細行数** | **全レイヤー**: `line_count` (✅ canonical準拠) | `line_count` |
| **伝票数（台数）** | **全レイヤー**: `slip_count` (✅ canonical準拠) | `slip_count` |
| **訪問回数** | **全レイヤー**: `visit_count` (✅ canonical準拠) | `visit_count` |

**ステータス**: ✅ **canonical準拠**

---

### 9. 単価 (Unit Price)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **単価（円/kg）** | **raw/stg**: `unit_price` (numeric)<br>**mart**: `unit_price_yen_per_kg` (✅ canonical準拠)<br>**API/FE**: `unit_price` | `unit_price_yen_per_kg` |

**ステータス**: ✅ **mart層はcanonical準拠**（API/FEでは単位サフィックス省略）

**補足**:
- mart層では単位を明示した `unit_price_yen_per_kg` を使用（canonical準拠）
- API/FE層では簡潔性のため `unit_price` に変換

---

### 10. カテゴリ (Category)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **カテゴリコード** | **全レイヤー**: `category_cd` (✅ canonical準拠) | `category_cd` |
| **カテゴリ名** | **全レイヤー**: `category_name` (✅ canonical準拠) | `category_name` |
| **カテゴリ種別** | **mart**: `category_kind` (✅ canonical準拠、enum string) | `category_kind` |

**ステータス**: ✅ **canonical準拠**

**方針**: 
- `category_cd`: 内部処理用の数値コード（1=廃棄物, 3=有価物）
- `category_kind`: API公開用のenum string（'waste', 'valuable'）

---

### 11. タイムスタンプ (Timestamps)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **作成日時** | **全レイヤー**: `created_at` (✅ canonical準拠) | `created_at` |
| **更新日時** | **全レイヤー**: `updated_at` (✅ canonical準拠) | `updated_at` |
| **削除日時** | **全レイヤー**: `deleted_at` (✅ canonical準拠) | `deleted_at` |

**ステータス**: ✅ **canonical準拠**

---

### 12. 論理削除フラグ (Soft Delete)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **削除フラグ** | **全レイヤー**: `is_deleted` (✅ canonical準拠) | `is_deleted` |
| **削除実行者** | **全レイヤー**: `deleted_by` (✅ canonical準拠) | `deleted_by` |

**ステータス**: ✅ **canonical準拠**

---

### 13. アップロード追跡 (Upload Tracking)

| 概念 | 現行の使用状況 | canonical |
|---|---|---|
| **アップロードファイルID** | **全レイヤー**: `upload_file_id` (✅ canonical準拠) | `upload_file_id` |
| **元行番号** | **全レイヤー**: `source_row_no` (✅ canonical準拠) | `source_row_no` |

**ステータス**: ✅ **canonical準拠**

---

## 📐 レイヤー別命名方針（canonical基準）

### 1. raw / stg 層（データソース層）

**方針**: 外部システム・CSV由来の名前をそのまま維持

- **理由**: データの出所が明確、元データとの対応関係が分かりやすい、変換ロジックの追跡が容易
- **例**: `sales_staff_cd`, `client_cd`, `item_cd`, `receive_no`, `amount`, `net_weight`
- **ルール**: 型変換のみ実施、カラム名の変更は行わない

---

### 2. mart 層（ビジネスロジック層）

**方針**: ドメイン駆動の **canonical 名** に統一

- **理由**: ビジネスドメインの用語に合わせる、単位の明示、拡張性の確保
- **例**: `rep_id`, `customer_id`, `vendor_id`, `item_id`, `slip_no`, `amount_yen`, `net_weight_kg`, `unit_price_yen_per_kg`
- **ルール**:
  - IDは `<concept>_id` 形式
  - 名称は `<concept>_name` 形式
  - 日付は `<purpose>_date` 形式
  - タイムスタンプは `<event>_at` 形式
  - 論理フラグは `is_<state>` 形式
  - 集計値は `total_<metric>_<unit>` 形式（**単位サフィックス必須**）
  - 金額・重量・単価は単位サフィックス付き（`_yen`, `_kg`, `_yen_per_kg`）

---

### 3. API層（Pydantic / FastAPI）

**方針**: mart層から単位サフィックスを除いたシンプルな名前に変換

- **理由**: Python規約（PEP 8）準拠、APIの簡潔性、型安全性
- **例**:
```python
class MetricEntry(BaseModel):
    id: str
    name: str
    amount: float           # mart: amount_yen
    net_weight: float       # mart: net_weight_kg
    line_count: int
    slip_count: int
    unit_price: Optional[float]  # mart: unit_price_yen_per_kg
```
- **ルール**: mart層の単位サフィックスを省略、ドキュメントで単位を明記

---

### 4. FE層（TypeScript / React）

**方針**: camelCaseに変換し、JavaScript規約に準拠

- **理由**: JavaScript/TypeScript標準規約、React等エコシステムとの一貫性
- **例**:
```typescript
interface MetricEntry {
  id: string;
  name: string;
  amount: number;          // API: amount → mart: amount_yen
  netWeight: number;       // API: net_weight → mart: net_weight_kg
  lineCount: number;
  slipCount: number;
  unitPrice: number | null; // API: unit_price → mart: unit_price_yen_per_kg
}
```
- **ルール**: API受信時に snake_case → camelCase 変換（Repository層で実施）

---

## 🔧 今後守るべき命名ルール（canonical基準）

新規実装・リファクタリング時に適用すべきルールです。

### 基本ルール

1. **IDカラム**: `<concept>_id`
   - 例: `rep_id`, `customer_id`, `item_id`

2. **名称カラム**: `<concept>_name`
   - 例: `rep_name`, `customer_name`, `item_name`

3. **日付カラム**: `<purpose>_date`
   - 例: `sales_date`, `slip_date`, `payment_date`

4. **タイムスタンプ**: `<event>_at`
   - 例: `created_at`, `updated_at`, `deleted_at`

5. **boolean フラグ**: `is_<state>`
   - 例: `is_deleted`, `is_business`

6. **集計値**: `total_<metric>_<unit>` （**単位サフィックス必須**）
   - 例: `total_amount_yen`, `total_net_weight_kg`

7. **カウント**: `<target>_count`
   - 例: `line_count`, `slip_count`, `visit_count`

---

### 単位の扱い（canonical方針）

**原則**: 単位はカラム名に明示し、BIツールやCSV出力時の可読性を確保

- **理由**: PostgreSQL COMMENTはBIツールで不可視、CSV出力時に単位が分からない、将来の多通貨・多単位対応
- **推奨サフィックス**: `_yen`, `_kg`, `_yen_per_kg`
- **例外**: 同じコンテキストで単位が自明な場合のみ省略可能（例: カウント系）

**推奨表記**:
```sql
-- Good: canonical方式（単位サフィックス付き）
CREATE TABLE sales (
  amount_yen numeric NOT NULL,          -- 売上金額（単位明示）
  net_weight_kg numeric NOT NULL,       -- 正味重量（単位明示）
  unit_price_yen_per_kg numeric         -- 単価（単位明示）
);
COMMENT ON COLUMN sales.amount_yen IS '売上金額（円）';
COMMENT ON COLUMN sales.net_weight_kg IS '正味重量（kg）';

-- Avoid: 単位サフィックスなし（BIツール・CSV出力時に単位不明）
CREATE TABLE sales (
  amount numeric NOT NULL,
  net_weight numeric NOT NULL,
  unit_price numeric
);
```

**API/FE層での扱い**:
- API層: 単位サフィックスを省略 (`amount`, `net_weight`, `unit_price`)
- FE層: camelCase変換 (`amount`, `netWeight`, `unitPrice`)
- ドキュメント（OpenAPI/JSDoc）で単位を明記

---

### レイヤー間の命名規則

| レイヤー | 命名規約 | 例 |
|---|---|---|
| **DB (PostgreSQL)** | `snake_case` + 単位サフィックス | `rep_id`, `customer_name`, `amount_yen`, `net_weight_kg` |
| **API (Pydantic)** | `snake_case` （単位省略） | `rep_id`, `customer_name`, `amount`, `net_weight` |
| **FE (TypeScript)** | `camelCase` （単位省略） | `repId`, `customerName`, `amount`, `netWeight` |

**変換ポイント**: 
- API → FE: Repository層で snake_case → camelCase
- FE → API: Repository層で camelCase → snake_case
- mart → API: 単位サフィックス削除（型定義とドキュメントで補完）

---

## 📝 まとめ

### ✅ canonical準拠が完了している領域

以下の領域は既に canonical 命名に統一されています：

- ✅ 営業担当ID/名前 (`rep_id`, `rep_name`) - 2025-11-27対応完了
- ✅ 顧客ID/名前 (`customer_id`, `customer_name`)
- ✅ 品目ID/名前 (`item_id`, `item_name`)
- ✅ 伝票番号 (`slip_no`)
- ✅ 日付 (`sales_date`, `slip_date`, `payment_date`)
- ✅ カウント (`line_count`, `slip_count`, `visit_count`)
- ✅ カテゴリ (`category_cd`, `category_name`, `category_kind`)
- ✅ タイムスタンプ (`created_at`, `updated_at`, `deleted_at`)
- ✅ 論理削除 (`is_deleted`, `deleted_by`)
- ✅ アップロード追跡 (`upload_file_id`, `source_row_no`)
- ✅ 金額: `amount_yen` - mart層で単位サフィックス付き canonical 準拠
- ✅ 単価: `unit_price_yen_per_kg` - mart層で単位サフィックス付き canonical 準拠
- ✅ 仕入先: `vendor_id` - stg層で `_cd` → `_id` 統一完了（2025-11-27）

### ⚠️ ギャップが残っている領域

以下の領域で canonical とのギャップがあります（詳細は「ギャップ一覧」参照）：

- ⚠️ 重量: `qty_kg` → `net_weight_kg`（用語統一の必要性、優先度: 低）

### 推奨アクション

**即座に実施可能**（リスク低）:
1. 新規ビュー/テーブルは canonical 命名を採用
2. 本ドキュメントをチーム内で共有・周知
3. コードレビュー時に canonical 準拠をチェック

**慎重に検討すべき**（破壊的変更）:
1. `qty_kg` → `net_weight_kg` の統一（API/FEに影響、優先度: 低）

**対応方針**:
- 短期: 単位サフィックス付き canonical 方針を新規開発で採用
- 中期: `qty_kg` → `net_weight_kg` 検討
- 長期: 既存ビューの用語統一（破壊的変更のため計画的に実施）

---

## 🔗 関連ドキュメント

- `docs/conventions/20251127_webapp_development_conventions_db.md` - DB設計・マイグレーション規約
- `docs/db_migration_policy.md` - Alembic マイグレーション方針
- `docs/FSD_ARCHITECTURE_GUIDE.md` - フロントエンドアーキテクチャ
- `docs/SOFT_DELETE_QUICKSTART.md` - 論理削除の実装方針

---

**最終更新**: 2025-11-27  
**更新内容**: canonical命名ルールの明確化、raw/stg → mart マッピング辞書の追加、現行スキーマとのギャップ一覧の作成  
**更新者**: GitHub Copilot (AI Assistant)
