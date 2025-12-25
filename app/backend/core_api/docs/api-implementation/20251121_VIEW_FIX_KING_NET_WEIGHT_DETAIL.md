# stg.v_king_receive_clean 修正レポート (2025-11-21)

## 概要

`stg.v_king_receive_clean` VIEW の定義を修正し、`net_weight` ではなく `net_weight_detail` カラムを正しく参照するようにしました。

## 問題

### 修正前の状態

```sql
-- 誤った定義（修正前）
SELECT
  invoice_d,
  invoice_no,
  net_weight AS net_weight_detail,  -- ← 伝票全体の正味重量を使用していた
  amount
FROM stg.receive_king_final k
WHERE
  vehicle_type_code = 1
  AND net_weight <> 0  -- ← 誤ったフィルタ
  ...
```

この定義では：

- **伝票全体の正味重量** (`net_weight`) を明細単位の重量として扱っていた
- Python 側で計算していた「正味重量\_明細」（`net_weight_detail`）と異なる値が集計されていた
- 結果として、KING のトン数が水増しされていた

## 実施した修正

### Alembic マイグレーション作成

新しいリビジョンファイルを作成：

```
20251121_100000000_fix_v_king_receive_clean_use_net_weight_detail.py
```

### 修正内容

```sql
-- 修正後の定義
CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
SELECT
  make_date(
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 1)::integer,
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer,
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer
  ) AS invoice_d,
  k.invoice_no,
  k.net_weight_detail,  -- ★ 修正: 明細単位の正味重量を直接参照
  k.amount
FROM stg.receive_king_final k
WHERE
  k.vehicle_type_code = 1
  AND k.net_weight_detail <> 0  -- ★ 修正: 正しいカラムでフィルタ
  AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text
  AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer BETWEEN 1 AND 12
  AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer BETWEEN 1 AND 31;
```

### 変更点

1. **SELECT 句**: `net_weight AS net_weight_detail` → `net_weight_detail`
2. **WHERE 句**: `net_weight <> 0` → `net_weight_detail <> 0`
3. その他のロジック（日付変換、`vehicle_type_code = 1`、日付バリデーション）は維持

## 適用手順

```bash
# 1. マイグレーション適用
cd /home/koujiro/work_env/22.Work_React/sanbou_app
make al-up

# 2. VIEW 定義確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev \
  -c "SELECT pg_get_viewdef('stg.v_king_receive_clean', true);"
```

## 検証結果

### データ統計

```sql
-- 全期間のデータ統計
SELECT
    MIN(invoice_d) as earliest_date,
    MAX(invoice_d) as latest_date,
    COUNT(*) as total_records,
    SUM(net_weight_detail) as total_net_weight_detail,
    SUM(amount) as total_amount
FROM stg.v_king_receive_clean;
```

実行結果（修正後）:

```
 earliest_date | latest_date | total_records | total_net_weight_detail | total_amount
---------------+-------------+---------------+-------------------------+--------------
 2021-03-01    | 2024-04-30  |        165269 |                87778251 |   5063660631
```

### 月別集計（最新5ヶ月）

```sql
SELECT
    DATE_TRUNC('month', invoice_d) as month,
    COUNT(*) as record_count,
    SUM(net_weight_detail)::numeric(12,2) as total_net_weight_detail,
    SUM(amount)::numeric(15,2) as total_amount
FROM stg.v_king_receive_clean
GROUP BY DATE_TRUNC('month', invoice_d)
ORDER BY month DESC
LIMIT 5;
```

実行結果:

```
         month          | record_count | total_net_weight_detail | total_amount
------------------------+--------------+-------------------------+--------------
 2024-04-01 00:00:00+00 |         4476 |              2421290.00 | 144405780.00
 2024-03-01 00:00:00+00 |         5015 |              2591210.00 | 154904400.00
 2024-02-01 00:00:00+00 |         4383 |              2196200.00 | 126428716.00
 2024-01-01 00:00:00+00 |         3966 |              2068010.00 | 113010450.00
 2023-12-01 00:00:00+00 |         4799 |              2425870.00 | 142900549.00
```

## 影響範囲

### 直接影響を受ける VIEW

- `stg.v_king_receive_clean` (修正対象)

### 間接的に影響を受ける VIEW

- `mart.v_receive_daily`
  - r_king CTE で `k.net_weight_detail` を参照
  - KING のトン数集計が正しい明細単位の値になる

## 比較検証用 SQL

### Python 側の「正味重量\_明細」との比較

```sql
-- 修正後の VIEW を使った集計（mart.v_receive_daily 経由）
SELECT
    DATE_TRUNC('month', ddate) as month,
    SUM(CASE WHEN source_system = 'king' THEN receive_net_ton ELSE 0 END) as king_ton,
    SUM(CASE WHEN source_system = 'king' THEN receive_vehicle_count ELSE 0 END) as king_vehicle_count,
    SUM(CASE WHEN source_system = 'king' THEN sales_yen ELSE 0 END) as king_sales_yen
FROM mart.v_receive_daily
WHERE ddate >= '2024-01-01' AND ddate < '2024-05-01'
GROUP BY DATE_TRUNC('month', ddate)
ORDER BY month;
```

### 生テーブルとの比較（検証用）

```sql
-- stg.receive_king_final の生データと VIEW の比較
WITH raw_data AS (
    SELECT
        DATE_TRUNC('month',
            make_date(
                split_part(replace(invoice_date::text, '/', '-'), '-', 1)::int,
                split_part(replace(invoice_date::text, '/', '-'), '-', 2)::int,
                split_part(replace(invoice_date::text, '/', '-'), '-', 3)::int
            )
        ) as month,
        SUM(net_weight_detail) as total_net_weight_detail_raw,
        COUNT(*) as record_count_raw
    FROM stg.receive_king_final
    WHERE vehicle_type_code = 1
      AND net_weight_detail <> 0
      AND invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
      AND split_part(replace(invoice_date::text, '/', '-'), '-', 2)::int BETWEEN 1 AND 12
      AND split_part(replace(invoice_date::text, '/', '-'), '-', 3)::int BETWEEN 1 AND 31
    GROUP BY DATE_TRUNC('month',
        make_date(
            split_part(replace(invoice_date::text, '/', '-'), '-', 1)::int,
            split_part(replace(invoice_date::text, '/', '-'), '-', 2)::int,
            split_part(replace(invoice_date::text, '/', '-'), '-', 3)::int
        )
    )
),
view_data AS (
    SELECT
        DATE_TRUNC('month', invoice_d) as month,
        SUM(net_weight_detail) as total_net_weight_detail_view,
        COUNT(*) as record_count_view
    FROM stg.v_king_receive_clean
    GROUP BY DATE_TRUNC('month', invoice_d)
)
SELECT
    COALESCE(r.month, v.month) as month,
    r.total_net_weight_detail_raw,
    v.total_net_weight_detail_view,
    r.total_net_weight_detail_raw - v.total_net_weight_detail_view as diff,
    r.record_count_raw,
    v.record_count_view
FROM raw_data r
FULL OUTER JOIN view_data v ON r.month = v.month
ORDER BY month DESC
LIMIT 5;
```

期待される結果: `diff` が 0 であること（VIEW と生テーブルで一致）

## ロールバック方法

万が一、元の定義に戻す必要がある場合：

```bash
# downgrade コマンド
make al-down
```

または、直接 SQL で元の定義に戻す：

```sql
CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
SELECT
  make_date(
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 1)::integer,
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer,
    split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer
  ) AS invoice_d,
  k.invoice_no,
  k.net_weight AS net_weight_detail,  -- 元の定義
  k.amount
FROM stg.receive_king_final k
WHERE
  k.vehicle_type_code = 1
  AND k.net_weight <> 0  -- 元のフィルタ
  AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text
  AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer BETWEEN 1 AND 12
  AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer BETWEEN 1 AND 31;
```

## まとめ

- ✅ `stg.v_king_receive_clean` VIEW を修正し、`net_weight_detail` を正しく参照するようにした
- ✅ Alembic マイグレーション `20251121_100000000` を作成・適用
- ✅ 既存の Alembic リビジョンファイルは編集せず、新規リビジョンで対応
- ✅ VIEW 定義の変更により、KING のトン数集計が明細単位の正確な値になった
- ✅ `mart.v_receive_daily` は修正後の VIEW を正しく参照している

---

**作成日**: 2025-11-21  
**担当**: GitHub Copilot  
**マイグレーションファイル**: `20251121_100000000_fix_v_king_receive_clean_use_net_weight_detail.py`
