# 将軍CSV アップロード機能実装ガイド

## 概要

sql_apiを廃止し、core_apiに統合した将軍CSVアップロード機能の実装です。
フロントエンドからアップロードされたCSV（受入一覧・ヤード一覧・出荷一覧）を、
backend_sharedのバリデーター・フォーマッターを使って検証・整形し、
PostgreSQLの`raw`スキーマ配下のテーブルに保存します。

## アーキテクチャ

```
Frontend (React)
    ↓ multipart/form-data
core_api (FastAPI)
    ├─ /database/upload/syogun_csv エンドポイント
    ├─ backend_shared (バリデーター・フォーマッター)
    ├─ ShogunCsvRepository (リポジトリ)
    └─ PostgreSQL (raw スキーマ)
        ├─ raw.receive_shogun_flash   (受入一覧)
        ├─ raw.yard_shogun_flash      (ヤード一覧)
        └─ raw.shipment_shogun_flash  (出荷一覧)
```

## DB構造

### スキーマ: `raw`

将軍CSVの生データを保存する専用スキーマ

### テーブル

#### 1. `raw.receive_shogun_flash` (受入一覧)

```sql
CREATE TABLE raw.receive_shogun_flash (
    id SERIAL PRIMARY KEY,
    slip_date DATE,              -- 伝票日付
    sales_date DATE,             -- 売上日付
    payment_date DATE,           -- 支払日付
    vendor_cd VARCHAR,           -- 業者CD
    vendor_name VARCHAR,         -- 業者名
    product_name VARCHAR,        -- 品名
    net_weight NUMERIC,          -- 正味重量
    quantity NUMERIC,            -- 数量
    unit_price NUMERIC,          -- 単価
    amount NUMERIC,              -- 金額
    raw_data_json JSONB,         -- 元データJSON
    uploaded_at TIMESTAMP,       -- アップロード日時
    created_at TIMESTAMP         -- 作成日時
);
```

#### 2. `raw.yard_shogun_flash` (ヤード一覧)

```sql
CREATE TABLE raw.yard_shogun_flash (
    id SERIAL PRIMARY KEY,
    slip_date DATE,              -- 伝票日付
    customer_name VARCHAR,       -- 取引先名
    product_name VARCHAR,        -- 品名
    net_weight NUMERIC,          -- 正味重量
    quantity NUMERIC,            -- 数量
    raw_data_json JSONB,         -- 元データJSON
    uploaded_at TIMESTAMP,       -- アップロード日時
    created_at TIMESTAMP         -- 作成日時
);
```

#### 3. `raw.shipment_shogun_flash` (出荷一覧)

```sql
CREATE TABLE raw.shipment_shogun_flash (
    id SERIAL PRIMARY KEY,
    slip_date DATE,              -- 伝票日付
    shipment_no VARCHAR,         -- 出荷番号
    customer_name VARCHAR,       -- 取引先名
    vendor_cd VARCHAR,           -- 業者CD
    vendor_name VARCHAR,         -- 業者名
    product_name VARCHAR,        -- 品名
    net_weight NUMERIC,          -- 正味重量
    quantity NUMERIC,            -- 数量
    raw_data_json JSONB,         -- 元データJSON
    uploaded_at TIMESTAMP,       -- アップロード日時
    created_at TIMESTAMP         -- 作成日時
);
```

## 設定のカスタマイズ

### 環境変数での設定

`.env`ファイルまたは環境変数で以下を設定できます：

```bash
# データベース接続
DATABASE_URL=postgresql://user:pass@host:port/dbname

# CSVアップロード設定
CSV_UPLOAD_MAX_SIZE=10485760  # 最大ファイルサイズ (bytes)
CSV_TEMP_DIR=/tmp/csv_uploads  # 一時保存ディレクトリ

# テーブル名のカスタマイズ
SHOGUN_CSV_SCHEMA=raw                    # スキーマ名
RECEIVE_TABLE_NAME=receive_shogun_flash  # 受入テーブル名
YARD_TABLE_NAME=yard_shogun_flash        # ヤードテーブル名
SHIPMENT_TABLE_NAME=shipment_shogun_flash # 出荷テーブル名
```

### コードでの設定

`app/config/settings.py` で直接編集も可能：

```python
class Settings(BaseSettings):
    # テーブル名マッピング
    CSV_TABLE_MAPPING: dict[str, str] = {
        "receive": "raw.receive_shogun_flash",
        "yard": "raw.yard_shogun_flash",
        "shipment": "raw.shipment_shogun_flash",
    }
```

## セットアップ手順

### 1. マイグレーション実行

```bash
# core_apiコンテナ内で実行
cd /backend
alembic upgrade head
```

これにより以下が作成されます：

- `raw` スキーマ
- 3つのテーブル（receive_shogun_flash, yard_shogun_flash, shipment_shogun_flash）
- インデックス

### 2. 依存関係インストール

```bash
# backend_sharedを含む依存関係をインストール
pip install -r requirements.txt
```

### 3. 設定確認

```bash
# 環境変数を確認
echo $DATABASE_URL
echo $SHOGUN_CSV_SCHEMA
```

## API仕様

### エンドポイント

```
POST /core_api/database/upload/syogun_csv
```

### リクエスト

- Content-Type: `multipart/form-data`
- フィールド（すべてオプション、最低1つ必要）:
  - `receive`: 受入一覧CSV
  - `yard`: ヤード一覧CSV
  - `shipment`: 出荷一覧CSV

### レスポンス例

#### 成功時

```json
{
  "status": "success",
  "detail": "アップロード成功: 合計 150 行を保存しました",
  "hint": "データベースに保存されました",
  "result": {
    "receive": {
      "filename": "receive.csv",
      "status": "success",
      "rows_saved": 50
    },
    "yard": {
      "filename": "yard.csv",
      "status": "success",
      "rows_saved": 50
    },
    "shipment": {
      "filename": "shipment.csv",
      "status": "success",
      "rows_saved": 50
    }
  }
}
```

#### エラー時

```json
{
  "code": "MISSING_COLUMNS",
  "status": 400,
  "user_message": "必須カラムが不足しています",
  "detail": "receive.csv: ['伝票日付', '業者CD'] が見つかりません"
}
```

## 処理フロー

1. **ファイル受信**: multipart/form-dataで3種類のCSVを受け取る
2. **CSVパース**: pandasでDataFrameに変換
3. **バリデーション**:
   - 必須カラムチェック (backend_shared)
   - 伝票日付の存在チェック
   - 伝票日付の整合性チェック（複数ファイル時）
4. **フォーマット**: 日本語カラム名→英語名、型変換 (backend_shared)
5. **DB保存**: ShogunCsvRepositoryでバルクインサート
6. **レスポンス**: 成功/エラー情報を返却

## バリデーションルール

### 必須カラム（CSVヘッダー）

**受入一覧 (receive)**

- 伝票日付
- 売上日付
- 支払日付
- 業者CD
- 業者名

**ヤード一覧 (yard)**

- 伝票日付
- 取引先名
- 品名
- 正味重量
- 数量

**出荷一覧 (shipment)**

- 伝票日付
- 出荷番号
- 取引先名
- 業者CD
- 業者名

### その他のバリデーション

- 伝票日付が全ファイルで一致すること
- CSVエンコーディング: UTF-8
- ファイルサイズ: デフォルト10MB以内

## 使用している backend_shared モジュール

- `SyogunCsvConfigLoader`: CSV定義ファイル読み込み
- `CSVValidationResponder`: CSVバリデーション
- `create_formatter`: CSVフォーマッター生成
- `SuccessApiResponse` / `ErrorApiResponse`: 統一レスポンス

## トラブルシューティング

### 1. マイグレーションエラー

```bash
# マイグレーション状態確認
alembic current

# 最新に更新
alembic upgrade head

# ロールバック（必要な場合）
alembic downgrade -1
```

### 2. テーブル名変更

環境変数で変更後、アプリケーション再起動：

```bash
export RECEIVE_TABLE_NAME=my_receive_table
# コンテナ再起動
docker-compose restart core_api
```

### 3. CSVフォーマットエラー

- CSVがUTF-8であることを確認
- ヘッダー行が日本語で正確に記載されているか確認
- `/backend/config/csv_config/syogun_csv_masters.yaml` の定義と一致しているか確認

### 4. backend_sharedインポートエラー

```bash
# backend_sharedが正しくインストールされているか確認
pip show backend-shared

# 再インストール
pip install -e /backend/backend_shared
```

## テスト

### 手動テスト（curl）

```bash
curl -X POST http://localhost:8000/core_api/database/upload/syogun_csv \
  -F "receive=@receive.csv" \
  -F "yard=@yard.csv" \
  -F "shipment=@shipment.csv"
```

### データ確認

```sql
-- レコード数確認
SELECT 'receive' as type, COUNT(*) FROM raw.receive_shogun_flash
UNION ALL
SELECT 'yard', COUNT(*) FROM raw.yard_shogun_flash
UNION ALL
SELECT 'shipment', COUNT(*) FROM raw.shipment_shogun_flash;

-- 最新データ確認
SELECT * FROM raw.receive_shogun_flash
ORDER BY uploaded_at DESC LIMIT 10;
```

## 次のステップ

1. フロントエンドの動作確認
2. エラーハンドリングの強化
3. ログ出力の充実
4. パフォーマンステスト（大量データ）
5. 自動テストの追加

## 参考ファイル

- マイグレーション: `migrations/versions/002_add_raw_shogun_tables.py`
- ORMモデル: `app/repositories/orm_models.py`
- 設定: `app/config/settings.py`
- リポジトリ: `app/repositories/shogun_csv_repo.py`
- エンドポイント: `app/routers/database.py`
