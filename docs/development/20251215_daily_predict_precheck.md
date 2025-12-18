# 日次予測 事前確認結果（target_date=2025-12-15）

**実行日時**: 2025-12-18  
**対象日**: 2025-12-15  
**環境**: local_dev

---

## 実績データ確認（mart.mv_receive_daily）

**期待**: 過去360日分（2024-12-20 ～ 2025-12-14）のデータが存在

```sql
WITH base AS (
  SELECT ddate::date AS d, receive_net_ton
  FROM mart.mv_receive_daily
  WHERE ddate >= DATE '2025-12-15' - INTERVAL '360 days'
    AND ddate <= DATE '2025-12-15' - INTERVAL '1 day'
)
SELECT
  MIN(d) AS min_date,
  MAX(d) AS max_date,
  COUNT(*) AS rows,
  COUNT(DISTINCT d) AS distinct_days,
  MIN(receive_net_ton) AS min_ton,
  MAX(receive_net_ton) AS max_ton,
  ROUND(AVG(receive_net_ton)::numeric, 2) AS avg_ton
FROM base;
```

### 結果

```
  min_date  |  max_date  | rows | distinct_days | min_ton | max_ton | avg_ton 
------------+------------+------+---------------+---------+---------+---------
 2024-12-20 | 2025-12-14 |  360 |           360 |   0.000 | 134.130 |   75.95
```

✅ **判定: OK**
- 360日分のデータが存在
- 最大日は前日（2025-12-14）まで
- 平均75.95トン、最大134.13トン

---

## 予約データ確認（mart.v_reserve_daily_for_forecast）

**期待**: 過去360日 + 当日（2025-12-15）のデータが存在

```sql
WITH base AS (
  SELECT date::date AS d, reserve_trucks, reserve_fixed_trucks
  FROM mart.v_reserve_daily_for_forecast
  WHERE date >= DATE '2025-12-15' - INTERVAL '360 days'
    AND date <= DATE '2025-12-15'
)
SELECT
  MIN(d) AS min_date,
  MAX(d) AS max_date,
  COUNT(*) AS rows,
  COUNT(DISTINCT d) AS distinct_days,
  SUM(CASE WHEN d = DATE '2025-12-15' THEN 1 ELSE 0 END) AS rows_on_target_date
FROM base;
```

### 結果

```
  min_date  |  max_date  | rows | distinct_days | rows_on_target_date 
------------+------------+------+---------------+---------------------
 2024-12-20 | 2025-12-15 |  337 |           337 |                   1
```

✅ **判定: OK**
- 337日分のデータが存在（営業日ベース）
- 最大日は当日（2025-12-15）まで
- 当日データあり（1行）

---

## 予約データ当日詳細

```sql
SELECT date, reserve_trucks, reserve_fixed_trucks, reserve_fixed_ratio, source
FROM mart.v_reserve_daily_for_forecast
WHERE date = DATE '2025-12-15';
```

### 結果

```
    date    | reserve_trucks | reserve_fixed_trucks | reserve_fixed_ratio | source 
------------+----------------+----------------------+---------------------+--------
 2025-12-15 |             76 |                   38 |              0.5000 | manual
```

✅ **判定: OK**
- 当日（2025-12-15）の予約データが存在
- 76台予約（内38台は固定顧客、比率50%）
- データソース: manual（手動入力）

---

## 総合判定

✅ **すべてOK - ジョブ投入可能**

- 実績データ: 360日分完備
- 予約データ: 337日分完備、当日含む
- 当日予約: 76台（明確な予測対象値）

次のステップ: forecast.forecast_jobsにジョブを投入
