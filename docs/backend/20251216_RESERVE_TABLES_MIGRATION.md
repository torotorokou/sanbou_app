# 予約系テーブル追加マイグレーション

**日付**: 2025-12-16  
**ブランチ**: feature/add-reserve-tables  
**実装者**: Alembic migrations_v2

---

## 概要

Alembicを使って予約データ基盤（stg 2テーブル + mart 1ビュー）をベイビーステップで追加しました。

### 追加されたオブジェクト

1. **stg.reserve_daily_manual** - ユーザー手入力の日次予約合計
2. **stg.reserve_customer_daily** - 顧客ごとの予約一覧
3. **mart.v_reserve_daily_for_forecast** - 予測用の予約日次ビュー

---

## Phase 1: stg.reserve_daily_manual

### マイグレーションファイル
- `20251216_001_add_reserve_daily_manual.py`
- Revision ID: `1d57288e056c`

### テーブル仕様

```sql
CREATE TABLE stg.reserve_daily_manual (
    reserve_date date PRIMARY KEY,
    total_trucks integer NOT NULL DEFAULT 0,
    fixed_trucks integer NOT NULL DEFAULT 0,
    note text,
    created_by text,
    updated_by text,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_total_trucks_non_negative CHECK (total_trucks >= 0),
    CONSTRAINT chk_fixed_trucks_non_negative CHECK (fixed_trucks >= 0),
    CONSTRAINT chk_fixed_trucks_not_exceed_total CHECK (fixed_trucks <= total_trucks)
);
```

### 特徴
- PK: `reserve_date` (date)
- manual入力は3項目のみ: `reserve_date`, `total_trucks`, `fixed_trucks`
- `fixed_ratio` は計算しない（VIEW側で計算）
- CHECK制約で整合性を保証

---

## Phase 2: stg.reserve_customer_daily

### マイグレーションファイル
- `20251216_002_add_reserve_customer_daily.py`
- Revision ID: `6807c2215b75`

### テーブル仕様

```sql
CREATE TABLE stg.reserve_customer_daily (
    id bigserial PRIMARY KEY,
    reserve_date date NOT NULL,
    customer_cd text NOT NULL,
    customer_name text,
    planned_trucks integer NOT NULL DEFAULT 0,
    is_fixed_customer boolean NOT NULL DEFAULT false,
    note text,
    created_by text,
    updated_by text,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_planned_trucks_non_negative CHECK (planned_trucks >= 0),
    CONSTRAINT uq_reserve_customer_daily_date_customer UNIQUE (reserve_date, customer_cd)
);

CREATE INDEX idx_reserve_customer_daily_date 
ON stg.reserve_customer_daily (reserve_date);

CREATE INDEX idx_reserve_customer_daily_date_fixed 
ON stg.reserve_customer_daily (reserve_date, is_fixed_customer);
```

### 特徴
- 顧客ごとの予約を管理
- UNIQUE制約: `(reserve_date, customer_cd)`
- インデックス: 日付検索、固定客フィルタ用

---

## Phase 3: mart.v_reserve_daily_for_forecast

### マイグレーションファイル
- `20251216_003_add_v_reserve_daily_for_forecast.py`
- Revision ID: `11e8fe1cc1d4`

### ビュー仕様

```sql
CREATE OR REPLACE VIEW mart.v_reserve_daily_for_forecast AS
WITH customer_agg AS (
    SELECT
        reserve_date AS date,
        SUM(planned_trucks) AS reserve_trucks,
        SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) AS reserve_fixed_trucks,
        'customer_agg' AS source
    FROM stg.reserve_customer_daily
    GROUP BY reserve_date
),
manual_data AS (
    SELECT
        reserve_date AS date,
        total_trucks AS reserve_trucks,
        fixed_trucks AS reserve_fixed_trucks,
        'manual' AS source
    FROM stg.reserve_daily_manual
),
combined AS (
    SELECT
        COALESCE(m.date, c.date) AS date,
        COALESCE(m.reserve_trucks, c.reserve_trucks, 0) AS reserve_trucks,
        COALESCE(m.reserve_fixed_trucks, c.reserve_fixed_trucks, 0) AS reserve_fixed_trucks,
        COALESCE(m.source, c.source) AS source
    FROM manual_data m
    FULL OUTER JOIN customer_agg c ON m.date = c.date
    WHERE COALESCE(m.date, c.date) IS NOT NULL
)
SELECT
    date,
    reserve_trucks,
    reserve_fixed_trucks,
    CASE 
        WHEN reserve_trucks > 0 THEN 
            ROUND(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
        ELSE 0
    END AS reserve_fixed_ratio,
    source
FROM combined
ORDER BY date;
```

### 出力列
- `date`: 予約日
- `reserve_trucks`: 予約台数合計
- `reserve_fixed_trucks`: 固定客台数
- `reserve_fixed_ratio`: 固定客比率（0除算は0）
- `source`: データソース（'manual' or 'customer_agg'）

### ロジック
1. manual入力がある日付は **manual を優先**
2. manualがない日付は **customer_agg を集計**
3. どちらもない日は出力しない
4. `fixed_ratio` は VIEW で計算（0除算は0）

---

## テスト結果

### テストケース1: manual入力のみ

```sql
INSERT INTO stg.reserve_daily_manual (reserve_date, total_trucks, fixed_trucks)
VALUES ('2025-01-10', 100, 60);

SELECT * FROM mart.v_reserve_daily_for_forecast WHERE date = '2025-01-10';
```

**結果**:
```
    date    | reserve_trucks | reserve_fixed_trucks | reserve_fixed_ratio | source 
------------+----------------+----------------------+---------------------+--------
 2025-01-10 |            100 |                   60 |              0.6000 | manual
```

✅ **成功**: source=manual で返る

---

### テストケース2: customer_daily のみ

```sql
INSERT INTO stg.reserve_customer_daily (reserve_date, customer_cd, customer_name, planned_trucks, is_fixed_customer)
VALUES 
    ('2025-01-11', 'C001', '顧客A', 30, true),
    ('2025-01-11', 'C002', '顧客B', 20, false);

SELECT * FROM mart.v_reserve_daily_for_forecast WHERE date = '2025-01-11';
```

**結果**:
```
    date    | reserve_trucks | reserve_fixed_trucks | reserve_fixed_ratio |    source    
------------+----------------+----------------------+---------------------+--------------
 2025-01-11 |             50 |                   30 |              0.6000 | customer_agg
```

✅ **成功**: source=customer_agg で集計される

---

### テストケース3: 0除算のケース

```sql
INSERT INTO stg.reserve_daily_manual (reserve_date, total_trucks, fixed_trucks)
VALUES ('2025-01-12', 0, 0);

SELECT * FROM mart.v_reserve_daily_for_forecast WHERE date = '2025-01-12';
```

**結果**:
```
    date    | reserve_trucks | reserve_fixed_trucks | reserve_fixed_ratio | source 
------------+----------------+----------------------+---------------------+--------
 2025-01-12 |              0 |                    0 |                   0 | manual
```

✅ **成功**: total_trucks=0 の場合 ratio=0 になる

---

## 実行手順

### 新規環境への適用

```bash
# 1. ベースライン適用（初回のみ）
make al-up-env ENV=vm_stg

# 2. 確認
docker compose -f docker/docker-compose.stg.yml -p vm_stg exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini current
```

### ローカル開発環境

```bash
# 1. マイグレーション適用
make al-up-env ENV=local_dev

# 2. 確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini current
```

### ロールバック手順

```bash
# Phase 3をロールバック（VIEWのみ削除）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini downgrade -1

# Phase 2をロールバック（customer_daily削除）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini downgrade -1

# Phase 1をロールバック（manual削除）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini downgrade -1
```

---

## ファイル一覧

### 追加されたファイル

```
app/backend/core_api/migrations_v2/alembic/versions/
├── 20251216_001_add_reserve_daily_manual.py
├── 20251216_002_add_reserve_customer_daily.py
└── 20251216_003_add_v_reserve_daily_for_forecast.py
```

### コミット履歴

```
d30af734 - db: add reserve_daily_manual (phase 1, alembic)
fd779322 - db: add reserve_customer_daily (phase 2, alembic)
889ab51c - db: add v_reserve_daily_for_forecast (phase 3, alembic)
```

---

## 安全性の確認

### 既存データへの影響
- ✅ 既存テーブルへの変更なし
- ✅ 既存ビューへの影響なし
- ✅ 新規スキーマオブジェクトのみ追加

### スキーマ運用
- ✅ stg/mart の標準スキーマ構成に準拠
- ✅ timestamptz 使用（既存規約に準拠）
- ✅ CHECK制約でデータ整合性を保証

### Alembic運用
- ✅ 日付+連番の命名規則に準拠
- ✅ upgrade/downgrade が対になっている
- ✅ ローカルで検証済み

---

## 次のステップ

1. ✅ **Phase 1-3 完了** - 基盤テーブル・ビュー追加
2. ⬜ **API実装** - CRUD endpoints 追加
3. ⬜ **フロントエンド** - UI実装
4. ⬜ **テストコード** - 統合テスト追加

---

## 参考資料

- [Alembic運用ルール](../conventions/db/20251216_001_alembic_migration_rules.md)
- [migrations_v2 README](../../app/backend/core_api/migrations_v2/README.md)
