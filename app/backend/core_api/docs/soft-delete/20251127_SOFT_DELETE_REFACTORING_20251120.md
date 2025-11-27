# 論理削除（Soft Delete）対応リファクタリング実装レポート

**実施日**: 2025-11-20  
**対象**: stg.shogun_final_receive / stg.shogun_flash_receive およびその他将軍テーブル  
**目的**: 論理削除済みデータを集計から自動的に除外し、データ整合性を保証する

---

## 📋 変更概要

### 対象テーブル
- `stg.shogun_flash_receive`
- `stg.shogun_final_receive`
- `stg.shogun_flash_yard`
- `stg.shogun_final_yard`
- `stg.shogun_flash_shipment`
- `stg.shogun_final_shipment`

### 実施内容

1. **アクティブ行専用ビューの作成**（`stg.active_*`）
2. **mart スキーマのビュー更新**（is_deleted フィルタ追加）
3. **部分インデックスの追加**（性能最適化）
4. **リグレッションテスト SQL の作成**

---

## 🔧 実装詳細

### 1. アクティブ行専用ビューの作成

**Alembic リビジョン**: `20251120_160000000_create_active_shogun_views.py`

**作成されたビュー**:
```sql
CREATE OR REPLACE VIEW stg.active_shogun_flash_receive AS
SELECT * FROM stg.shogun_flash_receive WHERE is_deleted = false;

CREATE OR REPLACE VIEW stg.active_shogun_final_receive AS
SELECT * FROM stg.shogun_final_receive WHERE is_deleted = false;

-- 同様に yard, shipment についても作成
```

**目的**:
- 論理削除済み行を自動的に除外する共通ビューを提供
- WHERE 句での is_deleted 条件の書き忘れを防止
- コードの可読性と保守性を向上

---

### 2. mart スキーマのビュー更新

**Alembic リビジョン**: `20251120_170000000_update_mart_views_for_soft_delete.py`

#### 2.1 mart.v_receive_daily の変更

**Before**:
```sql
WITH r_shogun_final AS (
    SELECT
        s.slip_date AS ddate,
        SUM(s.net_weight) / 1000.0 AS receive_ton,
        COUNT(DISTINCT s.receive_no) AS vehicle_count,
        SUM(s.amount) AS sales_yen
    FROM stg.shogun_final_receive s
    WHERE s.slip_date IS NOT NULL
    GROUP BY s.slip_date
),
r_shogun_flash AS (
    SELECT
        f.slip_date AS ddate,
        SUM(f.net_weight) / 1000.0 AS receive_ton,
        COUNT(DISTINCT f.receive_no) AS vehicle_count,
        SUM(f.amount) AS sales_yen
    FROM stg.shogun_flash_receive f
    WHERE f.slip_date IS NOT NULL
    GROUP BY f.slip_date
)
...
```

**After**:
```sql
WITH r_shogun_final AS (
    SELECT
        s.slip_date AS ddate,
        SUM(s.net_weight) / 1000.0 AS receive_ton,
        COUNT(DISTINCT s.receive_no) AS vehicle_count,
        SUM(s.amount) AS sales_yen
    FROM stg.active_shogun_final_receive s  -- ✅ active_* ビューに変更
    WHERE s.slip_date IS NOT NULL
      AND s.is_deleted = false  -- ✅ 明示的なフィルタも追加（防御的プログラミング）
    GROUP BY s.slip_date
),
r_shogun_flash AS (
    SELECT
        f.slip_date AS ddate,
        SUM(f.net_weight) / 1000.0 AS receive_ton,
        COUNT(DISTINCT f.receive_no) AS vehicle_count,
        SUM(f.amount) AS sales_yen
    FROM stg.active_shogun_flash_receive f  -- ✅ active_* ビューに変更
    WHERE f.slip_date IS NOT NULL
      AND f.is_deleted = false  -- ✅ 明示的なフィルタも追加
    GROUP BY f.slip_date
)
...
```

**変更点**:
- `stg.shogun_final_receive` → `stg.active_shogun_final_receive`
- `stg.shogun_flash_receive` → `stg.active_shogun_flash_receive`
- WHERE 句に `AND is_deleted = false` を明示的に追加（2重防御）

---

#### 2.2 mart.v_shogun_flash_receive_daily の変更

**Before**:
```sql
SELECT
    s.slip_date::date AS slip_date,
    'shogun_flash_receive'::text AS csv_kind,
    COUNT(*) AS row_count
FROM stg.shogun_flash_receive s
WHERE s.slip_date IS NOT NULL
GROUP BY s.slip_date
ORDER BY s.slip_date DESC;
```

**After**:
```sql
SELECT
    s.slip_date::date AS slip_date,
    'shogun_flash_receive'::text AS csv_kind,
    COUNT(*) AS row_count
FROM stg.shogun_flash_receive s
WHERE s.slip_date IS NOT NULL
  AND s.is_deleted = false  -- ✅ 論理削除済み行を除外
GROUP BY s.slip_date
ORDER BY s.slip_date DESC;
```

**変更点**:
- WHERE 句に `AND s.is_deleted = false` を追加

---

#### 2.3 mart.v_shogun_final_receive_daily の変更

**Before / After**: 上記と同様に `is_deleted = false` を追加

---

### 3. 部分インデックスの追加

**Alembic リビジョン**: `20251120_180000000_optimize_is_deleted_indexes.py`

**追加されたインデックス**:
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_shogun_flash_receive_active
ON stg.shogun_flash_receive (slip_date, upload_file_id)
WHERE is_deleted = false;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_shogun_final_receive_active
ON stg.shogun_final_receive (slip_date, upload_file_id)
WHERE is_deleted = false;

-- 同様に yard, shipment についても作成
```

**メリット**:
- アクティブ行のみにインデックスを張ることで、インデックスサイズを削減
- 論理削除率が高くなっても、クエリパフォーマンスが維持される
- `WHERE is_deleted = false` 条件付きクエリが高速化

**既存インデックスとの関係**:
- 既存の `idx_shogun_flash_receive_is_deleted` は保持（全行対象）
- 部分インデックスは `is_deleted = false` のクエリで優先的に使用される
- 論理削除行のクエリ（`is_deleted = true`）は既存インデックスを使用

---

### 4. データクリーンアップ

**実施内容**:
- `is_deleted` カラムが NULL の行を一括で `false` に更新
- 既存データの整合性を確保

**SQL**:
```sql
UPDATE stg.shogun_flash_receive
SET is_deleted = false
WHERE is_deleted IS NULL;
```

**備考**:
- 既存の Alembic マイグレーション（`20251119_130000000`）で `NOT NULL DEFAULT false` が定義済み
- このクリーンアップは念のための処理（本来 NULL は存在しない想定）

---

## 📊 影響範囲

### 変更されたビュー/マテビュー

| ビュー/マテビュー | 変更内容 | 影響 |
|---|---|---|
| `mart.v_receive_daily` | active_* ビュー使用 + is_deleted フィルタ | ✅ 論理削除行が集計から除外される |
| `mart.v_shogun_flash_receive_daily` | is_deleted フィルタ追加 | ✅ 論理削除行が集計から除外される |
| `mart.v_shogun_final_receive_daily` | is_deleted フィルタ追加 | ✅ 論理削除行が集計から除外される |
| `mart.mv_target_card_per_day` | 間接的に影響（v_receive_daily 経由） | ⚠️ REFRESH が必要 |
| `mart.mv_inb5y_week_profile_min` | 間接的に影響（v_receive_daily 経由） | ⚠️ REFRESH が必要 |
| `mart.mv_inb_avg5y_day_biz` | 間接的に影響（v_receive_daily 経由） | ⚠️ REFRESH が必要 |
| `mart.mv_inb_avg5y_weeksum_biz` | 間接的に影響（v_receive_daily 経由） | ⚠️ REFRESH が必要 |
| `mart.mv_inb_avg5y_day_scope` | 間接的に影響（v_receive_daily 経由） | ⚠️ REFRESH が必要 |

### Python コード

| ファイル | 変更内容 |
|---|---|
| `app/presentation/routers/database/router.py` | ✅ すでに `is_deleted = false` フィルタ適用済み（変更不要） |
| `app/infra/adapters/upload/shogun_csv_repository.py` | 変更不要（INSERT のみ） |

---

## 🚀 マイグレーション実行手順

### 1. Alembic マイグレーションの適用

```bash
# ローカル開発環境
make al-up

# または
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head
```

**実行されるリビジョン**:
1. `20251120_160000000` - active_* ビューの作成
2. `20251120_170000000` - mart ビューの更新
3. `20251120_180000000` - 部分インデックスの追加

---

### 2. マテリアライズドビューのリフレッシュ

```bash
# 全MVを一括リフレッシュ
make refresh-mv

# または個別に実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
```

---

### 3. 統計情報の更新

```bash
# テーブルの統計情報を更新（クエリプランナーの最適化）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_flash_receive;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_final_receive;"
```

---

### 4. リグレッションテストの実行

```bash
# テスト SQL を実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -f /path/to/test_is_deleted_regression.sql
```

**テスト項目**:
1. stg テーブルの論理削除状況の確認
2. slip_date 別の論理削除分布
3. 日次集計の比較（フィルタあり／なし）
4. active_* ビューの動作確認
5. mart.v_receive_daily の結果検証
6. インデックス使用状況の確認（EXPLAIN ANALYZE）
7. upload_file_id ごとの論理削除状況
8. カレンダー API の結果確認

---

## ✅ 検証ポイント

### 1. 論理削除率の確認

```sql
SELECT
    'shogun_flash_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_receive;
```

**期待結果**:
- `deleted_percent` が 0% に近い場合は影響なし
- 5% 以上の場合は、集計結果に有意な変化が生じる可能性あり

---

### 2. 集計結果の差異確認

```sql
-- フィルタあり／なしで集計を比較
WITH 
unfiltered AS (
    SELECT slip_date, SUM(net_weight) / 1000.0 AS ton
    FROM stg.shogun_flash_receive
    WHERE slip_date IS NOT NULL
    GROUP BY slip_date
),
filtered AS (
    SELECT slip_date, SUM(net_weight) / 1000.0 AS ton
    FROM stg.shogun_flash_receive
    WHERE slip_date IS NOT NULL AND is_deleted = false
    GROUP BY slip_date
)
SELECT
    u.slip_date,
    u.ton AS ton_unfiltered,
    f.ton AS ton_filtered,
    u.ton - f.ton AS ton_diff
FROM unfiltered u
JOIN filtered f ON u.slip_date = f.slip_date
WHERE u.ton <> f.ton
ORDER BY u.slip_date DESC
LIMIT 10;
```

**期待結果**:
- 差異がない場合: 論理削除行が存在しない
- 差異がある場合: 差分が論理削除行の影響

---

### 3. インデックス使用確認

```sql
EXPLAIN ANALYZE
SELECT slip_date, COUNT(*) AS row_count
FROM stg.shogun_flash_receive
WHERE slip_date >= CURRENT_DATE - INTERVAL '30 days'
  AND is_deleted = false
GROUP BY slip_date;
```

**期待結果**:
- `Index Scan using idx_shogun_flash_receive_active` が表示される
- 実行時間が高速化される

---

## 🔄 ロールバック手順

マイグレーションに問題がある場合、以下の手順で元に戻せます。

```bash
# 3つのリビジョンをロールバック
make al-down  # 1回目: 20251120_180000000 を戻す
make al-down  # 2回目: 20251120_170000000 を戻す
make al-down  # 3回目: 20251120_160000000 を戻す

# または特定リビジョンまで一括ロールバック
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini downgrade 20251120_150000000
```

---

## 📈 性能への影響

### 想定される改善点

1. **クエリ性能の向上**
   - 部分インデックスにより、is_deleted = false のクエリが高速化
   - インデックスサイズが削減され、メモリ効率が向上

2. **保守性の向上**
   - active_* ビューにより、is_deleted 条件の書き忘れを防止
   - コードの可読性が向上

3. **データ整合性の保証**
   - 論理削除済み行が自動的に集計から除外される
   - 誤って削除済みデータを含む集計が発生しない

### 想定されるオーバーヘッド

- **ビュー経由のクエリ**: 軽微（ビューは単純な SELECT * + WHERE）
- **部分インデックスの維持**: INSERT/UPDATE 時に若干のオーバーヘッド（ただし、既存の is_deleted インデックスと大差なし）

---

## 📝 今後の運用

### マテリアライズドビューのリフレッシュタイミング

1. **日次バッチ**: ETL 完了後に自動リフレッシュ
2. **手動リフレッシュ**: データ修正後に必要に応じて実行

```bash
# 日次バッチスクリプトに追加
make refresh-mv
```

### 論理削除の運用

- アップロード時に同日データを自動的に論理削除（既存実装）
- 論理削除率が高くなった場合、定期的に物理削除を検討（VACUUM FULL など）

---

## 🎯 まとめ

### 実施した変更

✅ **アクティブ行専用ビューの作成** (`stg.active_*`)  
✅ **mart ビューの更新** (is_deleted フィルタ追加)  
✅ **部分インデックスの追加** (性能最適化)  
✅ **リグレッションテスト SQL の作成**

### 変更の影響

- **データ整合性**: ✅ 論理削除済み行が集計から自動除外
- **性能**: ✅ 部分インデックスによる高速化
- **保守性**: ✅ active_* ビューによる書き忘れ防止
- **外部 API**: ✅ 変更なし（内部ロジックのみ変更）

### 次のアクション

1. ✅ Alembic マイグレーション適用
2. ✅ マテリアライズドビューのリフレッシュ
3. ✅ リグレッションテストの実行
4. ✅ 本番環境への展開（STG 環境で検証後）

---

**作成者**: GitHub Copilot (Claude Sonnet 4.5)  
**レビュー**: [担当者名]  
**承認**: [承認者名]

