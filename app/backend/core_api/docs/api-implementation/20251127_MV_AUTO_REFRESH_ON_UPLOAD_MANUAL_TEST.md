# 受入CSV成功時マテビュー自動更新機能 - 動作確認手順

## 概要

受入CSV（receive）のアップロードが成功したタイミングで、PostgreSQL のマテリアライズドビュー `mart.mv_target_card_per_day` を自動更新する機能を実装しました。

## 前提条件

1. PostgreSQL が起動していること
2. マイグレーションが完了していること（`mart.mv_target_card_per_day` が存在すること）
3. core_api が起動していること

```bash
# Docker環境の起動
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d

# マイグレーション実行（必要に応じて）
make al-up
```

## 手動テスト手順

### ステップ1: マテビューの初期状態を確認

```bash
# DBに接続
docker compose -f docker/docker-compose.dev.yml -p local_dev exec db psql -U myuser -d sanbou_dev

# マテビューの最終更新時刻を確認
SELECT schemaname, matviewname, last_refresh
FROM pg_matviews
WHERE matviewname = 'mv_target_card_per_day';

# マテビューのデータ件数を確認
SELECT COUNT(*) FROM mart.mv_target_card_per_day;

# 最新の受入データ日付を確認
SELECT MAX(ddate) FROM mart.mv_target_card_per_day;
```

### ステップ2: 受入CSVをアップロード

ブラウザまたはAPIクライアント（例：Postman, curl）を使用してCSVをアップロードします。

#### ブラウザから（推奨）

1. フロントエンドにアクセス: http://localhost:3000
2. Database > Upload ページに移動
3. 受入一覧CSV（receive）を選択してアップロード
4. アップロード成功のメッセージを確認

#### curlから

```bash
curl -X POST "http://localhost:8000/database/upload/syogun_csv_flash" \
  -F "receive=@/path/to/your/receive.csv"
```

### ステップ3: ログでマテビュー更新を確認

```bash
# core_api のログを確認
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f core_api

# 以下のようなログが出力されるはず:
# INFO: Marked receive upload as success: 2550 rows
# INFO: Starting materialized view refresh for csv_type='receive'
# INFO: Refreshing materialized view: mart.mv_target_card_per_day
# INFO: Successfully refreshed materialized view: mart.mv_target_card_per_day
# INFO: Successfully refreshed materialized views for csv_type='receive'
```

### ステップ4: マテビューが更新されたことを確認

```bash
# DBに接続
docker compose -f docker/docker-compose.dev.yml -p local_dev exec db psql -U myuser -d sanbou_dev

# マテビューの最終更新時刻が新しくなっていることを確認
SELECT schemaname, matviewname, last_refresh
FROM pg_matviews
WHERE matviewname = 'mv_target_card_per_day';

# データ件数の変化を確認
SELECT COUNT(*) FROM mart.mv_target_card_per_day;

# 最新の受入データ日付が反映されているか確認
SELECT MAX(ddate) FROM mart.mv_target_card_per_day;
```

### ステップ5: upload_file テーブルの確認

```bash
# 最新のアップロードログを確認
SELECT id, csv_type, file_name, processing_status, row_count, uploaded_at
FROM log.upload_file
ORDER BY uploaded_at DESC
LIMIT 5;

# csv_type='receive' かつ processing_status='success' の行が存在することを確認
```

## エラーケースのテスト

### ケース1: 受入以外のCSVをアップロード

```bash
# yard や shipment をアップロードした場合、マテビュー更新は実行されない
curl -X POST "http://localhost:8000/database/upload/syogun_csv_flash" \
  -F "yard=@/path/to/your/yard.csv"

# ログで以下のメッセージを確認:
# DEBUG: No csv_types provided for MV refresh（または該当MVがないメッセージ）
```

### ケース2: アップロード失敗時

不正なCSVファイルをアップロードした場合、マテビュー更新は実行されません。

```bash
# 不正なCSVをアップロード
curl -X POST "http://localhost:8000/database/upload/syogun_csv_flash" \
  -F "receive=@/path/to/invalid.csv"

# upload_file.processing_status が 'failed' になることを確認
SELECT id, csv_type, processing_status, error_message
FROM log.upload_file
ORDER BY uploaded_at DESC
LIMIT 1;

# マテビュー更新は実行されない（ログに "Starting materialized view refresh" が出力されない）
```

### ケース3: マテビュー更新失敗時

マテビュー更新に失敗した場合でも、アップロード処理自体は成功します。

```sql
-- テスト用: マテビューを意図的に壊す（実施しないでください！）
-- DROP MATERIALIZED VIEW mart.mv_target_card_per_day;
```

アップロードを実行すると:

- upload_file.processing_status は 'success' になる
- ログに ERROR レベルのメッセージが記録される
- ユーザーにはアップロード成功が返される（MVエラーは内部で処理）

## ユニットテストの実行

```bash
# テストファイルの場所
# /home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/core_api/tests/test_mv_refresh.py

# テスト実行（pytest）
cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/core_api
pytest tests/test_mv_refresh.py -v
```

## トラブルシューティング

### マテビュー更新が実行されない

1. `mv_refresher` が DI されているか確認

   - ログに "MaterializedViewRefresher not injected" が出力される場合、DI設定を確認

2. csv_type が 'receive' であるか確認

   - yard や shipment の場合、マテビュー更新は実行されない（MV_MAPPINGS に定義されていない）

3. processing_status が 'success' であるか確認
   - 失敗したアップロードではマテビュー更新は実行されない

### マテビュー更新が遅い

`REFRESH MATERIALIZED VIEW CONCURRENTLY` は安全ですが、データ量が多い場合は時間がかかります。

- 対処法: バックグラウンドジョブで非同期実行を検討
- 現状: 同期実行のため、アップロードAPIのレスポンスが遅くなる可能性あり

### エラーログが出力される

```
ERROR: Failed to refresh materialized view mart.mv_target_card_per_day: ...
```

考えられる原因:

1. マテビューが存在しない → マイグレーション実行
2. UNIQUE INDEX が存在しない → CONCURRENTLY オプションが使えない
3. DB接続エラー → DB の状態を確認

## 参考情報

### 関連ファイル

- マテビュー更新リポジトリ: `app/backend/core_api/app/infra/adapters/materialized_view/materialized_view_refresher.py`
- UseCase: `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`
- DI設定: `app/backend/core_api/app/config/di_providers.py`
- マイグレーション: `app/backend/core_api/migrations/alembic/versions/20251117_135913797_create_mv_target_card_per_day.py`

### 手動でマテビューを更新する方法

```bash
# Makefile経由
make refresh-mv-target-card

# または直接SQL実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev \
  -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
```

### モニタリング

```sql
-- マテビューのサイズと更新頻度を確認
SELECT
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size,
    last_refresh
FROM pg_matviews
WHERE matviewname = 'mv_target_card_per_day';
```

## 次のステップ

1. フロントエンドでの実測レスポンスタイム計測
2. 他の csv_type（shipment, yard）へのMV追加検討
3. バックグラウンドジョブでの非同期実行検討
4. Grafana でのモニタリング設定
