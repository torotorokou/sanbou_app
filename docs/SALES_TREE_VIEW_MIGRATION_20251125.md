# 売上ツリービュー移行マイグレーション実装レポート

## 実装日
2025-11-25

## 概要
sandbox スキーマに配置されていた売上ツリー関連ビューを、本番運用スキーマ（mart）に移行しました。

## 背景

### 移行前の状態
- `sandbox.v_sales_tree_detail_base`: 詳細データビュー（stg.shogun_flash_receive から集計）
- `sandbox.v_sales_tree_daily`: 日次集計ビュー（sandbox.mv_sales_tree_daily を参照）
- `sandbox.mv_sales_tree_daily`: Materialized View（実体データ保持）

これらは試験的に sandbox スキーマに配置されていましたが、実運用で使用するため mart スキーマに移行する必要がありました。

### 移行方針
- 互換期間として、旧 sandbox.* ビューは残す
- アプリケーションコードを mart.* に切り替え
- 別 revision で sandbox 側を DROP する予定

## 実装内容

### 1. Alembic マイグレーション作成

#### ファイルパス
```
app/backend/core_api/migrations/alembic/versions/
  └── 20251125_100000000_move_sales_tree_views_from_sandbox_to_mart.py
```

#### Revision情報
- **Revision ID**: `20251125_100000000`
- **Down Revision**: `20251121_100000000`
- **作成日時**: 2025-11-25 10:00:00

#### upgrade() 処理内容

1. **既存ビューのDROP**（再実行でも安全）
   ```sql
   DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
   DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
   ```

2. **mart.v_sales_tree_detail_base 作成**
   ```sql
   CREATE VIEW mart.v_sales_tree_detail_base AS
   SELECT
       COALESCE(sales_date, slip_date) AS sales_date,
       sales_staff_cd   AS rep_id,
       sales_staff_name AS rep_name,
       client_cd        AS customer_id,
       client_name      AS customer_name,
       item_cd          AS item_id,
       item_name,
       amount           AS amount_yen,
       net_weight       AS qty_kg,
       receive_no       AS slip_no,
       category_name,
       aggregate_item_cd,
       aggregate_item_name,
       id               AS source_id,
       upload_file_id,
       source_row_no
   FROM stg.shogun_flash_receive s
   WHERE
       category_cd = 1
       AND COALESCE(sales_date, slip_date) IS NOT NULL
       AND COALESCE(is_deleted, false) = false;
   ```

3. **mart.v_sales_tree_daily 作成**
   ```sql
   CREATE VIEW mart.v_sales_tree_daily AS
   SELECT
       sales_date,
       rep_id,
       rep_name,
       customer_id,
       customer_name,
       item_id,
       item_name,
       amount_yen,
       qty_kg,
       slip_count
   FROM sandbox.mv_sales_tree_daily;
   ```
   
   注意: 現時点では `sandbox.mv_sales_tree_daily` を参照。将来的に mart スキーマに移行予定。

4. **権限付与**
   ```sql
   GRANT SELECT ON mart.v_sales_tree_detail_base TO app_user;
   GRANT SELECT ON mart.v_sales_tree_daily TO app_user;
   ```

#### downgrade() 処理内容
```sql
DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
```

### 2. アプリケーションコード修正

#### 修正ファイル
```
app/backend/core_api/app/infra/adapters/sales_tree/sales_tree_repository.py
```

#### 修正内容
全ての `sandbox.v_sales_tree_daily` 参照を `mart.v_sales_tree_daily` に変更：

- モジュールドキュメント（3箇所）
- `fetch_summary()` メソッド
- `fetch_daily_series()` メソッド
- `fetch_pivot()` メソッド
- `get_sales_reps()` メソッド
- `get_customers()` メソッド
- `get_items()` メソッド
- `export_csv()` メソッド

合計 **10箇所** を一括変更。

## 動作確認手順

### 前提条件
1. Docker コンテナが起動していること
2. DB に接続できること
3. `sandbox.mv_sales_tree_daily` にデータが存在すること

### 1. マイグレーション適用

#### コマンド
```bash
# Alembic マイグレーションを実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head
```

または、VS Code のタスクを使用：
```
タスク: alembic: upgrade head
```

#### 期待する出力
```
[mart.v_sales_tree_detail_base] Creating VIEW for sales tree detail data...
[mart.v_sales_tree_detail_base] VIEW created successfully.
[mart.v_sales_tree_daily] Creating VIEW for daily aggregated sales tree data...
[mart.v_sales_tree_daily] VIEW created successfully.
[mart.v_sales_tree_*] Granting SELECT to app_user...
[mart.v_sales_tree_*] Permissions granted successfully.
[INFO] sandbox.v_sales_tree_* views remain intact for compatibility.
```

### 2. ビュー存在確認

#### コマンド
```bash
# psql でビューの存在を確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dv+ mart.v_sales_tree_detail_base"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dv+ mart.v_sales_tree_daily"
```

#### 期待する結果
- ビューが存在することを確認
- Owner が `postgres` であること
- Access privileges に `app_user=r/postgres` が含まれること

### 3. データ取得確認

#### mart.v_sales_tree_detail_base
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "
    SELECT 
      sales_date, 
      rep_name, 
      customer_name, 
      item_name, 
      amount_yen, 
      qty_kg 
    FROM mart.v_sales_tree_detail_base 
    LIMIT 10;
  "
```

#### mart.v_sales_tree_daily
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "
    SELECT 
      sales_date, 
      rep_name, 
      customer_name, 
      item_name, 
      amount_yen, 
      qty_kg, 
      slip_count 
    FROM mart.v_sales_tree_daily 
    LIMIT 10;
  "
```

#### データ件数確認
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "SELECT COUNT(*) FROM mart.v_sales_tree_daily;"
```

### 4. アプリケーション動作確認

#### バックエンド API テスト
```bash
# サマリーデータ取得
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  curl -X POST http://localhost:8000/core_api/analytics/sales-tree/summary \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-10-01",
    "date_to": "2025-10-31",
    "mode": "customer",
    "rep_ids": [],
    "filter_ids": [],
    "top_n": 10,
    "sort_by": "amount",
    "order": "desc"
  }'
```

#### 期待する結果
- ステータスコード: 200
- JSON レスポンス
- データが存在する場合は、営業別のサマリーデータが返る

#### フロントエンド確認
1. ブラウザで `http://localhost:5173/analytics/sales-tree` にアクセス
2. 営業を選択
3. データが表示されることを確認
4. モード切り替え（顧客/品目/日付）が動作することを確認

### 5. 互換性確認

旧 sandbox ビューが残っていることを確認：
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dv sandbox.v_sales_tree_*"
```

期待する結果:
- `sandbox.v_sales_tree_detail_base`
- `sandbox.v_sales_tree_daily`

が存在すること。

## トラブルシューティング

### 1. マイグレーション失敗: relation does not exist

**原因**: `sandbox.mv_sales_tree_daily` が存在しない

**確認コマンド**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\d sandbox.mv_sales_tree_daily"
```

**解決策**:
- Materialized View を作成するか、
- マイグレーション定義を修正して、直接 `stg.shogun_flash_receive` から集計する

### 2. API が 500 エラーを返す

**原因**: アプリケーションコードが古いスキーマを参照している可能性

**確認**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev logs core_api | tail -50
```

**解決策**:
- コンテナを再起動
  ```bash
  docker compose -f docker/docker-compose.dev.yml -p local_dev restart core_api
  ```

### 3. 権限エラー: permission denied

**原因**: `app_user` に SELECT 権限が付与されていない

**確認**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dp mart.v_sales_tree_daily"
```

**解決策**:
```sql
GRANT SELECT ON mart.v_sales_tree_detail_base TO app_user;
GRANT SELECT ON mart.v_sales_tree_daily TO app_user;
```

### 4. データが空で返る

**原因**: `sandbox.mv_sales_tree_daily` にデータがない

**確認**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "SELECT COUNT(*) FROM sandbox.mv_sales_tree_daily;"
```

**解決策**:
- CSV アップロードを実行してデータを投入
- または、Materialized View を REFRESH
  ```sql
  REFRESH MATERIALIZED VIEW sandbox.mv_sales_tree_daily;
  ```

## Rollback 手順

マイグレーションを戻す場合：

```bash
# 1つ前の revision に戻す
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini downgrade -1

# または、特定の revision に戻す
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini downgrade 20251121_100000000
```

注意: downgrade 後は、アプリケーションコードも `sandbox` に戻す必要があります。

## 今後の対応

### 1. sandbox ビューの削除
互換期間を経て、安全が確認できたら別 revision で削除：

```python
# 将来の revision
def upgrade():
    op.execute("DROP VIEW IF EXISTS sandbox.v_sales_tree_daily CASCADE;")
    op.execute("DROP VIEW IF EXISTS sandbox.v_sales_tree_detail_base CASCADE;")
```

### 2. Materialized View の移行
`sandbox.mv_sales_tree_daily` を `mart.mv_sales_tree_daily` に移行し、
`mart.v_sales_tree_daily` の参照先を変更：

```python
# 将来の revision
def upgrade():
    # 1. mart.mv_sales_tree_daily を作成
    op.execute("""
        CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
        SELECT ... FROM stg.shogun_flash_receive ...;
    """)
    
    # 2. mart.v_sales_tree_daily を再定義
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_sales_tree_daily AS
        SELECT * FROM mart.mv_sales_tree_daily;
    """)
```

### 3. インデックスの最適化
パフォーマンスを向上させるため、適切なインデックスを追加：

```sql
-- stg.shogun_flash_receive への複合インデックス
CREATE INDEX IF NOT EXISTS idx_shogun_flash_receive_sales_tree
ON stg.shogun_flash_receive(sales_date, sales_staff_cd, client_cd, item_cd)
WHERE category_cd = 1 AND COALESCE(is_deleted, false) = false;

-- Materialized View へのインデックス
CREATE INDEX IF NOT EXISTS idx_mv_sales_tree_daily_composite
ON mart.mv_sales_tree_daily(sales_date, rep_id, customer_id, item_id);
```

## 関連ドキュメント
- [SALES_TREE_API_IMPLEMENTATION_20251121.md](./SALES_TREE_API_IMPLEMENTATION_20251121.md)
- [FSD_ARCHITECTURE_GUIDE.md](./FSD_ARCHITECTURE_GUIDE.md)

## 変更履歴
- 2025-11-25 10:00: マイグレーション作成・適用完了
- 2025-11-25 10:30: アプリケーションコード修正完了
