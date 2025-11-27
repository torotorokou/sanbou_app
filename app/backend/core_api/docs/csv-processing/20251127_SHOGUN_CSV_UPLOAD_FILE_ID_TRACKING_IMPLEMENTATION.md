# 将軍CSVアップロード機能拡張: upload_file_id + source_row_no トラッキング実装案

## 概要

CSVアップロード処理において、以下の機能を追加します：
1. `log.upload_file` テーブルに各CSVアップロードを記録し、その `id` を取得
2. 各CSV行に `source_row_no`（元行番号）を採番
3. raw / stg テーブルに `upload_file_id` と `source_row_no` を保存
4. `log.upload_file` の既存カラム（`file_hash`, `csv_type` など）を使った重複チェック

---

## 1. 現状のコード・スキーマ構成

### 1-1. テーブル構成

#### `log.upload_file`（アップロードログ、全CSV共通）
**場所**: `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`

```python
# 既存カラム（変更なし）
Column('id', Integer, primary_key=True, autoincrement=True)
Column('csv_type', String(32), nullable=False)      # 'receive', 'yard', 'shipment'
Column('file_name', Text, nullable=False)
Column('file_hash', String(64), nullable=False)     # SHA-256
Column('file_type', String(20), nullable=False)     # 'FLASH' / 'FINAL'
Column('file_size_bytes', BigInteger, nullable=True)
Column('row_count', Integer, nullable=True)
Column('uploaded_at', DateTime(timezone=True), nullable=False)
Column('uploaded_by', String(100), nullable=True)
Column('processing_status', String(20), nullable=False)  # 'pending'/'success'/'failed'/'duplicate'
Column('error_message', Text, nullable=True)
Column('env', Text, nullable=False)                 # 'local_dev' など
```

#### raw層テーブル（生データ、全カラムTEXT型）
- `raw.receive_raw` (id, file_id, row_number + TEXT型カラム)
- `raw.yard_raw` (id, file_id, row_number + TEXT型カラム)
- `raw.shipment_raw` (id, file_id, row_number + TEXT型カラム)

**現状の問題点**:
- `file_id` カラム名が分かりにくい（`upload_file_id` の方が明示的）
- `row_number` が何の行番号か不明確（CSV元行か、DB行か）

#### stg層テーブル（型変換済み）
- `stg.receive_shogun_flash` (id + 型付きカラム)
- `stg.yard_shogun_flash` (id + 型付きカラム)
- `stg.shipment_shogun_flash` (id + 型付きカラム)
- `stg.receive_shogun_final` / `stg.yard_shogun_final` / `stg.shipment_shogun_final`

**現状の問題点**:
- アップロード元ファイル・行番号を追跡できない

### 1-2. 処理フロー

```
[フロントエンド]
  ↓ POST /database/upload/syogun_csv_flash (receive.csv, yard.csv, shipment.csv)
  
[router.py] /database/upload/syogun_csv_flash
  ↓ Depends(get_uc_flash) でDI
  
[UploadSyogunCsvUseCase.execute()]
  1. ファイルタイプ検証（MIME, 拡張子）
  2. CSV読込（pandas DataFrame化）
  3. CSVバリデーション（カラム、伝票日付）
  4. log.upload_file にレコード作成 ← ★ここで upload_file_id 取得済み
  5. raw層に保存（RawDataRepository経由）
  6. stg層に保存（ShogunCsvRepository経由）
  7. log.upload_file のステータス更新（success/failed）
  8. レスポンス返却
```

**関連ファイル**:
- **Router**: `app/backend/core_api/app/presentation/routers/database/router.py`
- **UseCase**: `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`
- **Repository (raw層)**: `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`
- **Repository (stg層)**: `app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`

---

## 2. スキーマ変更設計

### 2-1. raw層テーブル変更（`upload_file_id` + `source_row_no`）

#### 変更内容

```sql
-- ■ 変更前（raw.receive_raw の例）
CREATE TABLE raw.receive_raw (
    id BIGINT PRIMARY KEY,
    file_id INT NOT NULL REFERENCES log.upload_file(id),
    row_number INT NOT NULL,
    slip_date_text TEXT,
    -- ... その他TEXT型カラム
);

-- ■ 変更後
CREATE TABLE raw.receive_raw (
    id BIGINT PRIMARY KEY,
    upload_file_id INT NOT NULL REFERENCES log.upload_file(id) ON DELETE CASCADE,
    source_row_no INT NOT NULL,
    slip_date_text TEXT,
    -- ... その他TEXT型カラム
    CONSTRAINT uq_receive_raw_upload_row UNIQUE (upload_file_id, source_row_no)
);
CREATE INDEX idx_receive_raw_upload_file_id ON raw.receive_raw(upload_file_id);
```

**変更点**:
1. `file_id` → `upload_file_id` にリネーム（意味を明確化）
2. `row_number` → `source_row_no` にリネーム（CSV元行番号であることを明示）
3. UNIQUE制約: `(upload_file_id, source_row_no)` を追加
4. INDEX: `upload_file_id` を追加

**同様の変更を以下にも適用**:
- `raw.yard_raw`
- `raw.shipment_raw`

### 2-2. stg層テーブル変更（`upload_file_id` + `source_row_no` 追加）

#### 変更内容

```sql
-- ■ 変更前（stg.receive_shogun_flash の例）
CREATE TABLE stg.receive_shogun_flash (
    id BIGINT PRIMARY KEY,
    slip_date TIMESTAMP,
    vendor_cd INT,
    -- ... 型付きカラム
);

-- ■ 変更後
CREATE TABLE stg.receive_shogun_flash (
    id BIGINT PRIMARY KEY,
    upload_file_id INT NOT NULL,
    source_row_no INT NOT NULL,
    slip_date TIMESTAMP,
    vendor_cd INT,
    -- ... 型付きカラム
);
CREATE INDEX idx_receive_shogun_flash_upload ON stg.receive_shogun_flash(upload_file_id, source_row_no);
```

**変更点**:
1. `upload_file_id INT NOT NULL` を追加
2. `source_row_no INT NOT NULL` を追加
3. INDEX: `(upload_file_id, source_row_no)` を追加
4. **FK制約は不要**（raw層で log.upload_file への FK が設定されているため重複）

**同様の変更を以下すべてに適用**:
- `stg.receive_shogun_flash`
- `stg.yard_shogun_flash`
- `stg.shipment_shogun_flash`
- `stg.receive_shogun_final`
- `stg.yard_shogun_final`
- `stg.shipment_shogun_final`

---

## 3. CSV アップロード処理の修正案

### 3-1. UseCase修正: `upload_file_id` + `source_row_no` の保存

**ファイル**: `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`

#### ■ Before（現状）

```python
async def execute(self, receive, yard, shipment, file_type="FLASH", uploaded_by=None):
    # ... 入力チェック、バリデーション
    
    # log.upload_file にアップロードログを作成
    upload_file_ids: Dict[str, int] = {}
    if self.raw_data_repo:
        for csv_type, uf in uploaded_files.items():
            file_id = self.raw_data_repo.create_upload_file(
                csv_type=csv_type,
                file_name=uf.filename or f"{csv_type}.csv",
                file_hash=file_hash,
                file_type=file_type,
                file_size_bytes=len(content),
                uploaded_by=uploaded_by,
            )
            upload_file_ids[csv_type] = file_id  # ★ここで upload_file_id を取得済み
    
    # CSV読込
    dfs, read_error = await self._read_csv_files(uploaded_files)
    
    # バリデーション
    # ...
    
    # raw層保存（★ upload_file_id を渡していない）
    raw_result = await self._save_data(self.raw_writer, raw_cleaned_dfs, uploaded_files, "raw")
    
    # stg層保存（★ upload_file_id を渡していない）
    stg_result = await self._save_data(self.stg_writer, formatted_dfs, uploaded_files, "stg")
```

#### ■ After（修正後）

```python
async def execute(self, receive, yard, shipment, file_type="FLASH", uploaded_by=None):
    # ... 入力チェック、バリデーション
    
    # log.upload_file にアップロードログを作成
    upload_file_ids: Dict[str, int] = {}
    if self.raw_data_repo:
        for csv_type, uf in uploaded_files.items():
            file_id = self.raw_data_repo.create_upload_file(...)
            upload_file_ids[csv_type] = file_id
    
    # CSV読込（★ source_row_no を採番）
    dfs, read_error = await self._read_csv_files(uploaded_files)
    if read_error:
        return read_error
    
    # ★ source_row_no を各行に追加（1-indexed）
    for csv_type, df in dfs.items():
        df['source_row_no'] = range(1, len(df) + 1)
    
    # バリデーション
    # ...
    
    # raw層保存（★ upload_file_ids を渡す）
    raw_result = await self._save_data(
        self.raw_writer,
        raw_cleaned_dfs,
        uploaded_files,
        "raw",
        upload_file_ids=upload_file_ids  # ★追加
    )
    
    # stg層保存（★ upload_file_ids を渡す）
    stg_result = await self._save_data(
        self.stg_writer,
        formatted_dfs,
        uploaded_files,
        "stg",
        upload_file_ids=upload_file_ids  # ★追加
    )
```

#### ■ _save_data() メソッドの修正

```python
async def _save_data(
    self,
    writer: IShogunCsvWriter,
    formatted_dfs: Dict[str, pd.DataFrame],
    uploaded_files: Dict[str, UploadFile],
    layer_name: str,
    upload_file_ids: Optional[Dict[str, int]] = None,  # ★追加
) -> Dict[str, dict]:
    results = {}
    for csv_type, df in formatted_dfs.items():
        try:
            # ★ upload_file_id を DataFrame に追加
            if upload_file_ids and csv_type in upload_file_ids:
                df['upload_file_id'] = upload_file_ids[csv_type]
            
            # ★ source_row_no は既に追加済み（_read_csv_files 後に追加）
            
            count = await run_in_threadpool(writer.save_csv_by_type, csv_type, df)
            results[csv_type] = {
                "status": "success",
                "filename": uploaded_files[csv_type].filename,
                "rows": count,
            }
        except Exception as e:
            # エラー処理
```

### 3-2. Repository修正: raw層保存時の `upload_file_id` + `source_row_no` 対応

**ファイル**: `app/backend/core_api/app/infra/adapters/upload/raw_data_repository.py`

#### 既存メソッドの確認

```python
def save_receive_raw(self, file_id: int, df: pd.DataFrame) -> int:
    """
    受入CSV の生データを raw.receive_raw に保存
    
    Args:
        file_id: upload_file.id
        df: 日本語カラム名のままの DataFrame（変換前）
        
    Returns:
        int: 保存した行数
    """
    # ... （実装略）
```

#### 修正案

```python
def save_receive_raw(self, file_id: int, df: pd.DataFrame) -> int:
    """
    受入CSV の生データを raw.receive_raw に保存
    
    Args:
        file_id: upload_file.id（= upload_file_id）
        df: 日本語カラム名 + upload_file_id, source_row_no を含む DataFrame
        
    Returns:
        int: 保存した行数
    """
    # ★ upload_file_id, source_row_no が df に含まれていることを前提とする
    # （UseCase側で事前に追加済み）
    
    # カラム名マッピング（日本語→英語_text）
    # ... （既存ロジック）
    
    # upload_file_id, source_row_no はそのまま保持
    # INSERT実行
```

**同様の修正を以下メソッドにも適用**:
- `save_yard_raw()`
- `save_shipment_raw()`

### 3-3. Repository修正: stg層保存時の `upload_file_id` + `source_row_no` 対応

**ファイル**: `app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`

#### 既存メソッドの確認

```python
def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
    """
    CSV種別に応じて stg層に保存
    
    Args:
        csv_type: 'receive', 'yard', 'shipment'
        df: 型変換済みDataFrame
        
    Returns:
        int: 保存行数
    """
    # YAMLから日本語→英語のカラムマッピングを取得
    column_mapping = self.table_gen.get_column_mapping(csv_type)
    df_renamed = df.rename(columns=column_mapping)
    
    # stg層: YAML定義カラムのみフィルタ
    valid_columns = self.table_gen.get_columns(csv_type)
    df_to_save = filter_defined_columns(df_renamed, valid_columns, log_dropped=True)
    
    # INSERT
    model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=schema)
    records = df_to_save.to_dict('records')
    # ... bulk insert
```

#### 修正案

```python
def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
    """
    CSV種別に応じて stg層に保存
    
    Args:
        csv_type: 'receive', 'yard', 'shipment'
        df: 型変換済み + upload_file_id, source_row_no を含む DataFrame
        
    Returns:
        int: 保存行数
    """
    # YAMLから日本語→英語のカラムマッピングを取得
    column_mapping = self.table_gen.get_column_mapping(csv_type)
    df_renamed = df.rename(columns=column_mapping)
    
    # ★ upload_file_id, source_row_no は必須カラムとして保持
    required_columns = ['upload_file_id', 'source_row_no']
    for col in required_columns:
        if col not in df_renamed.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame")
    
    # stg層: YAML定義カラム + upload_file_id + source_row_no
    valid_columns = self.table_gen.get_columns(csv_type) + required_columns
    df_to_save = filter_defined_columns(df_renamed, valid_columns, log_dropped=True)
    
    # INSERT
    # ... （既存ロジック、upload_file_id, source_row_no も含めて保存）
```

---

## 4. 重複チェックロジックの設計と実装

### 4-1. 「同じファイル」の定義

**第一候補: (csv_type, file_hash) の組み合わせ**

```sql
SELECT id, processing_status, uploaded_at
FROM log.upload_file
WHERE csv_type = :csv_type
  AND file_hash = :file_hash
  AND processing_status = 'success'
ORDER BY uploaded_at DESC
LIMIT 1;
```

**理由**:
- `file_hash` (SHA-256) は内容が1バイトでも異なれば変わる
- 最も信頼性の高い同一判定
- `processing_status = 'success'` で、過去に成功したアップロードのみを対象

**フォールバック案: file_hash が NULL の場合**

```sql
SELECT id, processing_status, uploaded_at
FROM log.upload_file
WHERE csv_type = :csv_type
  AND file_name = :file_name
  AND file_size_bytes = :file_size_bytes
  AND row_count = :row_count
  AND processing_status = 'success'
ORDER BY uploaded_at DESC
LIMIT 1;
```

### 4-2. 重複チェックの実装ポイント

#### Repository層に重複チェックメソッドを追加

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
    
    Args:
        csv_type: CSV種別
        file_hash: SHA-256ハッシュ
        file_name: ファイル名（フォールバック用）
        file_size_bytes: ファイルサイズ（フォールバック用）
        row_count: 行数（フォールバック用）
        
    Returns:
        Optional[Dict]: 重複あり → {'id': ..., 'uploaded_at': ..., 'file_name': ...}
                        重複なし → None
    """
    try:
        # 第一候補: (csv_type, file_hash) で検索
        if file_hash:
            result = self.db.execute(
                self.upload_file_table.select()
                .where(
                    self.upload_file_table.c.csv_type == csv_type,
                    self.upload_file_table.c.file_hash == file_hash,
                    self.upload_file_table.c.processing_status == 'success',
                )
                .order_by(self.upload_file_table.c.uploaded_at.desc())
                .limit(1)
            ).fetchone()
            
            if result:
                return {
                    'id': result.id,
                    'uploaded_at': result.uploaded_at,
                    'file_name': result.file_name,
                }
        
        # フォールバック: (csv_type, file_name, file_size, row_count) で検索
        if file_name and file_size_bytes is not None:
            result = self.db.execute(
                self.upload_file_table.select()
                .where(
                    self.upload_file_table.c.csv_type == csv_type,
                    self.upload_file_table.c.file_name == file_name,
                    self.upload_file_table.c.file_size_bytes == file_size_bytes,
                    self.upload_file_table.c.row_count == row_count,
                    self.upload_file_table.c.processing_status == 'success',
                )
                .order_by(self.upload_file_table.c.uploaded_at.desc())
                .limit(1)
            ).fetchone()
            
            if result:
                return {
                    'id': result.id,
                    'uploaded_at': result.uploaded_at,
                    'file_name': result.file_name,
                }
        
        return None
    except Exception as e:
        logger.error(f"Failed to check duplicate upload: {e}")
        return None
```

#### UseCase層で重複チェックを呼び出し

**ファイル**: `app/backend/core_api/app/application/usecases/upload/upload_syogun_csv_uc.py`

```python
async def execute(self, receive, yard, shipment, file_type="FLASH", uploaded_by=None):
    # ... 入力チェック、ファイルタイプ検証
    
    # ★ 重複チェック（log.upload_file 作成前）
    if self.raw_data_repo:
        duplicates: Dict[str, Dict[str, Any]] = {}
        for csv_type, uf in uploaded_files.items():
            content = await uf.read()
            file_hash = self.raw_data_repo.calculate_file_hash(content)
            uf.file.seek(0)
            
            # 重複チェック
            duplicate = self.raw_data_repo.check_duplicate_upload(
                csv_type=csv_type,
                file_hash=file_hash,
                file_name=uf.filename,
                file_size_bytes=len(content),
            )
            
            if duplicate:
                duplicates[csv_type] = duplicate
        
        # 全ファイルが重複の場合はエラー
        if len(duplicates) == len(uploaded_files):
            return ErrorApiResponse(
                code="DUPLICATE_UPLOAD",
                detail="アップロードされたすべてのCSVファイルは既に取り込み済みです",
                metadata={
                    "duplicates": {
                        csv_type: {
                            "uploaded_at": str(info['uploaded_at']),
                            "file_name": info['file_name'],
                        }
                        for csv_type, info in duplicates.items()
                    }
                },
                status_code=409,  # Conflict
            )
        
        # 一部重複の場合は警告（処理は継続）
        if duplicates:
            logger.warning(
                f"Partial duplicates detected: {list(duplicates.keys())}. "
                f"Non-duplicate files will be processed."
            )
    
    # log.upload_file にアップロードログを作成（重複していないファイルのみ）
    upload_file_ids: Dict[str, int] = {}
    if self.raw_data_repo:
        for csv_type, uf in uploaded_files.items():
            if csv_type in duplicates:
                # 重複している場合は 'duplicate' ステータスでログ作成
                content = await uf.read()
                file_hash = self.raw_data_repo.calculate_file_hash(content)
                uf.file.seek(0)
                
                file_id = self.raw_data_repo.create_upload_file(
                    csv_type=csv_type,
                    file_name=uf.filename or f"{csv_type}.csv",
                    file_hash=file_hash,
                    file_type=file_type,
                    file_size_bytes=len(content),
                    uploaded_by=uploaded_by,
                )
                self.raw_data_repo.update_upload_status(
                    file_id=file_id,
                    status='duplicate',
                    error_message=f"Duplicate of upload_file.id={duplicates[csv_type]['id']}",
                )
                continue
            
            # 重複していない場合は通常処理
            content = await uf.read()
            file_hash = self.raw_data_repo.calculate_file_hash(content)
            uf.file.seek(0)
            
            file_id = self.raw_data_repo.create_upload_file(...)
            upload_file_ids[csv_type] = file_id
    
    # 重複していないファイルのみ処理（CSV読込、バリデーション、保存）
    non_duplicate_files = {k: v for k, v in uploaded_files.items() if k not in duplicates}
    if not non_duplicate_files:
        # すべて重複（上記で既にエラーレスポンス返却済み）
        pass
    
    # CSV読込（重複していないファイルのみ）
    dfs, read_error = await self._read_csv_files(non_duplicate_files)
    # ... 以降の処理
```

### 4-3. 重複時の挙動（設計方針）

**採用案: 案A（新規レコードを `duplicate` ステータスで保存）**

```python
# log.upload_file に 'duplicate' レコードを作成
file_id = self.raw_data_repo.create_upload_file(...)
self.raw_data_repo.update_upload_status(
    file_id=file_id,
    status='duplicate',
    error_message=f"Duplicate of upload_file.id={original_file_id}",
)
```

**理由**:
- アップロード試行の完全な履歴が残る
- 「いつ、誰が、何度同じファイルをアップロードしようとしたか」が分かる
- 監査ログとして有用

**レスポンス**:
```json
{
  "status": "error",
  "code": "DUPLICATE_UPLOAD",
  "detail": "アップロードされたすべてのCSVファイルは既に取り込み済みです",
  "metadata": {
    "duplicates": {
      "receive": {
        "uploaded_at": "2025-11-14T10:00:00+09:00",
        "file_name": "受入一覧_20251112_150252.csv"
      },
      "yard": {
        "uploaded_at": "2025-11-14T10:00:00+09:00",
        "file_name": "ヤード一覧_202404_202510.csv"
      }
    }
  },
  "status_code": 409
}
```

---

## 5. 制約・インデックスの追加

### 5-1. raw層テーブル

```sql
-- raw.receive_raw
ALTER TABLE raw.receive_raw RENAME COLUMN file_id TO upload_file_id;
ALTER TABLE raw.receive_raw RENAME COLUMN row_number TO source_row_no;
ALTER TABLE raw.receive_raw 
  ADD CONSTRAINT uq_receive_raw_upload_row UNIQUE (upload_file_id, source_row_no);
CREATE INDEX idx_receive_raw_upload_file_id ON raw.receive_raw(upload_file_id);

-- raw.yard_raw
ALTER TABLE raw.yard_raw RENAME COLUMN file_id TO upload_file_id;
ALTER TABLE raw.yard_raw RENAME COLUMN row_number TO source_row_no;
ALTER TABLE raw.yard_raw 
  ADD CONSTRAINT uq_yard_raw_upload_row UNIQUE (upload_file_id, source_row_no);
CREATE INDEX idx_yard_raw_upload_file_id ON raw.yard_raw(upload_file_id);

-- raw.shipment_raw
ALTER TABLE raw.shipment_raw RENAME COLUMN file_id TO upload_file_id;
ALTER TABLE raw.shipment_raw RENAME COLUMN row_number TO source_row_no;
ALTER TABLE raw.shipment_raw 
  ADD CONSTRAINT uq_shipment_raw_upload_row UNIQUE (upload_file_id, source_row_no);
CREATE INDEX idx_shipment_raw_upload_file_id ON raw.shipment_raw(upload_file_id);
```

### 5-2. stg層テーブル

```sql
-- stg.receive_shogun_flash
ALTER TABLE stg.receive_shogun_flash 
  ADD COLUMN upload_file_id INT NOT NULL;
ALTER TABLE stg.receive_shogun_flash 
  ADD COLUMN source_row_no INT NOT NULL;
CREATE INDEX idx_receive_shogun_flash_upload 
  ON stg.receive_shogun_flash(upload_file_id, source_row_no);

-- stg.yard_shogun_flash
ALTER TABLE stg.yard_shogun_flash 
  ADD COLUMN upload_file_id INT NOT NULL;
ALTER TABLE stg.yard_shogun_flash 
  ADD COLUMN source_row_no INT NOT NULL;
CREATE INDEX idx_yard_shogun_flash_upload 
  ON stg.yard_shogun_flash(upload_file_id, source_row_no);

-- stg.shipment_shogun_flash
ALTER TABLE stg.shipment_shogun_flash 
  ADD COLUMN upload_file_id INT NOT NULL;
ALTER TABLE stg.shipment_shogun_flash 
  ADD COLUMN source_row_no INT NOT NULL;
CREATE INDEX idx_shipment_shogun_flash_upload 
  ON stg.shipment_shogun_flash(upload_file_id, source_row_no);

-- 同様に *_final テーブルにも適用
-- （stg.receive_shogun_final, stg.yard_shogun_final, stg.shipment_shogun_final）
```

### 5-3. log.upload_file（重複チェック用インデックス）

```sql
-- 既存: uq_upload_file_hash_type_csv UNIQUE (file_hash, file_type, csv_type)
-- これで (csv_type, file_hash) のクエリは高速

-- フォールバック用の複合インデックス
CREATE INDEX idx_upload_file_duplicate_fallback 
  ON log.upload_file(csv_type, file_name, file_size_bytes, row_count, processing_status);
```

---

## 6. Alembicマイグレーション

### 6-1. マイグレーションファイル構成

```
app/backend/core_api/migrations/alembic/versions/
  20251114_130000000_add_upload_tracking_to_raw_tables.py
  20251114_130100000_add_upload_tracking_to_stg_tables.py
  20251114_130200000_add_duplicate_check_indexes.py
```

### 6-2. マイグレーションファイル1: raw層テーブル変更

**ファイル**: `20251114_130000000_add_upload_tracking_to_raw_tables.py`

```python
"""add upload_file_id and source_row_no to raw tables

1. raw.*_raw テーブルの file_id → upload_file_id にリネーム
2. raw.*_raw テーブルの row_number → source_row_no にリネーム
3. UNIQUE制約 (upload_file_id, source_row_no) を追加
4. INDEX (upload_file_id) を追加

Revision ID: 20251114_130000000
Revises: 20251114_120000000
Create Date: 2025-11-14 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20251114_130000000"
down_revision = "20251114_120000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ===== raw.receive_raw =====
    # FK削除 → カラムリネーム → FK再作成
    op.drop_constraint("fk_receive_raw_file_id", "receive_raw", schema="raw", type_="foreignkey")
    op.alter_column("receive_raw", "file_id", new_column_name="upload_file_id", schema="raw")
    op.alter_column("receive_raw", "row_number", new_column_name="source_row_no", schema="raw")
    op.create_foreign_key(
        "fk_receive_raw_upload_file_id",
        "receive_raw", "upload_file",
        ["upload_file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
    
    # UNIQUE制約とINDEX
    op.create_unique_constraint(
        "uq_receive_raw_upload_row",
        "receive_raw",
        ["upload_file_id", "source_row_no"],
        schema="raw"
    )
    op.create_index(
        "idx_receive_raw_upload_file_id",
        "receive_raw",
        ["upload_file_id"],
        schema="raw"
    )
    
    # ===== raw.yard_raw =====
    op.drop_constraint("fk_yard_raw_file_id", "yard_raw", schema="raw", type_="foreignkey")
    op.alter_column("yard_raw", "file_id", new_column_name="upload_file_id", schema="raw")
    op.alter_column("yard_raw", "row_number", new_column_name="source_row_no", schema="raw")
    op.create_foreign_key(
        "fk_yard_raw_upload_file_id",
        "yard_raw", "upload_file",
        ["upload_file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
    op.create_unique_constraint(
        "uq_yard_raw_upload_row",
        "yard_raw",
        ["upload_file_id", "source_row_no"],
        schema="raw"
    )
    op.create_index(
        "idx_yard_raw_upload_file_id",
        "yard_raw",
        ["upload_file_id"],
        schema="raw"
    )
    
    # ===== raw.shipment_raw =====
    op.drop_constraint("fk_shipment_raw_file_id", "shipment_raw", schema="raw", type_="foreignkey")
    op.alter_column("shipment_raw", "file_id", new_column_name="upload_file_id", schema="raw")
    op.alter_column("shipment_raw", "row_number", new_column_name="source_row_no", schema="raw")
    op.create_foreign_key(
        "fk_shipment_raw_upload_file_id",
        "shipment_raw", "upload_file",
        ["upload_file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
    op.create_unique_constraint(
        "uq_shipment_raw_upload_row",
        "shipment_raw",
        ["upload_file_id", "source_row_no"],
        schema="raw"
    )
    op.create_index(
        "idx_shipment_raw_upload_file_id",
        "shipment_raw",
        ["upload_file_id"],
        schema="raw"
    )


def downgrade() -> None:
    # receive_raw
    op.drop_index("idx_receive_raw_upload_file_id", "receive_raw", schema="raw")
    op.drop_constraint("uq_receive_raw_upload_row", "receive_raw", schema="raw", type_="unique")
    op.drop_constraint("fk_receive_raw_upload_file_id", "receive_raw", schema="raw", type_="foreignkey")
    op.alter_column("receive_raw", "source_row_no", new_column_name="row_number", schema="raw")
    op.alter_column("receive_raw", "upload_file_id", new_column_name="file_id", schema="raw")
    op.create_foreign_key(
        "fk_receive_raw_file_id",
        "receive_raw", "upload_file",
        ["file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
    
    # yard_raw
    op.drop_index("idx_yard_raw_upload_file_id", "yard_raw", schema="raw")
    op.drop_constraint("uq_yard_raw_upload_row", "yard_raw", schema="raw", type_="unique")
    op.drop_constraint("fk_yard_raw_upload_file_id", "yard_raw", schema="raw", type_="foreignkey")
    op.alter_column("yard_raw", "source_row_no", new_column_name="row_number", schema="raw")
    op.alter_column("yard_raw", "upload_file_id", new_column_name="file_id", schema="raw")
    op.create_foreign_key(
        "fk_yard_raw_file_id",
        "yard_raw", "upload_file",
        ["file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
    
    # shipment_raw
    op.drop_index("idx_shipment_raw_upload_file_id", "shipment_raw", schema="raw")
    op.drop_constraint("uq_shipment_raw_upload_row", "shipment_raw", schema="raw", type_="unique")
    op.drop_constraint("fk_shipment_raw_upload_file_id", "shipment_raw", schema="raw", type_="foreignkey")
    op.alter_column("shipment_raw", "source_row_no", new_column_name="row_number", schema="raw")
    op.alter_column("shipment_raw", "upload_file_id", new_column_name="file_id", schema="raw")
    op.create_foreign_key(
        "fk_shipment_raw_file_id",
        "shipment_raw", "upload_file",
        ["file_id"], ["id"],
        source_schema="raw", referent_schema="log",
        ondelete="CASCADE"
    )
```

### 6-3. マイグレーションファイル2: stg層テーブル変更

**ファイル**: `20251114_130100000_add_upload_tracking_to_stg_tables.py`

```python
"""add upload_file_id and source_row_no to stg tables

1. stg.*_shogun_* テーブルに upload_file_id, source_row_no カラムを追加
2. INDEX (upload_file_id, source_row_no) を追加

対象テーブル:
- stg.receive_shogun_flash / yard_shogun_flash / shipment_shogun_flash
- stg.receive_shogun_final / yard_shogun_final / shipment_shogun_final

Revision ID: 20251114_130100000
Revises: 20251114_130000000
Create Date: 2025-11-14 13:01:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20251114_130100000"
down_revision = "20251114_130000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = [
        "receive_shogun_flash",
        "yard_shogun_flash",
        "shipment_shogun_flash",
        "receive_shogun_final",
        "yard_shogun_final",
        "shipment_shogun_final",
    ]
    
    for table in tables:
        # カラム追加
        op.add_column(
            table,
            sa.Column("upload_file_id", sa.Integer(), nullable=False, server_default="0"),
            schema="stg"
        )
        op.add_column(
            table,
            sa.Column("source_row_no", sa.Integer(), nullable=False, server_default="0"),
            schema="stg"
        )
        
        # server_default削除（既存データは0、新規データは正しい値が入る）
        op.alter_column(table, "upload_file_id", server_default=None, schema="stg")
        op.alter_column(table, "source_row_no", server_default=None, schema="stg")
        
        # INDEX作成
        op.create_index(
            f"idx_{table}_upload",
            table,
            ["upload_file_id", "source_row_no"],
            schema="stg"
        )


def downgrade() -> None:
    tables = [
        "receive_shogun_flash",
        "yard_shogun_flash",
        "shipment_shogun_flash",
        "receive_shogun_final",
        "yard_shogun_final",
        "shipment_shogun_final",
    ]
    
    for table in tables:
        op.drop_index(f"idx_{table}_upload", table, schema="stg")
        op.drop_column(table, "source_row_no", schema="stg")
        op.drop_column(table, "upload_file_id", schema="stg")
```

### 6-4. マイグレーションファイル3: 重複チェック用インデックス

**ファイル**: `20251114_130200000_add_duplicate_check_indexes.py`

```python
"""add indexes for duplicate upload check

log.upload_file にフォールバック用の複合インデックスを追加

Revision ID: 20251114_130200000
Revises: 20251114_130100000
Create Date: 2025-11-14 13:02:00.000000
"""
from alembic import op

revision = "20251114_130200000"
down_revision = "20251114_130100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # フォールバック用: (csv_type, file_name, file_size_bytes, row_count, processing_status)
    op.create_index(
        "idx_upload_file_duplicate_fallback",
        "upload_file",
        ["csv_type", "file_name", "file_size_bytes", "row_count", "processing_status"],
        schema="log"
    )


def downgrade() -> None:
    op.drop_index("idx_upload_file_duplicate_fallback", "upload_file", schema="log")
```

### 6-5. マイグレーション実行コマンド

```bash
# Alembicマイグレーション作成（makefileを使用）
make al-rev MSG="add upload_file_id and source_row_no to raw tables" REV_ID=20251114_130000000
make al-rev MSG="add upload_file_id and source_row_no to stg tables" REV_ID=20251114_130100000
make al-rev MSG="add indexes for duplicate upload check" REV_ID=20251114_130200000

# マイグレーション適用
make al-up

# 確認
make al-cur
```

---

## 7. 動作確認手順

### 7-1. 初回アップロード（正常系）

```bash
# 1. テスト用CSVを準備
# - test_receive_mini.csv
# - test_yard_mini.csv
# - test_shipment_mini.csv

# 2. アップロード実行（フロントエンドまたはcurlで）
curl -X POST http://localhost:8001/database/upload/syogun_csv_flash \
  -F "receive=@test_receive_mini.csv" \
  -F "yard=@test_yard_mini.csv" \
  -F "shipment=@test_shipment_mini.csv"

# 3. レスポンス確認
# {
#   "status": "success",
#   "code": "UPLOAD_SUCCESS",
#   "detail": "CSVアップロードが完了しました",
#   ...
# }

# 4. DBでデータ確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev << EOF
-- log.upload_file にレコードが作成されている
SELECT id, csv_type, file_name, file_hash, processing_status, uploaded_at
FROM log.upload_file
ORDER BY uploaded_at DESC
LIMIT 10;

-- raw.receive_raw に upload_file_id, source_row_no が保存されている
SELECT id, upload_file_id, source_row_no, slip_date_text, vendor_name_text
FROM raw.receive_raw
ORDER BY upload_file_id DESC, source_row_no
LIMIT 10;

-- stg.receive_shogun_flash に upload_file_id, source_row_no が保存されている
SELECT id, upload_file_id, source_row_no, slip_date, vendor_cd, vendor_en_name
FROM stg.receive_shogun_flash
ORDER BY upload_file_id DESC, source_row_no
LIMIT 10;
EOF
```

### 7-2. 同じCSVを再度アップロード（重複チェック）

```bash
# 同じファイルを再度アップロード
curl -X POST http://localhost:8001/database/upload/syogun_csv_flash \
  -F "receive=@test_receive_mini.csv" \
  -F "yard=@test_yard_mini.csv" \
  -F "shipment=@test_shipment_mini.csv"

# レスポンス確認
# {
#   "status": "error",
#   "code": "DUPLICATE_UPLOAD",
#   "detail": "アップロードされたすべてのCSVファイルは既に取り込み済みです",
#   "metadata": {
#     "duplicates": {
#       "receive": {
#         "uploaded_at": "2025-11-14T13:00:00+09:00",
#         "file_name": "test_receive_mini.csv"
#       },
#       "yard": {...},
#       "shipment": {...}
#     }
#   },
#   "status_code": 409
# }

# log.upload_file で processing_status = 'duplicate' のレコードが作成されている
SELECT id, csv_type, file_name, processing_status, error_message, uploaded_at
FROM log.upload_file
WHERE processing_status = 'duplicate'
ORDER BY uploaded_at DESC;

# raw / stg には新規行が追加されていない（行数が増えていないことを確認）
SELECT COUNT(*) FROM raw.receive_raw;
SELECT COUNT(*) FROM stg.receive_shogun_flash;
```

### 7-3. 一部重複のケース

```bash
# receive と yard は既存、shipment は新規
curl -X POST http://localhost:8001/database/upload/syogun_csv_flash \
  -F "receive=@test_receive_mini.csv" \
  -F "yard=@test_yard_mini.csv" \
  -F "shipment=@test_shipment_NEW.csv"

# レスポンス確認
# - receive, yard は 'duplicate' として記録
# - shipment のみ処理され、成功レスポンス
# {
#   "status": "success",
#   "code": "PARTIAL_SUCCESS",
#   "detail": "一部のCSVファイルは重複のためスキップされました",
#   "metadata": {
#     "processed": ["shipment"],
#     "duplicates": ["receive", "yard"]
#   }
# }
```

---

## 8. まとめ

### 8-1. 変更箇所一覧

| カテゴリ | ファイル/テーブル | 変更内容 |
|---------|-----------------|---------|
| **スキーマ** | `raw.receive_raw` / `raw.yard_raw` / `raw.shipment_raw` | `file_id` → `upload_file_id`, `row_number` → `source_row_no`, UNIQUE制約、INDEX追加 |
| **スキーマ** | `stg.*_shogun_flash` / `stg.*_shogun_final` (6テーブル) | `upload_file_id`, `source_row_no` カラム追加、INDEX追加 |
| **スキーマ** | `log.upload_file` | フォールバック用INDEX追加 |
| **UseCase** | `upload_syogun_csv_uc.py` | 重複チェック、`source_row_no` 採番、`upload_file_id` 追加 |
| **Repository** | `raw_data_repository.py` | `check_duplicate_upload()` メソッド追加 |
| **Repository** | `shogun_csv_repository.py` | `upload_file_id`, `source_row_no` 保存対応 |
| **Alembic** | 3つのマイグレーションファイル | raw層変更、stg層変更、INDEX追加 |

### 8-2. 実装の優先順位

1. **Phase 1: スキーマ変更** (Alembicマイグレーション実行)
2. **Phase 2: Repository層の修正** (`check_duplicate_upload()` 追加)
3. **Phase 3: UseCase層の修正** (重複チェック、`source_row_no` 採番)
4. **Phase 4: テスト** (初回アップロード、重複アップロード、一部重複)

### 8-3. 注意事項

- 既存データは `upload_file_id = 0`, `source_row_no = 0` となるため、データクリーンアップが必要な場合は別途対応
- `processing_status` に 'duplicate' を追加したため、既存の enum 定義がある場合は更新が必要
- フロントエンド側でも 409 Conflict レスポンスを適切に処理する必要がある

---

以上、実装案でした。
