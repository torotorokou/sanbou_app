# CSV アップロード確認カレンダー機能 - 実装完了レポート

実装日: 2025-11-19

## 概要

CSV アップロード確認カレンダー機能を実装しました。この機能により、以下が実現されます:

1. **論理削除機能**: アップロードファイルを物理削除せず、`is_deleted=true` で管理
2. **重複チェックの改善**: 論理削除されたファイルは重複チェックから除外
3. **カレンダー表示**: 有効なファイルのデータのみを日次集計してカレンダー表示
4. **再アップロード許可**: 削除後の同一 CSV の再アップロードが可能

---

## 実装内容

### 1. データベースマイグレーション

#### ✅ Step 2: 論理削除カラムの追加
**ファイル**: `20251119_100000000_add_soft_delete_to_upload_file.py`

```sql
ALTER TABLE log.upload_file
  ADD COLUMN is_deleted boolean NOT NULL DEFAULT false,
  ADD COLUMN deleted_at timestamptz NULL,
  ADD COLUMN deleted_by text NULL;
```

#### ✅ Step 3: 部分ユニークインデックス
**ファイル**: `20251119_110000000_partial_unique_index_for_soft_delete.py`

既存の UNIQUE 制約を部分ユニークインデックスに置き換え:

```sql
-- 既存制約を削除
DROP CONSTRAINT uq_upload_file_hash_type_csv_status;

-- 部分ユニークインデックスを作成（is_deleted=false のみに適用）
CREATE UNIQUE INDEX ux_upload_file_hash_type_csv_status_active
  ON log.upload_file (file_hash, file_type, csv_type, processing_status)
  WHERE is_deleted = false;
```

**効果**: 論理削除されたレコードはユニーク制約から除外され、同じファイルの再アップロードが可能に。

#### ✅ Step 6: 日次集計ビューの作成
**ファイル**: `20251119_120000000_create_csv_calendar_daily_views.py`

6つの個別ビュー + 1つの統合ビューを作成:

```sql
-- 個別ビュー例（受入速報）
CREATE OR REPLACE VIEW mart.v_shogun_flash_receive_daily AS
SELECT
    s.slip_date::date              AS data_date,
    'shogun_flash_receive'::text   AS csv_kind,
    COUNT(*)                       AS row_count
FROM stg.receive_shogun_flash s
JOIN log.upload_file uf
  ON uf.id = s.upload_file_id
 AND uf.is_deleted = false  -- 論理削除されていないレコードのみ
WHERE s.slip_date IS NOT NULL
GROUP BY s.slip_date::date;

-- 統合ビュー
CREATE OR REPLACE VIEW mart.v_csv_calendar_daily AS
SELECT * FROM mart.v_shogun_flash_receive_daily
UNION ALL
SELECT * FROM mart.v_shogun_flash_yard_daily
UNION ALL
SELECT * FROM mart.v_shogun_flash_shipment_daily
UNION ALL
SELECT * FROM mart.v_shogun_final_receive_daily
UNION ALL
SELECT * FROM mart.v_shogun_final_yard_daily
UNION ALL
SELECT * FROM mart.v_shogun_final_shipment_daily;
```

---

### 2. アプリケーション層の修正

#### ✅ Step 4: 重複チェックロジックの修正
**ファイル**: `app/infra/adapters/upload/raw_data_repository.py`

```python
# テーブル定義に論理削除カラムを追加
Column('is_deleted', Integer, nullable=False, server_default=text('false')),
Column('deleted_at', DateTime(timezone=True), nullable=True),
Column('deleted_by', Text, nullable=True),

# 重複チェックに is_deleted=False 条件を追加
def check_duplicate_upload(...):
    result = self.db.execute(
        self.upload_file_table.select().where(
            self.upload_file_table.c.csv_type == csv_type,
            self.upload_file_table.c.file_hash == file_hash,
            self.upload_file_table.c.file_type == file_type,
            self.upload_file_table.c.processing_status == 'success',
            self.upload_file_table.c.is_deleted == False,  # ← 追加
        )
    )

# 論理削除メソッドを追加
def soft_delete_upload_file(self, file_id: int, deleted_by: Optional[str] = None):
    self.db.execute(
        self.upload_file_table.update()
        .where(self.upload_file_table.c.id == file_id)
        .values(
            is_deleted=True,
            deleted_at=datetime.utcnow(),
            deleted_by=deleted_by,
        )
    )
```

---

### 3. API エンドポイントの追加

#### ✅ Step 7: カレンダー API
**ファイル**: `app/presentation/routers/database/router.py`

**GET /database/upload-calendar**
- 指定年月のアップロード状況を取得
- 論理削除されたデータは除外

```python
@router.get("/upload-calendar")
def get_upload_calendar(year: int, month: int, db: Session = Depends(get_db)):
    """
    CSV アップロードカレンダー用の日次集計データを取得
    
    Returns:
        {
            "items": [
                {
                    "date": "2025-11-01",
                    "csvKind": "shogun_flash_receive",
                    "rowCount": 1234
                },
                ...
            ]
        }
    """
```

**DELETE /database/upload-calendar/{upload_file_id}**
- アップロードファイルを論理削除
- カレンダーから該当データが消える

```python
@router.delete("/upload-calendar/{upload_file_id}")
def delete_upload_file(upload_file_id: int, deleted_by: Optional[str] = None, ...):
    """
    アップロードファイルを論理削除
    
    Returns:
        {"status": "deleted", "uploadFileId": <id>}
    """
```

---

## マイグレーション実行手順

### 1. マイグレーション適用

```bash
# マイグレーションを順次適用
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head
```

実行されるマイグレーション:
1. `20251119_100000000` - is_deleted カラム追加
2. `20251119_110000000` - 部分ユニークインデックス作成
3. `20251119_120000000` - カレンダービュー作成

### 2. データベース確認

```sql
-- 1. log.upload_file のカラム確認
\d log.upload_file

-- 2. 部分ユニークインデックスの確認
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'log' 
  AND tablename = 'upload_file'
  AND indexname LIKE '%active%';

-- 3. カレンダービューの確認
\dv mart.v_csv_calendar_daily
```

---

## 動作確認シナリオ

### シナリオ 1: 通常のアップロード → 削除 → 再アップロード

```bash
# 1. CSV をアップロード
curl -X POST http://localhost:8000/database/upload/syogun_csv \
  -F "receive=@test/test_receive_mini.csv"

# upload_file_id が返される（例: 123）

# 2. データベースで確認
SELECT * FROM log.upload_file ORDER BY id DESC LIMIT 1;
# is_deleted = false を確認

SELECT * FROM mart.v_csv_calendar_daily 
WHERE csv_kind = 'shogun_flash_receive' 
ORDER BY data_date DESC LIMIT 10;
# 該当日にデータが表示されることを確認

# 3. 論理削除を実行
curl -X DELETE http://localhost:8000/database/upload-calendar/123

# 4. データベースで確認
SELECT * FROM log.upload_file WHERE id = 123;
# is_deleted = true を確認

SELECT * FROM mart.v_csv_calendar_daily 
WHERE csv_kind = 'shogun_flash_receive' 
ORDER BY data_date DESC LIMIT 10;
# 該当データが表示されないことを確認

# 5. 同じ CSV を再アップロード
curl -X POST http://localhost:8000/database/upload/syogun_csv \
  -F "receive=@test/test_receive_mini.csv"

# 新しい upload_file_id が返される（重複エラーにならない）
```

### シナリオ 2: カレンダー API の動作確認

```bash
# 1. 2025年11月のカレンダーデータを取得
curl -X GET "http://localhost:8000/database/upload-calendar?year=2025&month=11"

# 期待されるレスポンス:
{
  "items": [
    {
      "date": "2025-11-01",
      "csvKind": "shogun_flash_receive",
      "rowCount": 1234
    },
    {
      "date": "2025-11-01",
      "csvKind": "shogun_flash_yard",
      "rowCount": 567
    },
    ...
  ]
}
```

### シナリオ 3: SQL での直接確認

```sql
-- 全 upload_file を確認（削除済み含む）
SELECT 
    id,
    csv_type,
    file_type,
    processing_status,
    is_deleted,
    deleted_at,
    uploaded_at
FROM log.upload_file 
ORDER BY id DESC 
LIMIT 10;

-- 有効な upload_file のみ確認
SELECT 
    id,
    csv_type,
    file_type,
    processing_status,
    uploaded_at
FROM log.upload_file 
WHERE is_deleted = false
ORDER BY id DESC 
LIMIT 10;

-- カレンダービューの日次集計を確認
SELECT 
    data_date,
    csv_kind,
    row_count
FROM mart.v_csv_calendar_daily
WHERE data_date >= '2025-11-01' 
  AND data_date <= '2025-11-30'
ORDER BY data_date, csv_kind;

-- 特定日の詳細を確認
SELECT 
    s.slip_date::date as data_date,
    COUNT(*) as row_count,
    uf.id as upload_file_id,
    uf.file_name,
    uf.is_deleted
FROM stg.receive_shogun_flash s
JOIN log.upload_file uf ON uf.id = s.upload_file_id
WHERE s.slip_date::date = '2025-11-01'
GROUP BY s.slip_date::date, uf.id, uf.file_name, uf.is_deleted;
```

---

## トラブルシューティング

### 問題 1: 部分ユニークインデックス作成エラー

**エラー**: `constraint "uq_upload_file_hash_type_csv_status" of relation "upload_file" does not exist`

**原因**: 既存制約名が異なる

**解決策**:
```sql
-- 現在の制約を確認
SELECT conname FROM pg_constraint 
WHERE conrelid = 'log.upload_file'::regclass;

-- 実際の制約名で DROP を実行
DROP CONSTRAINT <実際の制約名>;
```

### 問題 2: カレンダービューにデータが表示されない

**確認ポイント**:
1. `upload_file_id` が stg テーブルに正しくセットされているか
2. `is_deleted = false` のレコードが存在するか
3. `slip_date` が NULL でないか

**確認クエリ**:
```sql
-- stg テーブルの upload_file_id 設定状況
SELECT 
    COUNT(*) as total_rows,
    COUNT(upload_file_id) as with_upload_file_id,
    COUNT(CASE WHEN upload_file_id IS NULL THEN 1 END) as null_upload_file_id
FROM stg.receive_shogun_flash;

-- upload_file の is_deleted 状況
SELECT 
    is_deleted,
    COUNT(*) as count
FROM log.upload_file
GROUP BY is_deleted;
```

---

## まとめ

### 実装完了項目

✅ Step 1: 現状確認  
✅ Step 2: `is_deleted` カラム追加  
✅ Step 3: 部分ユニークインデックス  
✅ Step 4: 重複チェックロジック修正  
✅ Step 5: stg テーブル紐付け確認（既存実装済み）  
✅ Step 6: 日次集計ビュー作成  
✅ Step 7: カレンダー API 実装  
✅ Step 8: 動作確認手順作成

### 利点

1. **柔軟な運用**: 誤って削除したデータを復元可能（`is_deleted=false` に戻すだけ）
2. **履歴管理**: 削除日時・削除者を記録
3. **再アップロード対応**: 削除後の同一ファイル再登録が可能
4. **カレンダー整合性**: 削除したデータは自動的にカレンダーから除外

### 今後の拡張案

1. **物理削除機能**: 一定期間経過後の自動物理削除バッチ
2. **復元 API**: `is_deleted=true` を `false` に戻す機能
3. **削除履歴ビュー**: 削除されたファイルの一覧表示
4. **通知機能**: 削除時のメール通知など

---

## 関連ファイル

### マイグレーション
- `app/backend/core_api/migrations/alembic/versions/20251119_100000000_add_soft_delete_to_upload_file.py`
- `app/backend/core_api/migrations/alembic/versions/20251119_110000000_partial_unique_index_for_soft_delete.py`
- `app/backend/core_api/migrations/alembic/versions/20251119_120000000_create_csv_calendar_daily_views.py`

### アプリケーション
- `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`
- `app/backend/core_api/app/presentation/routers/database/router.py`

### フロントエンド連携
- API エンドポイント: `/database/upload-calendar` (GET)
- API エンドポイント: `/database/upload-calendar/{id}` (DELETE)
