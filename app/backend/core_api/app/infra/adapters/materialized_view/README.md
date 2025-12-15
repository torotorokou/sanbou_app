# Materialized View Refresher

マテリアライズドビュー（MV）の自動更新を担当するモジュール。

## 概要

CSVアップロード成功時に、関連するマテリアライズドビューを自動的に更新します。
Clean Architectureに従い、Infra層に配置されています。

## トランザクション設計（2025-12-12更新）

### 原則

**トランザクション境界はUseCaseレベルで管理**します。Repository層では`commit()`や`rollback()`を呼びません。

### CSV削除時のトランザクション

```python
# DeleteUploadScopeUseCase の実行フロー:
try:
    # 1. CSV削除（RawDataRepository）
    affected_rows = repository.soft_delete_by_date_and_kind(...)
    
    # 2. MV更新（MaterializedViewRefresher）
    mv_refresher.refresh_for_csv_kind(csv_kind)
    
    # 3. 正常終了時: FastAPIのget_db()が自動的にcommit()
except Exception:
    # 4. エラー時: FastAPIのget_db()が自動的にrollback()
    raise
```

### メリット

1. **原子性の保証**: CSV削除とMV更新が同一トランザクション内で実行され、両方成功するか両方失敗するかのどちらか
2. **データ整合性**: 片方だけ成功してデータ不整合になることを防止
3. **責務の明確化**: Repository層はデータ操作のみ、トランザクション管理はUseCase/API層

## 対応CSV種別

### receive（受入CSV）

将軍速報CSV（flash）と将軍最終CSV（final）の **両方に対応** しています。

#### 更新されるMV

1. **`mart.mv_receive_daily`** - 日次受入集計MV（基礎データ）
   - 将軍最終版（final）を優先
   - 最終版がない日付は将軍速報版（flash）を使用
   - どちらもなければKingシステムのデータを使用

2. **`mart.mv_target_card_per_day`** - 目標カードMV
   - `mv_receive_daily` に依存
   - 依存関係の順序で更新されます（mv_receive_daily → mv_target_card_per_day）
   - **各MV更新後にcommit()を実行**し、次のMVが最新データを確実に参照できるようにします

**注意**: 
- MV名はクォートなしの標準PostgreSQL形式を使用（`mart.mv_receive_daily`）
- 依存関係のあるMVは、基礎MVの更新とコミット後に更新されます

#### データの優先順位

```
1. stg.v_active_shogun_final_receive (最優先)
   ↓ 存在しない日付は
2. stg.v_active_shogun_flash_receive (次優先)
   ↓ 存在しない日付は
3. stg.receive_king_final (最低優先)
```

### yard（ヤードCSV）

将来実装予定

### shipment（出荷CSV）

将来実装予定

## 使用方法

### 1. DIコンテナ経由で注入

```python
from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher

# FastAPI Depends
def get_mv_refresher(db: Session = Depends(get_db)) -> MaterializedViewRefresher:
    return MaterializedViewRefresher(db)

# UseCase内で使用
class SomeUseCase:
    def __init__(self, mv_refresher: MaterializedViewRefresher):
        self.mv_refresher = mv_refresher
```

### 2. CSV種別ごとに更新

```python
# receive CSV アップロード成功時
mv_refresher.refresh_for_csv_type("receive")

# 将軍速報CSV（flash）でも将軍最終CSV（final）でも同じメソッドを呼ぶ
# MVは自動的にfinal優先、なければflashを使用する
```

### 3. 個別MV更新（内部メソッド）

```python
# 通常は使用しない（デバッグ用）
mv_refresher._refresh_single_mv("mart.mv_receive_daily")
```

## エラーハンドリング

### UNIQUE INDEX不足

```
ERROR: UNIQUE INDEX が存在しない可能性があります。
CONCURRENTLY オプションには UNIQUE INDEX が必要です。
migration を確認してください。
```

**対処方法:**
```sql
-- UNIQUE INDEX を作成
CREATE UNIQUE INDEX idx_mv_receive_daily_ddate 
ON mart.mv_receive_daily (ddate);
```

### MV不存在

```
ERROR: マテリアライズドビュー 'mart.mv_xxx' が存在しません。
```

**対処方法:**
Alembic migration を実行して MV を作成してください。

### 更新エラー

MV更新に失敗してもCSVアップロード処理自体は成功扱いになります。
エラーはログに記録され、次回のアップロード時に再試行されます。

### 複数MV更新時の部分失敗

**動作仕様（2025-12-12修正）:**
- 複数のMVを更新する際、1つのMV更新が失敗しても、残りのMVの更新を継続します
- 例: `mv_receive_daily` の更新に失敗しても、`mv_target_card_per_day` の更新を試みます
- 各MVの成功/失敗はログに個別に記録されます

**ログ例（部分失敗時）:**
```
[MV_REFRESH] Starting refresh for csv_type='receive'
[MV_REFRESH] Refreshing MV: mart.mv_receive_daily
[MV_REFRESH] ❌ MV refresh failed: mart.mv_receive_daily - UNIQUE INDEX が存在しない...
[MV_REFRESH] Refreshing MV: mart.mv_target_card_per_day
[MV_REFRESH] ✅ MV refresh successful: mart.mv_target_card_per_day (730 rows)
[MV_REFRESH] ⚠️ Refresh completed with errors for csv_type='receive': 1/2 succeeded
```

この仕様により、依存関係のないMV間で障害が伝播することを防ぎます。

## ログ出力

### 成功時

```
[MV_REFRESH] Starting refresh for csv_type='receive'
[MV_REFRESH] Refreshing MV: mart.mv_receive_daily
[MV_REFRESH] ✅ MV refresh successful: mart.mv_receive_daily (365 rows)
[MV_REFRESH] Refreshing MV: mart.mv_target_card_per_day
[MV_REFRESH] ✅ MV refresh successful: mart.mv_target_card_per_day (730 rows)
[MV_REFRESH] ✅ All MVs refreshed successfully for csv_type='receive' (2/2)
```

### エラー時

```
[MV_REFRESH] Starting refresh for csv_type='receive'
[MV_REFRESH] Refreshing MV: mart.mv_receive_daily
[MV_REFRESH] ❌ MV refresh failed: mart.mv_receive_daily - UNIQUE INDEX が存在しない可能性があります。
[MV_REFRESH] MV refresh failed: mart.mv_receive_daily
[MV_REFRESH] ⚠️ Refresh completed with errors for csv_type='receive': 0/2 succeeded
```

## 新しいMVの追加方法

1. `MV_MAPPINGS` に追加:

```python
MV_MAPPINGS = {
    "receive": [
        fq(SCHEMA_MART, MV_RECEIVE_DAILY),
        fq(SCHEMA_MART, MV_TARGET_CARD_PER_DAY),
        fq(SCHEMA_MART, "新しいMV名"),  # ← 追加
    ],
}
```

2. Migration でMVとUNIQUE INDEXを作成:

```python
# migrations/alembic/versions/YYYYMMDD_HHMMSS_create_new_mv.py
def upgrade():
    op.execute("""
        CREATE MATERIALIZED VIEW mart.新しいMV名 AS
        SELECT ... ;
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX idx_新しいMV名_pk
        ON mart.新しいMV名 (主キー列);
    """)
```

3. `backend_shared.db.names` に定数を追加:

```python
# backend_shared/src/backend_shared/db/names.py
MV_NEW_VIEW = "新しいMV名"
```

## 注意事項

- **CONCURRENTLY オプション**: ロックを最小化するために使用
  - UNIQUE INDEX が必要
  - 初回更新時は CONCURRENTLY を使わない方が良い（データがない場合）
  
- **更新時間**: MVのサイズによって数秒～数十秒かかる場合あり
  
- **依存関係**: MVが他のMVに依存している場合は、更新順序に注意
  - 現状: `mv_receive_daily` → `mv_target_card_per_day` の順で更新

## 環境変数設計

### Migration の環境変数対応

Migration (`20251212_100000000_add_unique_indexes_for_mvs.py`) は環境変数から動的にDB情報を取得します：

- **POSTGRES_USER**: アプリケーションDBユーザー（例: `myapp_user_dev`, `myapp_user_stg`, `myapp_user_prod`）
- **POSTGRES_DB**: データベース名（例: `myapp_dev`, `myapp_stg`, `myapp_prod`）

#### メリット

1. **環境ごとにハードコードされたマッピング不要**
   - 新しい環境（demo, test, etc.）を追加してもmigration変更不要
   
2. **環境分離の保証**
   - STG環境では `myapp_user_stg` のみ、PROD環境では `myapp_user_prod` のみに権限付与
   
3. **柔軟な設定管理**
   - `env/.env.local_dev`, `env/.env.vm_stg`, `env/.env.vm_prod` で一元管理

#### 環境変数設定例

```bash
# env/.env.local_dev
POSTGRES_USER=myapp_user_dev
POSTGRES_DB=myapp_dev

# env/.env.vm_stg
POSTGRES_USER=myapp_user_stg
POSTGRES_DB=myapp_stg

# env/.env.vm_prod
POSTGRES_USER=myapp_user_prod
POSTGRES_DB=myapp_prod
```

## トラブルシューティング

### MVが更新されない

1. ログを確認:
   ```
   docker logs <container_id> | grep "MV_REFRESH"
   ```

2. `mv_refresher` が注入されているか確認:
   ```
   [MV_REFRESH] ⚠️ MaterializedViewRefresher not injected, skipping MV refresh.
   ```
   → DI設定を確認

3. CSV保存が成功しているか確認:
   ```sql
   SELECT * FROM log.upload_file 
   WHERE processing_status = 'success' 
   ORDER BY uploaded_at DESC LIMIT 10;
   ```

4. UNIQUE INDEXが存在するか確認:
   ```sql
   SELECT indexname, indexdef 
   FROM pg_indexes 
   WHERE tablename IN ('mv_receive_daily', 'mv_target_card_per_day')
   AND indexname LIKE 'ux_%';
   ```
   → 存在しない場合は migration 20251212_100000000 を実行

5. 手動でMV更新を実行:
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_receive_daily;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;
   ```

### 権限エラー (permission denied)

**エラーメッセージ:**
```
permission denied for materialized view mv_receive_daily
```

**原因:**
- Alembic migration実行ユーザー (postgres/admin_user) がMVを作成
- アプリケーション実行ユーザー (myapp_user_*) がMVにアクセス
- SELECT権限が付与されていない

**対策:**
Migration 20251212_100000000 で対策済み。以下の権限が自動付与される：
- myapp_user_dev (local_dev環境)
- myapp_user_stg (vm_stg環境)
- myapp_user_prod (vm_prod環境)

**手動で権限を付与する場合:**
```sql
-- 各環境のアプリユーザーに権限付与
GRANT USAGE ON SCHEMA mart TO myapp_user_dev;  -- local_dev
GRANT SELECT ON mart.mv_receive_daily TO myapp_user_dev;
GRANT SELECT ON mart.mv_target_card_per_day TO myapp_user_dev;

-- STG環境の場合
GRANT USAGE ON SCHEMA mart TO myapp_user_stg;
GRANT SELECT ON mart.mv_receive_daily TO myapp_user_stg;
GRANT SELECT ON mart.mv_target_card_per_day TO myapp_user_stg;

-- PROD環境の場合
GRANT USAGE ON SCHEMA mart TO myapp_user_prod;
GRANT SELECT ON mart.mv_receive_daily TO myapp_user_prod;
GRANT SELECT ON mart.mv_target_card_per_day TO myapp_user_prod;
```

**確認方法:**
```sql
-- アプリユーザーでMVにアクセスできるか確認
\c myapp_dev myapp_user_dev
SELECT COUNT(*) FROM mart.mv_receive_daily;  -- 正常に実行できればOK
```

### MVの内容を確認

```sql
-- 日次受入集計
SELECT * FROM mart.mv_receive_daily 
ORDER BY ddate DESC LIMIT 10;

-- 目標カード
SELECT * FROM mart.mv_target_card_per_day
ORDER BY ddate DESC LIMIT 10;
```

## STG/PROD環境へのデプロイ

### 事前準備（重要）

Migration 20251212_100000000 は以下を実行します：
1. MVにUNIQUE INDEXを追加（REFRESH CONCURRENTLY を有効化）
2. アプリユーザー (sanbou_app_*) にSELECT権限を付与

**この migration を実行しないと、本番環境でMV更新が失敗します。**

### デプロイ手順

#### STG環境 (vm_stg)

```bash
# 1. STG VMにSSH接続
ssh <vm_stg_host>

# 2. プロジェクトディレクトリに移動
cd /path/to/sanbou_app

# 3. 最新コードをpull
git pull origin main

# 4. Alembic migration を実行
make al-up ENV=vm_stg

# 5. アプリケーションを再起動
make restart ENV=vm_stg

# 6. 動作確認
make logs ENV=vm_stg S=core_api | grep "MV_REFRESH"
```

#### PROD環境 (vm_prod)

```bash
# 1. PROD VMにSSH接続
ssh <vm_prod_host>

# 2. プロジェクトディレクトリに移動
cd /path/to/sanbou_app

# 3. 最新コードをpull
git pull origin main

# 4. Alembic migration を実行（慎重に）
make al-up ENV=vm_prod

# 5. アプリケーションを再起動
make restart ENV=vm_prod

# 6. 動作確認
make logs ENV=vm_prod S=core_api | grep "MV_REFRESH"

# 7. MVの内容を確認
docker compose -f docker/docker-compose.prod.yml -p vm_prod exec -T db \
  psql -U myapp_user_prod -d myapp_prod -c \
  "SELECT COUNT(*) FROM mart.mv_receive_daily;"
```

### デプロイ後の確認

```bash
# 1. UNIQUE INDEXが作成されているか
docker compose ... exec -T db psql -U myuser -d <db_name> -c "
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('mv_receive_daily', 'mv_target_card_per_day')
AND indexname LIKE 'ux_%';
"
# 期待: ux_mv_receive_daily_ddate, ux_mv_target_card_per_day_ddate

# 2. アプリユーザーがMVにアクセスできるか
docker compose ... exec -T db psql -U myapp_user_<env> -d <db_name> -c "
SELECT COUNT(*) FROM mart.mv_receive_daily;
"
# 期待: 数値が返る（権限エラーが出ない）

# 3. CSV アップロードでMVが更新されるか
# フロントエンドからCSVをアップロード → ログを確認
docker logs <container_id> | grep "MV_REFRESH"
# 期待: 
# [MV_REFRESH] Starting refresh for csv_type='receive'
# [MV_REFRESH] ✅ MV refresh successful: mart.mv_receive_daily (XXX rows)
```

## 関連ファイル

- `materialized_view_refresher.py` - MVリフレッシャー本体
- `upload_shogun_csv_uc.py` - CSVアップロードUseCase（MV更新呼び出し元）
- `di_providers.py` - DI設定
- `migrations/alembic/versions/20251212_100000000_add_unique_indexes_for_mvs.py` - UNIQUE INDEX作成・権限付与migration
- `migrations/alembic/versions/*_create_mv_*.py` - MV作成マイグレーション
