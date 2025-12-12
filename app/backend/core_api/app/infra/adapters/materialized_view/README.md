# Materialized View Refresher

マテリアライズドビュー（MV）の自動更新を担当するモジュール。

## 概要

CSVアップロード成功時に、関連するマテリアライズドビューを自動的に更新します。
Clean Architectureに従い、Infra層に配置されています。

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

4. 手動でMV更新を実行:
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_receive_daily;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;
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

## 関連ファイル

- `materialized_view_refresher.py` - MVリフレッシャー本体
- `upload_shogun_csv_uc.py` - CSVアップロードUseCase（MV更新呼び出し元）
- `di_providers.py` - DI設定
- `migrations/alembic/versions/*_create_mv_*.py` - MV作成マイグレーション
