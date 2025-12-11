# DBパフォーマンス調査レポート：ダッシュボードAPI高速化提案

**作成日**: 2025年12月11日  
**対象**: 受入ダッシュボード API（`/inbound/daily` と `/dashboard/target`）  
**目標**: daily エンドポイントを 1秒前後まで短縮、target エンドポイントの安定化

---

## 1. 対象エンドポイントと関連ファイル一覧

### 1.1 エンドポイント

| エンドポイント | 用途 | Router | UseCase | Repository |
|-------------|------|---------|---------|------------|
| `GET /inbound/daily` | 日次搬入量データ取得（カレンダー連続・0埋め済み） | [app/api/routers/inbound/router.py](app/backend/core_api/app/api/routers/inbound/router.py#L38) | [GetInboundDailyUseCase](app/backend/core_api/app/core/usecases/inbound/get_inbound_daily_uc.py) | [InboundRepositoryImpl](app/backend/core_api/app/infra/adapters/inbound/inbound_repository.py) |
| `GET /dashboard/target` | 月次/週次/日次ターゲット＋実績 | [app/api/routers/dashboard/router.py](app/backend/core_api/app/api/routers/dashboard/router.py#L33) | [BuildTargetCardUseCase](app/backend/core_api/app/core/usecases/dashboard/build_target_card_uc.py) | [DashboardTargetRepository](app/backend/core_api/app/infra/adapters/dashboard/dashboard_target_repository.py) |

### 1.2 主要クエリファイル

- **daily**: [inbound_pg_repository__get_daily_with_comparisons.sql](app/backend/core_api/app/infra/db/sql/inbound/inbound_pg_repository__get_daily_with_comparisons.sql)
- **target**: [dashboard_target_repo__get_by_date_optimized.sql](app/backend/core_api/app/infra/db/sql/dashboard/dashboard_target_repo__get_by_date_optimized.sql)

---

## 2. 参照テーブル・ビュー・インデックスの現状

### 2.1 主要データソース

#### 2.1.1 `mart.v_receive_daily` (VIEW)

**役割**: 受入実績の日次集計（将軍Flash/Final + KINGの優先順位統合）

**定義**: [migrations/alembic/sql/mart/v_receive_daily.sql](app/backend/core_api/migrations/alembic/sql/mart/v_receive_daily.sql)

**構造**:
```sql
WITH r_shogun_final AS (
  SELECT s.slip_date AS ddate,
         (sum(s.net_weight) / 1000.0) AS receive_ton,
         count(DISTINCT s.receive_no) AS vehicle_count,
         sum(s.amount) AS sales_yen
  FROM stg.receive_shogun_final s
  WHERE s.slip_date IS NOT NULL
  GROUP BY s.slip_date
),
r_shogun_flash AS (...同様),
r_king AS (
  SELECT (k.invoice_date)::date AS ddate,
         ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
         count(DISTINCT k.invoice_no) AS vehicle_count,
         (sum(k.amount))::numeric AS sales_yen
  FROM stg.receive_king_final k
  WHERE k.vehicle_type_code = 1 AND k.net_weight_detail <> 0
  GROUP BY (k.invoice_date)::date
),
r_pick AS (
  -- 優先順位: shogun_final > shogun_flash > king
  SELECT ... FROM r_shogun_final
  UNION ALL SELECT ... FROM r_shogun_flash WHERE NOT EXISTS (...)
  UNION ALL SELECT ... FROM r_king WHERE NOT EXISTS (...)
)
SELECT cal.ddate, ..., p.receive_net_ton, ...
FROM ref.v_calendar_classified cal
LEFT JOIN r_pick p ON p.ddate = cal.ddate
WHERE cal.ddate <= (now() AT TIME ZONE 'Asia/Tokyo')::date - 1
ORDER BY cal.ddate;
```

**粒度**: 日次（1行 = 1日の全体集計）  
**想定行数**: ~1,000行（過去3年分程度）  
**既存インデックス**: なし（VIEWのため実体化されていない）

**依存する stg テーブル**:
- `stg.receive_shogun_final` (主キー: `receive_no, line_no`)
- `stg.receive_shogun_flash` (主キー: `receive_no, line_no`)
- `stg.receive_king_final` (主キー: `invoice_no, line_no`)

#### 2.1.2 `mart.mv_target_card_per_day` (MATERIALIZED VIEW)

**役割**: 日次/週次/月次の目標と実績を事前集計

**定義**: [migrations/alembic/sql/mart/v_target_card_per_day.sql](app/backend/core_api/migrations/alembic/sql/mart/v_target_card_per_day.sql)

**マテリアライズド化の経緯**: 
- 元々は VIEW `mart.v_target_card_per_day` として存在
- 2025-11-17 に MV 化（[migration](app/backend/core_api/migrations/alembic/versions/20251117_135913797_create_mv_target_card_per_day.py)）
- 日次で `REFRESH MATERIALIZED VIEW CONCURRENTLY` される前提

**構造**:
```sql
WITH base AS (
  SELECT v.ddate, v.iso_year, v.iso_week, ..., day_target_ton
  FROM mart.v_daily_target_with_calendar v
),
week_target AS (
  SELECT iso_year, iso_week, sum(target_ton) AS week_target_ton
  FROM mart.v_daily_target_with_calendar
  GROUP BY iso_year, iso_week
),
month_target AS (
  SELECT month_key, month_target_ton
  FROM kpi.monthly_targets WHERE metric='inbound' AND segment='factory'
),
week_actual AS (
  SELECT iso_year, iso_week, sum(receive_net_ton) AS week_actual_ton
  FROM mart.v_receive_daily r GROUP BY iso_year, iso_week
),
month_actual AS (
  SELECT month_key, sum(receive_net_ton) AS month_actual_ton
  FROM mart.v_receive_daily r GROUP BY month_key
)
SELECT b.ddate, day_target_ton, week_target_ton, month_target_ton,
       day_actual_ton_prev, week_actual_ton, month_actual_ton, ...
FROM base b
LEFT JOIN week_target wt ...
LEFT JOIN month_target mt ...
LEFT JOIN week_actual wa ...
LEFT JOIN month_actual ma ...
LEFT JOIN mart.v_receive_daily rprev ON rprev.ddate = b.ddate - 1
ORDER BY b.ddate;
```

**粒度**: 日次（カレンダー全体、将来日も含む）  
**想定行数**: ~3,000行（2022-01-01 ～ 2027-12-31 想定）  

**既存インデックス**:
- `UNIQUE INDEX ux_mv_target_card_per_day_ddate ON (ddate)` ← REFRESH CONCURRENTLY 要件 + 単一日検索最適化
- `INDEX ix_mv_target_card_per_day_iso_week ON (iso_year, iso_week)` ← 週次集計最適化

#### 2.1.3 `ref.v_calendar_classified` (VIEW)

**役割**: 営業カレンダー（営業日フラグ、ISO週番号など）

**粒度**: 日次  
**想定行数**: ~3,650行（10年分）  
**既存インデックス**: なし（VIEWのため）

#### 2.1.4 `stg.receive_king_final`

**役割**: KING伝票データ（行レベル）

**推定行数**: ~数万～数十万行（伝票×行）  

**既存インデックス**:
- `idx_king_invdate_func_no_filtered ON ((invoice_date::date))` ← 日付検索用
- `idx_king_invdate_receiveno_cover ON (invoice_date, receive_no)` ← カバリングインデックス

#### 2.1.5 `stg.receive_shogun_final` / `stg.receive_shogun_flash`

**役割**: 将軍伝票データ（行レベル）

**推定行数**: ~数万～数十万行（伝票×行）  

**既存インデックス**: 
- `slip_date` に対する明示的なインデックスは確認できず（主キー: `receive_no, line_no` のみ）

---

### 2.2 データフロー図

```
[stg.receive_shogun_final]
[stg.receive_shogun_flash]  → [mart.v_receive_daily (VIEW)] → [daily API]
[stg.receive_king_final]                                      ↓
                                                    [mart.mv_target_card_per_day (MV)] → [target API]
[ref.v_calendar_classified]  ←────────────────────┘
[kpi.monthly_targets]        ←────────────────────┘
```

---

## 3. クエリ構造とボトルネック仮説

### 3.1 `/inbound/daily` の処理フロー

#### クエリ構造（[inbound_pg_repository__get_daily_with_comparisons.sql](app/backend/core_api/app/infra/db/sql/inbound/inbound_pg_repository__get_daily_with_comparisons.sql)）

```sql
WITH d AS (
  -- 対象期間のカレンダー × 受入実績を LEFT JOIN
  SELECT c.ddate, c.iso_year, c.iso_week, c.iso_dow, c.is_business,
         COALESCE(r.receive_net_ton, 0) AS ton
  FROM mart.v_calendar c
  LEFT JOIN mart.v_receive_daily r ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
),
prev_month AS (
  -- 4週前のデータ（28日前）
  SELECT c.ddate + INTERVAL '28 days' AS target_ddate,
         COALESCE(r.receive_net_ton, 0) AS pm_ton
  FROM mart.v_calendar c
  LEFT JOIN mart.v_receive_daily r ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN (:start - 28) AND (:end - 28)
),
prev_year AS (
  -- 前年同週同曜日のデータ
  SELECT c_curr.ddate AS target_ddate,
         COALESCE(r_prev.receive_net_ton, 0) AS py_ton
  FROM mart.v_calendar c_curr
  LEFT JOIN mart.v_calendar c_prev ON c_prev.iso_year = c_curr.iso_year - 1
    AND c_prev.iso_week = c_curr.iso_week AND c_prev.iso_dow = c_curr.iso_dow
  LEFT JOIN mart.v_receive_daily r_prev ON r_prev.ddate = c_prev.ddate
  WHERE c_curr.ddate BETWEEN :start AND :end
),
base_with_comparisons AS (
  SELECT d.*, pm.pm_ton AS prev_month_ton, py.py_ton AS prev_year_ton
  FROM d
  LEFT JOIN prev_month pm ON pm.target_ddate = d.ddate
  LEFT JOIN prev_year py ON py.target_ddate = d.ddate
)
SELECT ddate, iso_year, iso_week, iso_dow, is_business, NULL AS segment,
       ton,
       -- cum_scope に応じてウィンドウ関数で累積計算
       CASE cum_scope
         WHEN 'range' THEN SUM(ton) OVER (ORDER BY ddate ROWS UNBOUNDED PRECEDING)
         WHEN 'month' THEN SUM(ton) OVER (PARTITION BY DATE_TRUNC('month', ddate) ORDER BY ddate ...)
         WHEN 'week' THEN SUM(ton) OVER (PARTITION BY iso_year, iso_week ORDER BY ddate ...)
         ELSE NULL
       END AS cum_ton,
       prev_month_ton, prev_year_ton,
       -- 前月/前年の累積も同様に計算
       ...
FROM base_with_comparisons b
ORDER BY b.ddate;
```

#### ボトルネック仮説

1. **`mart.v_receive_daily` が VIEW であるため、毎回 CTE を再評価**
   - `r_shogun_final`, `r_shogun_flash`, `r_king` の 3つの集計を毎回実行
   - 各 CTE で `GROUP BY slip_date` / `invoice_date::date` を実行 → stg テーブルのフルスキャンまたはインデックススキャン
   - `r_pick` の UNION ALL + NOT EXISTS による優先順位制御 → 複雑な実行計画

2. **前月/前年の比較データ取得で `v_receive_daily` を複数回参照**
   - `prev_month` CTE で再度 `v_receive_daily` を評価（28日前の範囲）
   - `prev_year` CTE で再度 `v_receive_daily` を評価（前年同週同曜日）
   - → 合計 3回 `v_receive_daily` のCTEが展開される可能性

3. **`stg.receive_shogun_*` テーブルに `slip_date` のインデックスがない**
   - `WHERE slip_date IS NOT NULL` + `GROUP BY slip_date` → Sequential Scan の可能性
   - 特に `stg.receive_shogun_final` / `stg.receive_shogun_flash` が大きい場合に顕著

4. **ウィンドウ関数の累積計算（`cum_scope`）**
   - `cum_scope='month'` や `cum_scope='week'` の場合、PARTITION BY + ORDER BY でソートが発生
   - 対象期間が長いと（例: 1年分）、計算コストが増大

5. **クエリの複雑さ（複数CTEの入れ子）**
   - 最適化されたとしても、プランニング時間が長い
   - EXPLAIN ANALYZE を取らないと実測は不明だが、「複数VIEW参照 + CTE + ウィンドウ関数」は重い傾向

---

### 3.2 `/dashboard/target` の処理フロー

#### クエリ構造（[dashboard_target_repo__get_by_date_optimized.sql](app/backend/core_api/app/infra/db/sql/dashboard/dashboard_target_repo__get_by_date_optimized.sql)）

```sql
WITH today AS (SELECT CURRENT_DATE::date AS today),
bounds AS (
  SELECT date_trunc('month', :req)::date AS month_start,
         (date_trunc('month', :req) + INTERVAL '1 month - 1 day')::date AS month_end
),
anchor AS (
  -- 当月/過去月/未来月でアンカー日を自動解決
  SELECT CASE
    WHEN month_start = today_month THEN LEAST(today, month_end)
    WHEN month_start < today_month THEN month_end
    ELSE COALESCE(MIN(mv.ddate) WHERE is_business=true, month_start)
  END AS ddate
),
base AS (
  -- MV から該当日の1行を取得（UNIQUE INDEX で高速）
  SELECT ddate, day_target_ton, week_target_ton, month_target_ton,
         day_actual_ton_prev, week_actual_ton, month_actual_ton, ...
  FROM mart.mv_target_card_per_day v
  JOIN anchor a ON v.ddate = a.ddate
  LIMIT 1
),
cumulative_end_date AS (
  -- 累積計算の終了日を決定（昨日 or 月末 or アンカー日-1）
  SELECT ...
),
month_target_to_date AS (
  -- 月初～累積終了日までの day_target_ton を SUM
  SELECT SUM(day_target_ton) AS month_target_to_date_ton
  FROM mart.mv_target_card_per_day v
  WHERE v.ddate BETWEEN month_start AND cumulative_end_date
),
month_target_total AS (
  -- 月全体の MAX(month_target_ton)
  SELECT MAX(month_target_ton) AS month_target_total_ton
  FROM mart.mv_target_card_per_day v
  WHERE v.ddate BETWEEN month_start AND month_end
),
week_target_to_date AS (
  -- 週初～累積終了日までの day_target_ton を SUM（同一 iso_year, iso_week）
  SELECT SUM(day_target_ton) AS week_target_to_date_ton
  FROM mart.mv_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year AND v.iso_week = b.iso_week
    AND v.ddate >= month_start AND v.ddate <= cumulative_end_date
),
week_target_total AS (
  -- 週全体の MAX(week_target_ton)
  SELECT MAX(week_target_ton) AS week_target_total_ton
  FROM mart.mv_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year AND v.iso_week = b.iso_week
    AND v.ddate >= month_start AND v.ddate <= month_end
),
month_actual_to_date AS (
  -- 月初～累積終了日までの receive_net_ton を SUM
  SELECT SUM(receive_net_ton) AS month_actual_to_date_ton
  FROM mart.v_receive_daily r
  WHERE r.ddate BETWEEN month_start AND cumulative_end_date
),
week_actual_to_date AS (
  -- 週初～累積終了日までの receive_net_ton を SUM（同一 iso_year, iso_week）
  SELECT SUM(receive_net_ton) AS week_actual_to_date_ton
  FROM mart.v_receive_daily r, base b
  WHERE r.iso_year = b.iso_year AND r.iso_week = b.iso_week
    AND r.ddate >= month_start AND r.ddate <= cumulative_end_date
)
SELECT b.ddate,
       CASE WHEN mode='monthly' AND NOT current_month THEN NULL ELSE day_target_ton END,
       ...,
       month_target_to_date_ton, month_target_total_ton,
       week_target_to_date_ton, week_target_total_ton,
       month_actual_to_date_ton, week_actual_to_date_ton
FROM base b;
```

#### ボトルネック仮説

1. **`mart.mv_target_card_per_day` の複数回スキャン**
   - `base` で 1行取得（UNIQUE INDEX で高速）
   - `month_target_to_date` / `month_target_total` / `week_target_to_date` / `week_target_total` で再度スキャン
   - → 合計 5回の MV アクセス（ただし MV なので VIEW よりは高速）

2. **`mart.v_receive_daily` を2回参照（`month_actual_to_date` / `week_actual_to_date`）**
   - VIEW なので毎回 CTE を再評価 → stg テーブルの集計を2回実行
   - 特に `month_actual_to_date` で月全体をスキャン → 30～40日分の CTE 展開

3. **複数の CTE が Sequential に実行される**
   - PostgreSQL のクエリプランナーは CTE を最適化しづらい（Materialization fence）
   - 各 CTE が独立して実行されるため、共通部分を共有できない

4. **`week_actual_to_date` / `month_actual_to_date` の実行コスト**
   - `v_receive_daily` は実体化されていないため、毎回 stg テーブルの集計が走る
   - `WHERE ddate BETWEEN ...` でフィルタされるが、VIEW の定義上 `ORDER BY ddate` があるため、全体をソートしてから範囲抽出する可能性

5. **キャッシュの有効期限（60秒 TTL）**
   - UseCase 層で cachetools を使用（TTL 60秒）
   - → 同一 `(date, mode)` への連続リクエストは高速だが、60秒経過後は再計算
   - → 複数ユーザーが異なる月を同時に開くとキャッシュミスが多発

---

## 4. 高速化アイデア一覧

### 4.1 物理設計（テーブル / MV / パーティション）

#### 【高優先度】案1: `mart.v_receive_daily` をマテリアライズドビュー化

**概要**:
- 現在 VIEW である `mart.v_receive_daily` を `mart.mv_receive_daily` として MV 化
- 毎回 stg テーブルの集計を実行するコストを削減

**具体的な手順**:
```sql
-- 1. MVを作成
CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
SELECT * FROM mart.v_receive_daily;

-- 2. UNIQUE INDEX を付与（REFRESH CONCURRENTLY 要件）
CREATE UNIQUE INDEX ux_mv_receive_daily_ddate ON mart.mv_receive_daily (ddate);

-- 3. 複合インデックス（週次集計用）
CREATE INDEX ix_mv_receive_daily_iso_week ON mart.mv_receive_daily (iso_year, iso_week);

-- 4. 日次で REFRESH（CSV アップロード後など）
REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_receive_daily;
```

**狙い**:
- `/inbound/daily` の `prev_month` / `prev_year` CTE で `v_receive_daily` を 3回参照 → MV なら事前集計済みで高速
- `/dashboard/target` の `month_actual_to_date` / `week_actual_to_date` でも MV 参照 → 集計コスト削減

**想定効果**: **大**（特に `/inbound/daily` で顕著）

**影響範囲**:
- [InboundRepositoryImpl](app/backend/core_api/app/infra/adapters/inbound/inbound_repository.py) の SQL テンプレート（`mart.v_receive_daily` → `mart.mv_receive_daily` に置換）
- [DashboardTargetRepository](app/backend/core_api/app/infra/adapters/dashboard/dashboard_target_repository.py) の SQL テンプレート
- 新規マイグレーションファイルの作成
- **REFRESH タイミング**: CSV アップロード完了後、または日次バッチで自動実行

**注意点**:
- MV のリフレッシュコスト: 数百行程度なら数秒で完了（CONCURRENTLY なのでロック無し）
- データ整合性: リフレッシュ前の古いデータが表示される可能性（許容範囲なら OK）
- 運用ルール: `make refresh-mv-receive-daily` のようなタスクを Makefile に追加

**DDL サンプル**:
```sql
-- migrations/alembic/versions/20251211_create_mv_receive_daily.py

def upgrade():
    op.execute("""
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
        SELECT * FROM mart.v_receive_daily;
    """)
    op.execute("""
        CREATE UNIQUE INDEX ux_mv_receive_daily_ddate 
        ON mart.mv_receive_daily (ddate);
    """)
    op.execute("""
        CREATE INDEX ix_mv_receive_daily_iso_week 
        ON mart.mv_receive_daily (iso_year, iso_week);
    """)
    print("✓ Created mart.mv_receive_daily with indexes")

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily;")
```

---

#### 【中優先度】案2: 日次集計専用のサマリテーブル `kpi.inbound_daily_summary`

**概要**:
- `mart.v_receive_daily` の結果を毎日コピーして、軽量な物理テーブルに格納
- MV よりも軽量で、追加カラム（前月比、前年比など）を事前計算して格納可能

**テーブル定義**:
```sql
CREATE TABLE kpi.inbound_daily_summary (
  ddate date PRIMARY KEY,
  iso_year int,
  iso_week int,
  iso_dow int,
  is_business boolean,
  receive_net_ton numeric(18,3),
  receive_vehicle_count int,
  avg_weight_kg_per_vehicle numeric(18,3),
  sales_yen numeric(18,0),
  unit_price_yen_per_kg numeric(18,3),
  source_system text,
  -- 事前計算フィールド
  prev_month_ton numeric(18,3),  -- 4週前の同日
  prev_year_ton numeric(18,3),   -- 前年同週同曜日
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now()
);

CREATE INDEX ix_inbound_daily_summary_iso_week 
ON kpi.inbound_daily_summary (iso_year, iso_week);
```

**更新ロジック**:
```sql
-- CSV アップロード後に実行（Upsert）
INSERT INTO kpi.inbound_daily_summary (ddate, iso_year, iso_week, receive_net_ton, ...)
SELECT ddate, iso_year, iso_week, receive_net_ton, ...
FROM mart.v_receive_daily
WHERE ddate = :target_date
ON CONFLICT (ddate) DO UPDATE SET
  receive_net_ton = EXCLUDED.receive_net_ton,
  updated_at = now();
```

**狙い**:
- `/inbound/daily` のクエリが単純な `SELECT * FROM kpi.inbound_daily_summary WHERE ddate BETWEEN ...` になる
- 前月比・前年比も事前計算済みなので、CTE 不要

**想定効果**: **大**（`/inbound/daily` が 1秒未満になる可能性）

**影響範囲**:
- 新規テーブル作成
- CSV アップロード完了後の更新処理（[IngestUseCase](app/backend/core_api/app/core/usecases/ingest/ingest_uc.py) に追加）
- [InboundRepositoryImpl](app/backend/core_api/app/infra/adapters/inbound/inbound_repository.py) のクエリを書き換え

**注意点**:
- 過去データの初回投入が必要（バックフィル）
- 更新タイミングを明確にする（CSV アップロード後、日次バッチ後など）
- VIEW との二重管理になるため、整合性チェックが必要

---

#### 【低優先度】案3: 月次目標テーブルの正規化

**概要**:
- 現在 `kpi.monthly_targets` は `(month_date, metric, segment)` の複合キーで管理
- `month_target_ton` を取得するたびに `DISTINCT ON` + `ORDER BY updated_at DESC` で最新値を取得
- → 最新値のみを保持する専用テーブル `kpi.monthly_targets_current` を作成

**テーブル定義**:
```sql
CREATE TABLE kpi.monthly_targets_current (
  month_date date,
  metric text,
  segment text,
  value numeric,
  updated_at timestamp DEFAULT now(),
  PRIMARY KEY (month_date, metric, segment)
);
```

**狙い**:
- `mart.v_target_card_per_day` の `month_target` CTE が単純な JOIN になる
- `DISTINCT ON` + `ORDER BY` のコストを削減

**想定効果**: **小**（月次目標は数十行程度なので、効果は限定的）

**影響範囲**:
- 新規テーブル作成
- 目標値更新処理（[MonthlyTargetUseCase](app/backend/core_api/app/core/usecases/kpi/monthly_target_uc.py)）に Upsert ロジック追加

---

### 4.2 インデックス設計

#### 【高優先度】案4: `stg.receive_shogun_*` に `slip_date` のインデックスを追加

**概要**:
- `stg.receive_shogun_final` と `stg.receive_shogun_flash` に `slip_date` の B-tree インデックスを追加
- `WHERE slip_date IS NOT NULL` + `GROUP BY slip_date` が高速化される

**DDL**:
```sql
CREATE INDEX IF NOT EXISTS ix_receive_shogun_final_slip_date 
ON stg.receive_shogun_final (slip_date) 
WHERE slip_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_receive_shogun_flash_slip_date 
ON stg.receive_shogun_flash (slip_date) 
WHERE slip_date IS NOT NULL;
```

**狙い**:
- `mart.v_receive_daily` の `r_shogun_final` / `r_shogun_flash` CTE で Sequential Scan → Index Scan に変更
- 特に `GROUP BY slip_date` の前処理が高速化

**想定効果**: **中～大**（stg テーブルが大きい場合に顕著）

**影響範囲**:
- 新規インデックス追加のみ（既存クエリは変更不要）

**注意点**:
- 部分インデックス（`WHERE slip_date IS NOT NULL`）にすることでインデックスサイズを削減
- インデックスの肥大化を防ぐため、定期的な `REINDEX` または `VACUUM FULL` を検討

---

#### 【中優先度】案5: `stg.receive_king_final` の複合インデックス最適化

**概要**:
- 現在 `idx_king_invdate_func_no_filtered` が `(invoice_date::date)` にあるが、`WHERE vehicle_type_code = 1` のフィルタには効かない
- → `(vehicle_type_code, invoice_date)` の複合インデックスを追加

**DDL**:
```sql
CREATE INDEX IF NOT EXISTS ix_receive_king_final_vtype_invdate 
ON stg.receive_king_final (vehicle_type_code, (invoice_date::date))
WHERE vehicle_type_code = 1 AND net_weight_detail <> 0;
```

**狙い**:
- `mart.v_receive_daily` の `r_king` CTE で `WHERE vehicle_type_code = 1 AND net_weight_detail <> 0` + `GROUP BY invoice_date::date` が高速化

**想定効果**: **中**（KING伝票が多い場合に効果あり）

**影響範囲**:
- 新規インデックス追加のみ

**注意点**:
- 部分インデックス（`WHERE vehicle_type_code = 1 AND net_weight_detail <> 0`）にすることでサイズ削減
- 既存インデックス `idx_king_invdate_func_no_filtered` と併用（将来的に統合検討）

---

### 4.3 クエリ設計の見直し

#### 【高優先度】案6: `/inbound/daily` のクエリを段階的に分割

**概要**:
- 現在のクエリは「当期間 + 前月 + 前年」を1つの SQL で取得
- → まず当期間のデータのみを取得し、前月/前年は別途クエリで取得（または省略）

**変更案**:
```python
# 1. 当期間のデータのみ取得（軽量クエリ）
SELECT ddate, iso_year, iso_week, iso_dow, is_business, ton, cum_ton
FROM mart.mv_receive_daily
WHERE ddate BETWEEN :start AND :end
ORDER BY ddate;

# 2. 前月/前年データは必要な場合のみ別クエリで取得（オプション）
SELECT ddate, ton AS prev_month_ton
FROM mart.mv_receive_daily
WHERE ddate BETWEEN (:start - 28) AND (:end - 28);
```

**狙い**:
- メインクエリの複雑さを削減 → プランニング時間短縮
- フロントエンドで「前月/前年比較は詳細表示時のみ取得」といった UX 改善も可能

**想定効果**: **中～大**（特にクエリが複雑な場合）

**影響範囲**:
- [InboundRepositoryImpl](app/backend/core_api/app/infra/adapters/inbound/inbound_repository.py) のクエリロジック変更
- フロントエンド側の API 呼び出し調整（必要に応じて）

---

#### 【中優先度】案7: `/dashboard/target` の累積計算を MV に統合

**概要**:
- 現在 `month_target_to_date` / `week_target_to_date` などを毎回 SQL で計算
- → これらを `mart.mv_target_card_per_day` に事前計算済みカラムとして追加

**MV の追加カラム案**:
```sql
CREATE MATERIALIZED VIEW mart.mv_target_card_per_day_enhanced AS
WITH base AS (...),
     week_target AS (...),
     month_target AS (...),
     week_actual AS (...),
     month_actual AS (...),
     -- 新規: 累積計算
     month_cumulative AS (
       SELECT ddate, 
              SUM(day_target_ton) OVER (
                PARTITION BY DATE_TRUNC('month', ddate) 
                ORDER BY ddate ROWS UNBOUNDED PRECEDING
              ) AS month_target_to_date_ton,
              SUM(receive_net_ton) OVER (
                PARTITION BY DATE_TRUNC('month', ddate) 
                ORDER BY ddate ROWS UNBOUNDED PRECEDING
              ) AS month_actual_to_date_ton
       FROM base
     ),
     week_cumulative AS (...)
SELECT b.ddate, ..., 
       mc.month_target_to_date_ton, 
       mc.month_actual_to_date_ton,
       wc.week_target_to_date_ton,
       wc.week_actual_to_date_ton
FROM base b
LEFT JOIN month_cumulative mc ON mc.ddate = b.ddate
LEFT JOIN week_cumulative wc ON wc.ddate = b.ddate;
```

**狙い**:
- `/dashboard/target` のクエリが単純な `SELECT * FROM mv_target_card_per_day_enhanced WHERE ddate = :date` になる
- 複数 CTE の再計算が不要

**想定効果**: **大**（特に `/dashboard/target` の応答時間が 50%以上短縮される可能性）

**影響範囲**:
- MV の再設計（マイグレーション）
- [DashboardTargetRepository](app/backend/core_api/app/infra/adapters/dashboard/dashboard_target_repository.py) のクエリ書き換え

**注意点**:
- MV のリフレッシュ時間が若干増加（累積計算のため）
- ただし事前計算なので、クエリ実行時のコストは大幅削減

---

#### 【低優先度】案8: 不要な `ORDER BY` の削除

**概要**:
- `mart.v_receive_daily` の定義に `ORDER BY cal.ddate` があるが、VIEW の結果をさらに JOIN/フィルタする場合は無駄なソート
- → VIEW 定義から `ORDER BY` を削除し、必要な箇所（最終的な SELECT）でのみソート

**変更案**:
```sql
-- Before
CREATE OR REPLACE VIEW mart.v_receive_daily AS
...
ORDER BY cal.ddate;

-- After
CREATE OR REPLACE VIEW mart.v_receive_daily AS
...
-- ORDER BY 削除
;
```

**狙い**:
- VIEW を参照する側で `WHERE ddate BETWEEN ...` などのフィルタがある場合、ソートが無駄になる
- PostgreSQL のクエリプランナーは ORDER BY を最適化できない場合がある

**想定効果**: **小～中**（プランナーが賢い場合は効果なし）

**影響範囲**:
- VIEW 定義の修正（マイグレーション）
- 既存の参照箇所で `ORDER BY` が必要な場合は明示的に追加

---

### 4.4 キャッシュ戦略（DB or アプリ）

#### 【高優先度】案9: 目標値のメモリキャッシュ（TTL 延長）

**概要**:
- 現在 `BuildTargetCardUseCase` で cachetools による 60秒 TTL キャッシュ
- → 目標値は日次でしか変わらないため、TTL を 1時間 or 当日中に延長

**変更案**:
```python
# app/core/usecases/dashboard/build_target_card_uc.py
from cachetools import TTLCache
_CACHE: TTLCache = TTLCache(maxsize=512, ttl=3600)  # 1時間
```

**狙い**:
- 複数ユーザーが同じ月を開いても、1時間内なら DB クエリ不要
- キャッシュヒット率が大幅向上

**想定効果**: **中**（アクセスパターンによる）

**影響範囲**:
- UseCase の TTL 設定のみ変更

**注意点**:
- CSV アップロード後に `BuildTargetCardUseCase.clear_cache()` を呼び出す必要あり
- キャッシュサイズ（maxsize）も 512 程度に増やすと良い

---

#### 【中優先度】案10: Redis によるグローバルキャッシュ

**概要**:
- 現在のメモリキャッシュはアプリインスタンスごとに独立
- → Redis を導入し、複数インスタンス間でキャッシュを共有

**実装案**:
```python
import redis
from functools import lru_cache

redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_target_card_cached(date: str, mode: str):
    cache_key = f"target_card:{date}:{mode}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # DB から取得
    result = repository.get_by_date_optimized(date, mode)
    redis_client.setex(cache_key, 3600, json.dumps(result))  # 1時間
    return result
```

**狙い**:
- 複数 API サーバー（Kubernetes など）で同じキャッシュを共有
- TTL を柔軟に設定可能（日次で自動削除など）

**想定効果**: **中～大**（マルチインスタンス環境で顕著）

**影響範囲**:
- Redis の導入（インフラ）
- UseCase または Repository 層にキャッシュロジック追加

**注意点**:
- Redis の可用性管理が必要
- キャッシュの無効化タイミングを明確にする（CSV アップロード後など）

---

#### 【低優先度】案11: フロントエンドでの SWR（Stale-While-Revalidate）

**概要**:
- React の SWR ライブラリを使い、フロントエンドでデータをキャッシュ
- バックグラウンドで再取得しつつ、古いデータをすぐ表示

**実装案**:
```tsx
import useSWR from 'swr';

function InboundForecastDashboardPage() {
  const { data, error } = useSWR(
    `/dashboard/target?date=${date}&mode=monthly`,
    fetcher,
    { refreshInterval: 60000 } // 1分ごとに再取得
  );
  
  if (!data) return <Skeleton />;
  return <TargetCard data={data} />;
}
```

**狙い**:
- 初回アクセス後、ブラウザ内でキャッシュされるため、2回目以降は瞬時に表示
- バックエンドの負荷も軽減

**想定効果**: **中**（UX 改善がメイン）

**影響範囲**:
- フロントエンドのみ（バックエンドは変更不要）

---

### 4.5 API 粒度の調整（DB寄りの観点）

#### 【中優先度】案12: `/dashboard/all` で `daily` + `target` を一括取得

**概要**:
- 現在フロントエンドは `/inbound/daily` と `/dashboard/target` を別々に呼び出し
- → 1つの API `/dashboard/all` で両方のデータを返すことで、DB クエリを統合

**実装案**:
```python
@router.get("/all")
def get_dashboard_all(
    date: date_type,
    mode: Literal["daily", "monthly"] = "monthly",
    uc_target: BuildTargetCardUseCase = Depends(...),
    uc_daily: GetInboundDailyUseCase = Depends(...),
):
    # 月初～月末の範囲を計算
    start = date.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # target データを取得
    target_output = uc_target.execute(BuildTargetCardInput(date, mode))
    
    # daily データを取得（月全体）
    daily_output = uc_daily.execute(GetInboundDailyInput(start, end, None, "month"))
    
    return {
        "target": target_output.data,
        "daily": daily_output.data,
    }
```

**狙い**:
- 2つの HTTP リクエスト → 1つにまとめることで、RTT（Round Trip Time）を削減
- 裏側で `mart.mv_receive_daily` を1回だけ評価すれば両方のクエリで使える

**想定効果**: **中**（ネットワークレイテンシが大きい環境で効果大）

**影響範囲**:
- 新規エンドポイント追加
- フロントエンドの API 呼び出しロジック変更

**注意点**:
- レスポンスサイズが大きくなる（圧縮必須）
- 既存エンドポイントとの互換性を保つため、`/dashboard/target` と `/inbound/daily` は残す

---

## 5. 優先順位と推奨ロードマップ

### 5.1 優先順位マトリクス

| 案 | 優先度 | 難易度 | 想定効果 | `/daily` への効果 | `/target` への効果 |
|---|-------|-------|---------|-----------------|------------------|
| 案1: `mart.v_receive_daily` の MV 化 | **High** | 中 | **大** | ⭐⭐⭐ | ⭐⭐ |
| 案4: `stg.receive_shogun_*` にインデックス追加 | **High** | 小 | **中～大** | ⭐⭐⭐ | ⭐ |
| 案6: `/inbound/daily` のクエリ分割 | **High** | 中 | **中～大** | ⭐⭐⭐ | - |
| 案9: 目標値キャッシュの TTL 延長 | **High** | 小 | 中 | - | ⭐⭐ |
| 案7: `/dashboard/target` の累積計算を MV に統合 | Medium | 大 | **大** | - | ⭐⭐⭐ |
| 案2: 日次集計専用テーブル `kpi.inbound_daily_summary` | Medium | 中 | **大** | ⭐⭐⭐ | ⭐ |
| 案5: `stg.receive_king_final` の複合インデックス | Medium | 小 | 中 | ⭐⭐ | - |
| 案10: Redis によるグローバルキャッシュ | Medium | 中 | 中～大 | ⭐ | ⭐⭐ |
| 案12: `/dashboard/all` で一括取得 | Medium | 中 | 中 | ⭐ | ⭐ |
| 案8: 不要な `ORDER BY` の削除 | Low | 小 | 小～中 | ⭐ | - |
| 案3: 月次目標テーブルの正規化 | Low | 小 | 小 | - | ⭐ |
| 案11: フロントエンド SWR | Low | 小 | 中（UX改善） | ⭐ | ⭐ |

---

### 5.2 推奨ロードマップ

#### **Phase 1: 即効性のある軽量施策（1週間以内）**

1. **案4**: `stg.receive_shogun_final` / `stg.receive_shogun_flash` に `slip_date` のインデックス追加
   - **実装**: マイグレーションファイル作成 → `alembic upgrade`
   - **検証**: EXPLAIN ANALYZE で Sequential Scan → Index Scan を確認
   - **期待**: `/inbound/daily` のレスポンスタイム 20～30% 短縮

2. **案9**: `BuildTargetCardUseCase` の TTL を 60秒 → 3600秒（1時間）に延長
   - **実装**: UseCase のコード変更（1行）
   - **期待**: キャッシュヒット率向上（複数ユーザー環境で効果大）

3. **案8**: `mart.v_receive_daily` の定義から不要な `ORDER BY` を削除
   - **実装**: マイグレーションで VIEW を再作成
   - **検証**: プランナーの実行計画を確認
   - **期待**: 軽微な高速化（ただし案1の前提作業として有用）

---

#### **Phase 2: 本命施策（2～3週間）**

4. **案1**: `mart.v_receive_daily` を `mart.mv_receive_daily` として MV 化 ⭐
   - **実装**:
     1. 新規マイグレーションファイル作成
     2. MV 作成 + UNIQUE INDEX + 週次インデックス
     3. Repository の SQL テンプレートを `mv_receive_daily` に置換
     4. CSV アップロード後の REFRESH ロジック追加
   - **検証**:
     - EXPLAIN ANALYZE で CTE の再計算が減っているか確認
     - `/inbound/daily` のレスポンスタイム計測（目標: 1秒未満）
   - **期待**: `/inbound/daily` のレスポンスタイム **50～70% 短縮**

5. **案6**: `/inbound/daily` のクエリを段階的に分割
   - **実装**:
     1. メインクエリ（当期間のみ）を新規 SQL として作成
     2. Repository に `fetch_daily_simple()` メソッド追加
     3. UseCase で「前月/前年比較は必要時のみ取得」ロジック実装
   - **検証**: 複雑な CTE が不要になり、プランニング時間が短縮されているか確認
   - **期待**: `/inbound/daily` のレスポンスタイム **さらに 20～30% 短縮**

---

#### **Phase 3: 中長期的な最適化（1～2ヶ月）**

6. **案7**: `/dashboard/target` の累積計算を MV に統合
   - **実装**:
     1. `mart.v_target_card_per_day` の定義を拡張（累積カラム追加）
     2. MV を再作成（`mv_target_card_per_day_enhanced`）
     3. Repository のクエリを単純な `SELECT * WHERE ddate = :date` に変更
   - **検証**: EXPLAIN ANALYZE で複数 CTE が消えているか確認
   - **期待**: `/dashboard/target` のレスポンスタイム **50～60% 短縮**

7. **案2**: 日次集計専用テーブル `kpi.inbound_daily_summary` を導入
   - **実装**:
     1. 新規テーブル作成（マイグレーション）
     2. CSV アップロード後の Upsert ロジック追加
     3. 過去データのバックフィル（バッチスクリプト）
     4. Repository を新テーブル参照に切り替え
   - **検証**: `/inbound/daily` のクエリが単純な `SELECT * FROM kpi.inbound_daily_summary` になっているか確認
   - **期待**: `/inbound/daily` のレスポンスタイム **1秒未満を安定達成**

8. **案10**: Redis によるグローバルキャッシュ導入
   - **実装**:
     1. Redis サーバーをインフラに追加
     2. UseCase または Repository 層にキャッシュロジック追加
     3. CSV アップロード後のキャッシュ無効化処理
   - **検証**: マルチインスタンス環境でキャッシュが共有されているか確認
   - **期待**: 複数ユーザー環境でレスポンスタイム **さらに 30～50% 短縮**

---

#### **Phase 4: 付加価値施策（必要に応じて）**

9. **案5**: `stg.receive_king_final` の複合インデックス最適化
10. **案12**: `/dashboard/all` で一括取得
11. **案3**: 月次目標テーブルの正規化
12. **案11**: フロントエンド SWR 導入

---

### 5.3 特に `/inbound/daily` を 1秒前後まで短縮するための本命案

✅ **必ず実施**:
- **案1**: `mart.v_receive_daily` の MV 化
- **案4**: `stg.receive_shogun_*` にインデックス追加

✅ **強く推奨**:
- **案6**: クエリの段階的分割

✅ **理想形**:
- **案2**: 日次集計専用テーブル導入（最終的に MV も不要になる）

---

## 6. 次のステップ

### 6.1 EXPLAIN ANALYZE の実行（推奨）

現状のクエリのボトルネックを正確に把握するため、以下のクエリで `EXPLAIN ANALYZE` を取得してください。

```sql
-- 1. /inbound/daily のクエリ
EXPLAIN (ANALYZE, BUFFERS, TIMING) 
<inbound_pg_repository__get_daily_with_comparisons.sql の内容>;

-- 2. /dashboard/target のクエリ
EXPLAIN (ANALYZE, BUFFERS, TIMING)
<dashboard_target_repo__get_by_date_optimized.sql の内容>;
```

**確認ポイント**:
- Seq Scan が発生している箇所（特に stg テーブル）
- CTE の Materialize が複数回実行されているか
- Sort や Hash Join のコスト
- 実行時間の内訳（Planning Time vs Execution Time）

---

### 6.2 段階的な実装とモニタリング

1. **Phase 1 を実装**（インデックス追加 + キャッシュ延長）
2. **負荷テストを実施**（Apache Bench, Locust など）
3. **本番環境でのレスポンスタイムを計測**（APM ツール: New Relic, Datadog など）
4. **効果が不十分なら Phase 2 へ進む**（MV 化 + クエリ分割）
5. **継続的に EXPLAIN ANALYZE でボトルネック確認**

---

### 6.3 運用ルールの整備

- **MV のリフレッシュ**: CSV アップロード完了後に自動実行（`make refresh-mv` のようなタスク）
- **キャッシュの無効化**: CSV アップロード後に `BuildTargetCardUseCase.clear_cache()` を呼び出す
- **インデックスのメンテナンス**: 定期的に `REINDEX` または `VACUUM ANALYZE` を実行
- **モニタリング**: Slow Query Log で 1秒以上かかるクエリをアラート

---

## 7. まとめ

### 現状の課題

- `/inbound/daily`: `mart.v_receive_daily` が VIEW であるため、毎回 stg テーブルの集計を実行 → 複数 CTE + 前月/前年比較で重い
- `/dashboard/target`: 複数の CTE で MV を何度もスキャン + `v_receive_daily` を2回参照 → 累積計算のコストが大きい

### 最優先で実施すべき施策

1. **`mart.v_receive_daily` の MV 化**（案1） → **効果大**
2. **`stg.receive_shogun_*` にインデックス追加**（案4） → **即効性あり**
3. **目標値キャッシュの TTL 延長**（案9） → **簡単で効果あり**

### 最終目標

- `/inbound/daily` のレスポンスタイム: **1秒未満**
- `/dashboard/target` のレスポンスタイム: **500ms 以内**

---

**次のアクション**: Phase 1 の実装（インデックス追加 + キャッシュ延長）を開始し、EXPLAIN ANALYZE で効果を検証してください。

---

**以上、DB パフォーマンス調査レポートでした。**
