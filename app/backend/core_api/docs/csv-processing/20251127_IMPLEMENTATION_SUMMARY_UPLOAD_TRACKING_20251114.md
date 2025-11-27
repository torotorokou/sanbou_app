# 将軍CSVアップロード機能拡張: 実装完了サマリー

## 実装日
2025-11-14

## 概要
CSVアップロード処理に `upload_file_id` と `source_row_no` によるトラッキング機能、および既存カラムを使った重複チェック機能を追加しました。

---

## 実装内容

### 1. 調査・設計ドキュメント
- **詳細ドキュメント**: `docs/SHOGUN_CSV_UPLOAD_FILE_ID_TRACKING_IMPLEMENTATION.md`
  - 現状の構成分析
  - スキーマ変更設計
  - 処理フロー修正案
  - 重複チェックロジック
  - 動作確認手順

### 2. Alembicマイグレーションファイル（3つ）

#### 2-1. raw層テーブル変更
**ファイル**: `migrations/alembic/versions/20251114_130000000_add_upload_tracking_to_raw_tables.py`

```python
# 変更内容:
# - file_id → upload_file_id (リネーム)
# - row_number → source_row_no (リネーム)
# - UNIQUE制約: (upload_file_id, source_row_no)
# - INDEX: upload_file_id

# 対象:
# - raw.receive_raw
# - raw.yard_raw
# - raw.shipment_raw
```

#### 2-2. stg層テーブル変更
**ファイル**: `migrations/alembic/versions/20251114_130100000_add_upload_tracking_to_stg_tables.py`

```python
# 変更内容:
# - upload_file_id カラム追加 (INT NOT NULL)
# - source_row_no カラム追加 (INT NOT NULL)
# - INDEX: (upload_file_id, source_row_no)

# 対象:
# - stg.receive_shogun_flash / yard_shogun_flash / shipment_shogun_flash
# - stg.receive_shogun_final / yard_shogun_final / shipment_shogun_final
```

#### 2-3. 重複チェック用インデックス
**ファイル**: `migrations/alembic/versions/20251114_130200000_add_duplicate_check_indexes.py`

```python
# 変更内容:
# - log.upload_file にフォールバック用複合インデックスを追加
# - INDEX: (csv_type, file_name, file_size_bytes, row_count, processing_status)
```

---

## 今後の実装タスク（コード修正）

### Phase 1: Repository層の拡張

#### Task 1-1: RawDataRepository に重複チェックメソッド追加
**ファイル**: `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`

```python
def check_duplicate_upload(
    self,
    csv_type: str,
    file_hash: str,
    file_name: Optional[str] = None,
    file_size_bytes: Optional[int] = None,
    row_count: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    同一ファイルが既に成功済みかチェック
    
    Returns:
        Optional[Dict]: 重複あり → {'id': ..., 'uploaded_at': ..., 'file_name': ...}
                        重複なし → None
    """
    # 実装詳細は SHOGUN_CSV_UPLOAD_FILE_ID_TRACKING_IMPLEMENTATION.md 参照
```

#### Task 1-2: RawDataRepository の save_*_raw メソッド修正
```python
def save_receive_raw(self, file_id: int, df: pd.DataFrame) -> int:
    """
    Args:
        file_id: upload_file.id（= upload_file_id）
        df: upload_file_id, source_row_no を含む DataFrame
    """
    # df に upload_file_id, source_row_no が含まれていることを前提
    # カラム名マッピングで保持
```

#### Task 1-3: ShogunCsvRepository の save_csv_by_type メソッド修正
**ファイル**: `app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`

```python
def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
    """
    Args:
        df: 型変換済み + upload_file_id, source_row_no を含む DataFrame
    """
    # upload_file_id, source_row_no を必須カラムとして保持
    required_columns = ['upload_file_id', 'source_row_no']
    valid_columns = self.table_gen.get_columns(csv_type) + required_columns
    # フィルタリング時に upload_file_id, source_row_no を除外しない
```

### Phase 2: UseCase層の修正

#### Task 2-1: UploadSyogunCsvUseCase.execute() に重複チェック追加
**ファイル**: `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`

```python
async def execute(self, receive, yard, shipment, file_type="FLASH", uploaded_by=None):
    # ... 入力チェック、ファイルタイプ検証
    
    # ★ 重複チェック（log.upload_file 作成前）
    if self.raw_data_repo:
        duplicates = {}
        for csv_type, uf in uploaded_files.items():
            duplicate = self.raw_data_repo.check_duplicate_upload(...)
            if duplicate:
                duplicates[csv_type] = duplicate
        
        # 全ファイルが重複の場合はエラー
        if len(duplicates) == len(uploaded_files):
            return ErrorApiResponse(
                code="DUPLICATE_UPLOAD",
                detail="アップロードされたすべてのCSVファイルは既に取り込み済みです",
                metadata={"duplicates": {...}},
                status_code=409,
            )
    
    # ... 以降の処理
```

#### Task 2-2: source_row_no の採番
```python
# CSV読込後、各行に source_row_no を追加
dfs, read_error = await self._read_csv_files(uploaded_files)

for csv_type, df in dfs.items():
    df['source_row_no'] = range(1, len(df) + 1)  # 1-indexed
```

#### Task 2-3: _save_data() メソッドに upload_file_ids を渡す
```python
raw_result = await self._save_data(
    self.raw_writer,
    raw_cleaned_dfs,
    uploaded_files,
    "raw",
    upload_file_ids=upload_file_ids  # ★追加
)

async def _save_data(
    self,
    writer: IShogunCsvWriter,
    formatted_dfs: Dict[str, pd.DataFrame],
    uploaded_files: Dict[str, UploadFile],
    layer_name: str,
    upload_file_ids: Optional[Dict[str, int]] = None,  # ★追加
) -> Dict[str, dict]:
    for csv_type, df in formatted_dfs.items():
        if upload_file_ids and csv_type in upload_file_ids:
            df['upload_file_id'] = upload_file_ids[csv_type]
        
        # source_row_no は既に追加済み
        count = await run_in_threadpool(writer.save_csv_by_type, csv_type, df)
```

---

## マイグレーション実行手順

```bash
# 1. マイグレーション実行
cd /home/koujiro/work_env/22.Work_React/sanbou_app
make al-up

# 2. 現在のバージョン確認
make al-cur

# 期待される出力:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# 20251114_130200000 (head)

# 3. DBで確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev << 'EOF'
-- raw.receive_raw のカラム確認
\d raw.receive_raw

-- stg.receive_shogun_flash のカラム確認
\d stg.receive_shogun_flash

-- log.upload_file のインデックス確認
\di log.*upload_file*
EOF
```

---

## 動作確認（マイグレーション後）

### 確認1: スキーマ変更の確認

```sql
-- raw.receive_raw の変更確認
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'raw' 
  AND table_name = 'receive_raw'
  AND column_name IN ('upload_file_id', 'source_row_no')
ORDER BY ordinal_position;

-- 期待される結果:
--  column_name   | data_type | is_nullable
-- ---------------+-----------+-------------
--  upload_file_id | integer   | NO
--  source_row_no  | integer   | NO

-- stg.receive_shogun_flash の変更確認
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'stg' 
  AND table_name = 'receive_shogun_flash'
  AND column_name IN ('upload_file_id', 'source_row_no')
ORDER BY ordinal_position;

-- 制約確認
SELECT 
    conname AS constraint_name,
    contype AS constraint_type
FROM pg_constraint
JOIN pg_namespace ON pg_namespace.oid = pg_constraint.connamespace
WHERE nspname = 'raw' 
  AND conrelid::regclass::text LIKE 'raw.receive_raw'
  AND conname LIKE '%upload%';

-- 期待される結果:
--  constraint_name              | constraint_type
-- ------------------------------+-----------------
--  fk_receive_raw_upload_file_id | f (foreign key)
--  uq_receive_raw_upload_row     | u (unique)
```

---

## 次のステップ（実装タスク）

1. **Repository層のコード修正**（Phase 1）
   - [ ] `RawDataRepository.check_duplicate_upload()` 実装
   - [ ] `RawDataRepository.save_receive_raw()` 修正（source_row_no 対応）
   - [ ] `ShogunCsvRepository.save_csv_by_type()` 修正（upload_file_id, source_row_no 保持）

2. **UseCase層のコード修正**（Phase 2）
   - [ ] `UploadSyogunCsvUseCase.execute()` に重複チェック追加
   - [ ] `source_row_no` 採番処理追加
   - [ ] `_save_data()` メソッドに `upload_file_ids` 引数追加

3. **単体テスト作成**
   - [ ] `test_raw_data_repository.py` - 重複チェックのテスト
   - [ ] `test_upload_syogun_csv_uc.py` - UseCase の統合テスト

4. **結合テスト**
   - [ ] 初回アップロード（正常系）
   - [ ] 同じCSVの再アップロード（重複エラー）
   - [ ] 一部重複のケース

---

## 参考資料

- **詳細設計ドキュメント**: `docs/SHOGUN_CSV_UPLOAD_FILE_ID_TRACKING_IMPLEMENTATION.md`
- **Makefile**: `makefile` (Alembic関連コマンド: `al-rev`, `al-up`, `al-cur` など)
- **既存マイグレーション**: `migrations/alembic/versions/20251114_120000000_move_upload_file_to_log_and_extend.py`

---

## 注意事項

1. **既存データの扱い**:
   - マイグレーション後、既存データは `upload_file_id = 0`, `source_row_no = 0` となります
   - 本番適用前にデータクリーンアップが必要な場合は別途対応してください

2. **processing_status の拡張**:
   - 'duplicate' ステータスを追加するため、enum定義がある場合は更新が必要

3. **フロントエンド対応**:
   - 409 Conflict レスポンス（重複エラー）を適切に表示する UI 実装が必要

4. **パフォーマンス**:
   - 重複チェックはファイルハッシュ計算を伴うため、大容量ファイルの場合は注意
   - インデックスにより検索は高速化されていますが、負荷テストを推奨

---

## 実装完了チェックリスト

- [x] 詳細設計ドキュメント作成
- [x] Alembicマイグレーションファイル作成（3つ）
- [ ] Repository層のコード修正
- [ ] UseCase層のコード修正
- [ ] 単体テスト作成
- [ ] 結合テスト実施
- [ ] フロントエンド対応（重複エラーUI）
