# reserve_daily_manual に customer_count列追加＋フロント入力3項目化

**作成日**: 2025-12-19  
**目的**: 固定客数（企業数）を予約表手入力で保存できるようにし、フロント入力を3項目に変更

---

## 0. 事前調査結果

### 0.1 現状のDDL（stg.reserve_daily_manual）

```sql
Table "stg.reserve_daily_manual"
    Column    |           Type           | Nullable |      Default      | Description
--------------+--------------------------+----------+-------------------+-------------
 reserve_date | date                     | not null |                   | 予約日（PK）
 total_trucks | integer                  | not null | 0                 | 合計台数
 fixed_trucks | integer                  | not null | 0                 | 固定客台数
 note         | text                     |          |                   | 
 created_by   | text                     |          |                   | 
 updated_by   | text                     |          |                   | 
 created_at   | timestamp with time zone | not null | CURRENT_TIMESTAMP | 
 updated_at   | timestamp with time zone | not null | CURRENT_TIMESTAMP | 
 deleted_at   | timestamp with time zone |          |                   | 論理削除日時
 deleted_by   | text                     |          |                   | 削除実行者

Indexes:
    "reserve_daily_manual_pkey" PRIMARY KEY, btree (reserve_date)
    "idx_reserve_daily_manual_not_deleted" btree (reserve_date) WHERE deleted_at IS NULL

Check constraints:
    "chk_fixed_trucks_non_negative" CHECK (fixed_trucks >= 0)
    "chk_fixed_trucks_not_exceed_total" CHECK (fixed_trucks <= total_trucks)
    "chk_total_trucks_non_negative" CHECK (total_trucks >= 0)
```

**現状の入力項目**:
- `total_trucks` (integer): 合計台数
- `fixed_trucks` (integer): 固定客台数

**追加する列**:
- `total_customer_count` (integer): 予約企業数
- `fixed_customer_count` (integer): 固定客企業数

### 0.2 現状のView定義（mart.v_reserve_daily_features）

**出力列**:
1. `date` (date): 予約日
2. `total_customer_count` (bigint): 予約企業数（stg.reserve_customer_dailyから算出）
3. `fixed_customer_count` (bigint): 固定客企業数（同上）
4. `fixed_customer_ratio` (numeric): 固定客企業比率（fixed/totalで算出）
5. `reserve_trucks` (bigint): 予約台数（manual優先、なければcustomer_aggから台数合計）
6. `reserve_fixed_trucks` (bigint): 固定客台数（同上）
7. `reserve_fixed_trucks_ratio` (numeric): 固定客台数比率（reserve_fixed_trucks/reserve_trucks）
8. `source` (text): データソース（'manual' or 'customer_agg'）

**ロジック**:
1. `customer_agg` CTE: stg.reserve_customer_dailyから企業数・台数を集計
2. `manual_data` CTE: stg.reserve_daily_manualから手入力データ取得（**現状はcustomer_count列なし、NULL固定**）
3. `combined` CTE: manual優先でFULL JOIN（台数はmanual優先、企業数はcustomer_aggのみ）
4. 最終SELECT: 比率計算＋出力

**重要な発見**:
- 現状のViewでは、`manual_data`のcustomer_count列が**NULL固定**
  ```sql
  SELECT reserve_daily_manual.reserve_date AS date,
      NULL::bigint AS total_customer_count,    ← 常にNULL
      NULL::bigint AS fixed_customer_count,    ← 常にNULL
      reserve_daily_manual.total_trucks AS reserve_trucks,
      reserve_daily_manual.fixed_trucks AS reserve_fixed_trucks,
      'manual'::text AS source
  FROM stg.reserve_daily_manual
  WHERE reserve_daily_manual.deleted_at IS NULL
  ```
- **COALESCE(m.total_customer_count, c.total_customer_count)** で、manual入力があっても企業数はcustomer_aggから取得

---

## 1. 方針

### 1.1 DB変更

**stg.reserve_daily_manual に2列追加**:
```sql
ALTER TABLE stg.reserve_daily_manual
ADD COLUMN total_customer_count integer NULL,
ADD COLUMN fixed_customer_count integer NULL;

-- 制約追加（後方互換のためNULL許可）
ALTER TABLE stg.reserve_daily_manual
ADD CONSTRAINT chk_total_customer_count_non_negative 
CHECK (total_customer_count IS NULL OR total_customer_count >= 0);

ALTER TABLE stg.reserve_daily_manual
ADD CONSTRAINT chk_fixed_customer_count_non_negative 
CHECK (fixed_customer_count IS NULL OR fixed_customer_count >= 0);

ALTER TABLE stg.reserve_daily_manual
ADD CONSTRAINT chk_fixed_customer_count_not_exceed_total 
CHECK (fixed_customer_count IS NULL OR total_customer_count IS NULL OR fixed_customer_count <= total_customer_count);
```

**mart.v_reserve_daily_features を更新**:
```sql
-- manual_data CTEを修正
manual_data AS (
    SELECT 
        reserve_date AS date,
        total_customer_count,  -- ← NULLから実値に変更
        fixed_customer_count,  -- ← NULLから実値に変更
        total_trucks AS reserve_trucks,
        fixed_trucks AS reserve_fixed_trucks,
        'manual'::text AS source
    FROM stg.reserve_daily_manual
    WHERE deleted_at IS NULL
)

-- combined CTEを修正（manual優先）
SELECT 
    COALESCE(m.date, c.date) AS date,
    COALESCE(m.total_customer_count, c.total_customer_count, 0) AS total_customer_count,  -- ← manual優先
    COALESCE(m.fixed_customer_count, c.fixed_customer_count, 0) AS fixed_customer_count,  -- ← manual優先
    ...
FROM manual_data m
FULL JOIN customer_agg c ON m.date = c.date
```

### 1.2 API変更

**Request DTO** (例: ReserveDailyManualCreateDto):
```typescript
{
  reserveDate: string;      // YYYY-MM-DD
  totalTrucks: number;       // 合計台数
  totalCustomerCount: number; // 予約企業数 (新規)
  fixedCustomerCount: number; // 固定客企業数 (新規)
}
```

**Repository（UPSERT）**:
```sql
INSERT INTO stg.reserve_daily_manual (
    reserve_date, 
    total_trucks, 
    total_customer_count,  -- ← 追加
    fixed_customer_count,  -- ← 追加
    created_by, 
    updated_by
)
VALUES (
    :reserve_date, 
    :total_trucks, 
    :total_customer_count, 
    :fixed_customer_count, 
    :user_id, 
    :user_id
)
ON CONFLICT (reserve_date) 
DO UPDATE SET
    total_trucks = EXCLUDED.total_trucks,
    total_customer_count = EXCLUDED.total_customer_count,  -- ← 追加
    fixed_customer_count = EXCLUDED.fixed_customer_count,  -- ← 追加
    updated_by = EXCLUDED.updated_by,
    updated_at = CURRENT_TIMESTAMP;
```

### 1.3 フロント変更

**入力フォーム（3項目）**:
1. **合計台数** (totalTrucks) - number input
2. **予約企業数** (totalCustomerCount) - number input (新規)
3. **固定客企業数** (fixedCustomerCount) - number input (新規)

**バリデーション**:
- `totalTrucks >= 0`
- `totalCustomerCount >= 0`
- `fixedCustomerCount >= 0`
- `fixedCustomerCount <= totalCustomerCount`

**後方互換**:
- `fixed_trucks`列は残す（既存データ維持のため）
- UIからは削除（新3項目のみ）

---

## 2. 実装詳細（TBD - 次のステップで記入）

### 2.1 Alembic Migration

**ファイル名**: `20251219_002_add_customer_count_to_reserve_daily_manual.py`

**upgrade()**:
```python
# TBD
```

**downgrade()**:
```python
# TBD
```

### 2.2 View更新

**ファイル名**: `20251219_003_update_v_reserve_daily_features_with_manual_customer_count.py`

**upgrade()**:
```python
# TBD
```

### 2.3 API修正

**ファイル**: `app/backend/core_api/app/api/routes/reserve.py`

**変更内容**:
```python
# TBD
```

### 2.4 フロント修正

**ファイル**: `app/frontend/src/features/reserve/components/ReserveDailyManualForm.tsx`

**変更内容**:
```typescript
// TBD
```

---

## 3. テスト計画（TBD）

### 3.1 DB確認SQL

```sql
-- 列が増えていること
\d+ stg.reserve_daily_manual;

-- viewが新列を返すこと
SELECT 
    reserve_date, 
    total_trucks, 
    total_customer_count, 
    fixed_customer_count,
    source
FROM mart.v_reserve_daily_features
ORDER BY reserve_date DESC
LIMIT 10;
```

### 3.2 API確認

```bash
# curl or Postmanで投稿→取得
curl -X POST http://localhost:8000/api/reserve/daily-manual \
  -H "Content-Type: application/json" \
  -d '{
    "reserveDate": "2025-12-25",
    "totalTrucks": 100,
    "totalCustomerCount": 50,
    "fixedCustomerCount": 30
  }'
```

### 3.3 画面確認

1. 予約表ページを開く
2. 3項目（台数、企業数、固定客数）が表示されること
3. 入力→保存→再取得で同じ値が返ること
4. カレンダーに反映されること

---

## 4. 変更ファイル一覧（TBD）

### 4.1 Backend

- [ ] `app/backend/core_api/migrations_v2/alembic/versions/20251219_002_add_customer_count_to_reserve_daily_manual.py`
- [ ] `app/backend/core_api/migrations_v2/alembic/versions/20251219_003_update_v_reserve_daily_features_with_manual_customer_count.py`
- [ ] `app/backend/core_api/app/api/routes/reserve.py`
- [ ] `app/backend/core_api/app/domain/reserve/reserve_daily_manual.py` (Domain Model)
- [ ] `app/backend/core_api/app/infra/repositories/reserve_repository.py`

### 4.2 Frontend

- [ ] `app/frontend/src/features/reserve/types/reserveDailyManual.ts`
- [ ] `app/frontend/src/features/reserve/components/ReserveDailyManualForm.tsx`
- [ ] `app/frontend/src/features/reserve/viewModel/useReserveDailyManualViewModel.ts`

### 4.3 Docs

- [ ] `docs/development/20251219_reserve_manual_customer_cols.md` (本ファイル)

---

## 5. 次のアクション

1. ✅ 事前調査完了（DDL、View定義確認）
2. ⏳ Alembic migration作成（2列追加）
3. ⏳ View更新（manual優先ロジック）
4. ⏳ API/Repository/DTO修正
5. ⏳ フロント入力フォーム3項目化
6. ⏳ テスト/確認SQL実行
7. ⏳ レポート完成（本ファイル更新）

---

**作成者**: GitHub Copilot (Claude Sonnet 4.5)  
**レビュー**: 未実施  
**承認**: 未実施
