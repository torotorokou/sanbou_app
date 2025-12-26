# 論理削除（Soft Delete）対応リファクタリング - クイックスタートガイド

## 📋 概要

このガイドは、`stg.shogun_final_receive` と `stg.shogun_flash_receive` テーブルの論理削除対応リファクタリングの実行手順を簡潔にまとめたものです。

詳細なドキュメントは `docs/SOFT_DELETE_REFACTORING_20251120.md` を参照してください。

---

## 🚀 クイックスタート（自動実行）

### 1. スクリプトに実行権限を付与

```bash
chmod +x scripts/apply_soft_delete_refactoring.sh
```

### 2. スクリプトを実行

```bash
./scripts/apply_soft_delete_refactoring.sh
```

このスクリプトは以下を自動的に実行します:

- ✅ Alembic マイグレーションの適用（3つのリビジョン）
- ✅ マテリアライズドビューのリフレッシュ（5つのMV）
- ✅ テーブル統計情報の更新（6テーブル）
- ✅ リグレッションテストの実行

---

## 🔧 手動実行（ステップバイステップ）

自動スクリプトを使わず、手動で実行する場合は以下の手順に従ってください。

### Step 1: Alembic マイグレーションの適用

```bash
# 現在のリビジョンを確認
make al-cur

# マイグレーションを適用
make al-up

# 適用後のリビジョンを確認
make al-cur
```

**適用されるリビジョン**:

1. `20251120_160000000` - アクティブ行専用ビュー（stg.active\_\*）の作成
2. `20251120_170000000` - mart ビューの更新（is_deleted フィルタ追加）
3. `20251120_180000000` - 部分インデックスの追加

---

### Step 2: マテリアライズドビューのリフレッシュ

```bash
# 全MVを一括リフレッシュ
make refresh-mv

# または個別に実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb5y_week_profile_min;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_biz;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_weeksum_biz;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_scope;"
```

---

### Step 3: テーブル統計情報の更新

```bash
# 各テーブルの統計情報を更新
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_flash_receive;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_final_receive;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_flash_yard;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_final_yard;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_flash_shipment;"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_final_shipment;"
```

---

### Step 4: リグレッションテストの実行

```bash
# テストSQLを実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev < scripts/sql/test_is_deleted_regression.sql
```

**主なテスト項目**:

1. 論理削除状況の確認
2. slip_date 別の削除分布
3. 集計結果の比較（フィルタあり／なし）
4. active\_\* ビューの動作確認
5. インデックス使用状況の確認

---

## ✅ 検証チェックリスト

### 1. マイグレーションの適用確認

```bash
# 現在のリビジョンが 20251120_180000000 以降であることを確認
make al-cur
```

### 2. active\_\* ビューの存在確認

```sql
-- psql で実行
SELECT schemaname, viewname
FROM pg_views
WHERE schemaname = 'stg'
  AND viewname LIKE 'active_%'
ORDER BY viewname;
```

**期待される結果**: 6つのビューが表示される

- `active_shogun_flash_receive`
- `active_shogun_final_receive`
- `active_shogun_flash_yard`
- `active_shogun_final_yard`
- `active_shogun_flash_shipment`
- `active_shogun_final_shipment`

---

### 3. 部分インデックスの存在確認

```sql
-- psql で実行
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'stg'
  AND indexname LIKE '%_active'
ORDER BY indexname;
```

**期待される結果**: 6つのインデックスが表示される

---

### 4. 論理削除率の確認

```sql
SELECT
    'shogun_flash_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_receive

UNION ALL

SELECT
    'shogun_final_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_final_receive;
```

---

### 5. API エンドポイントの動作確認

```bash
# ヘルスチェック
curl http://localhost:8001/health

# カレンダーAPI（論理削除済みデータが含まれないこと）
curl "http://localhost:8001/database/upload-calendar?year=2025&month=11"

# ダッシュボードAPI（集計結果が正常であること）
curl "http://localhost:8001/dashboard/target?date=2025-11-01"
```

---

## 🔄 ロールバック手順

問題が発生した場合、以下の手順でロールバックできます。

```bash
# 3つのリビジョンを順番にロールバック
make al-down  # 1回目: 20251120_180000000
make al-down  # 2回目: 20251120_170000000
make al-down  # 3回目: 20251120_160000000

# または一括ロールバック
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini downgrade 20251120_150000000
```

---

## 📊 性能測定

### インデックス使用状況の確認

```sql
EXPLAIN ANALYZE
SELECT
    slip_date,
    COUNT(*) AS row_count,
    SUM(net_weight) / 1000.0 AS total_ton
FROM stg.shogun_flash_receive
WHERE slip_date >= CURRENT_DATE - INTERVAL '30 days'
  AND is_deleted = false
GROUP BY slip_date
ORDER BY slip_date DESC;
```

**期待される結果**:

- `Index Scan using idx_shogun_flash_receive_active` が表示される
- 実行時間が短い（数ミリ秒～数十ミリ秒）

---

## 📝 トラブルシューティング

### エラー: "relation does not exist"

**原因**: マイグレーションが正しく適用されていない

**解決策**:

```bash
make al-cur  # 現在のリビジョンを確認
make al-up   # マイグレーションを再実行
```

---

### エラー: "CONCURRENTLY cannot be executed in a transaction block"

**原因**: トランザクション内で CONCURRENTLY インデックス作成を実行している

**解決策**:

- Alembic マイグレーションは自動的にトランザクション外で実行されます
- 手動で実行する場合は、個別のコマンドとして実行してください

---

### マテリアライズドビューのリフレッシュが遅い

**原因**: データ量が多い、またはインデックスが未作成

**解決策**:

1. ANALYZE を実行してテーブル統計を更新
2. 部分インデックスが作成されているか確認
3. バックグラウンドで実行（nohup など）

---

## 📚 関連ドキュメント

- **詳細実装レポート**: `docs/SOFT_DELETE_REFACTORING_20251120.md`
- **テストSQL**: `scripts/sql/test_is_deleted_regression.sql`
- **マイグレーションファイル**:
  - `20251120_160000000_create_active_shogun_views.py`
  - `20251120_170000000_update_mart_views_for_soft_delete.py`
  - `20251120_180000000_optimize_is_deleted_indexes.py`

---

## 🎯 完了チェック

すべて完了したら、以下をチェックしてください:

- [ ] Alembic マイグレーションが 20251120_180000000 まで適用されている
- [ ] active\_\* ビューが6つ作成されている
- [ ] 部分インデックスが6つ作成されている
- [ ] マテリアライズドビューが5つリフレッシュされている
- [ ] テーブル統計が更新されている
- [ ] リグレッションテストがパスしている
- [ ] API エンドポイントが正常に動作している

---

**作成日**: 2025-11-20  
**最終更新**: 2025-11-20
