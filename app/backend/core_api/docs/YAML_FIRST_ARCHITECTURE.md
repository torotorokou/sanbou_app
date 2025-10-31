# YAMLファーストアーキテクチャ実装完了レポート

## 概要

`syogun_csv_masters.yaml` を唯一の真（Single Source of Truth）とするアーキテクチャに完全移行しました。
テーブル定義、ORM モデル、カラムマッピングはすべて YAML から動的に生成されます。

## 実装日時

2024年（実装完了）

## 実装内容

### 1. YAML設定ファイル

**パス**: `/backend/config/csv_config/syogun_csv_masters.yaml`

- コンテナ内パス: docker-compose.dev.yml で `../app/config:/backend/config` としてマウント
- 環境変数で変更可能: `CSV_MASTERS_YAML_PATH`
- 3種類のCSV定義（shipment, receive, yard）+ レポート用（payable, sales_summary）

**YAMLの構造**:
```yaml
shipment:
  label: "出荷一覧"
  expected_headers:
    - "伝票日付"
    - "仕入先コード"
    # ...
  unique_keys:
    - slip_date
    - vendor_cd
    # ...
  columns:
    伝票日付:
      en_name: slip_date
      type: datetime
      agg: false
      nullable: true
    # ...
```

### 2. テーブル定義ジェネレーター

**ファイル**: `app/config/table_definition.py`

**クラス**: `TableDefinitionGenerator`

**主要メソッド**:
- `get_csv_types()` - アップロード対象のCSV種別リストを取得
- `get_columns_definition(csv_type)` - SQLAlchemyカラム定義を生成
- `get_column_mapping(csv_type)` - 日本語→英語カラムマッピングを取得
- `get_type_mapping()` - YAML type → SQLAlchemy type マッピング
- `generate_index_columns(csv_type)` - インデックスカラムリストを生成

**型マッピング**:
| YAML type | SQLAlchemy type |
|-----------|-----------------|
| datetime  | Date            |
| date      | Date            |
| str       | String          |
| int       | Integer         |
| Int64     | Integer         |
| float     | Numeric         |
| bool      | Boolean         |

**パス設定**:
- 環境変数 `CSV_MASTERS_YAML_PATH` から読み込み
- デフォルト: `/backend/config/csv_config/syogun_csv_masters.yaml`
- コンストラクタで明示的に指定も可能

### 3. マイグレーション（動的生成）

**ファイル**: `migrations/versions/002_add_raw_shogun_tables.py`

**変更内容**:
- 静的なテーブル定義を削除
- `TableDefinitionGenerator` を使用して動的に生成
- CSV種別ごとにループ処理でテーブル作成
- インデックスも YAML から自動生成

**実装例**:
```python
from app.config.table_definition import TableDefinitionGenerator

def upgrade():
    gen = TableDefinitionGenerator()
    
    for csv_type in gen.get_csv_types():
        # カラム定義を取得
        columns_def = gen.get_columns_definition(csv_type)
        
        # テーブル作成
        op.create_table(
            f"{csv_type}_shogun_flash",
            sa.Column("id", sa.Integer(), ...),
            *columns_def,
            schema="raw"
        )
        
        # インデックス作成
        index_columns = gen.generate_index_columns(csv_type)
        # ...
```

### 4. ORM モデル（動的生成）

**ファイル**: `app/repositories/dynamic_models.py`

**関数**:
- `create_shogun_model_class(csv_type)` - Python の `type()` を使って実行時にクラスを生成
- `get_shogun_model_class(csv_type)` - キャッシュ機能付きモデル取得

**生成されるモデル**:
- `ReceiveShogunFlash`
- `YardShogunFlash`
- `ShipmentShogunFlash`

**実装例**:
```python
def create_shogun_model_class(csv_type: str):
    gen = TableDefinitionGenerator()
    columns_def = gen.get_columns_definition(csv_type)
    
    # 動的にクラスを生成
    model_class = type(
        f"{csv_type.capitalize()}ShogunFlash",
        (Base,),
        {
            "__tablename__": f"{csv_type}_shogun_flash",
            "__table_args__": {"schema": "raw"},
            "id": Column(Integer, primary_key=True, ...),
            **{col.name: col for col in columns_def}
        }
    )
    return model_class
```

**orm_models.py での利用**:
```python
from app.repositories.dynamic_models import (
    ReceiveShogunFlash,
    YardShogunFlash,
    ShipmentShogunFlash,
)
```

### 5. リポジトリ（YAML ベースカラム検証）

**ファイル**: `app/repositories/shogun_csv_repo.py`

**変更内容**:
- 静的なモデルインポートを削除
- `get_shogun_model_class(csv_type)` で動的モデル取得
- DataFrame のカラムを YAML 定義に基づいてフィルタリング
- YAML に定義されていないカラムは自動除外

**実装例**:
```python
def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
    # 動的モデル取得
    model_class = get_shogun_model_class(csv_type)
    
    # YAML定義に基づくカラムフィルタリング
    gen = TableDefinitionGenerator()
    column_mapping = gen.get_column_mapping(csv_type)
    en_columns = list(column_mapping.values())
    
    # 定義されているカラムのみ抽出
    df_filtered = df[[col for col in en_columns if col in df.columns]]
    
    # 保存処理
    # ...
```

### 6. Settings（動的モデル対応）

**ファイル**: `app/config/settings.py`

**変更内容**:
- `get_orm_model_class(csv_type)` メソッドを動的生成版に変更
- `CSV_MASTERS_YAML_PATH` 環境変数を追加

**実装**:
```python
class Settings(BaseSettings):
    CSV_MASTERS_YAML_PATH: str = os.getenv(
        "CSV_MASTERS_YAML_PATH",
        "/backend/config/csv_config/syogun_csv_masters.yaml"
    )
    
    def get_orm_model_class(self, csv_type: str):
        from app.repositories.dynamic_models import get_shogun_model_class
        return get_shogun_model_class(csv_type)
```

### 7. エンドポイント

**ファイル**: `app/routers/database.py`

**変更なし**:
- すでに backend_shared のバリデーター・フォーマッターを使用
- これらも syogun_csv_masters.yaml をベースにしている
- フロー: CSV受信 → backend_shared でバリデート → backend_shared でフォーマット → リポジトリで保存

### 8. 環境変数設定

**ファイル**: `.env.example`

**追加した環境変数**:
```bash
# YAML Configuration Path (container path)
CSV_MASTERS_YAML_PATH=/backend/config/csv_config/syogun_csv_masters.yaml
```

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│                syogun_csv_masters.yaml                  │
│              (Single Source of Truth)                   │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   Migration   ORM Models   Repository
   (動的生成)   (動的生成)   (カラム検証)
        │           │           │
        └───────────┼───────────┘
                    ▼
              Database Tables
           (raw.{type}_shogun_flash)
```

## データフロー

```
1. フロントエンド（UploadPage.tsx）
   ↓ CSV ファイルアップロード
2. core_api/database.py エンドポイント
   ↓ backend_shared でバリデート（YAML ベース）
   ↓ backend_shared でフォーマット（YAML ベース）
3. ShogunCsvRepository
   ↓ 動的モデル取得（YAML ベース）
   ↓ カラムフィルタリング（YAML ベース）
4. PostgreSQL raw スキーマ
   - raw.receive_shogun_flash
   - raw.yard_shogun_flash
   - raw.shipment_shogun_flash
```

## メリット

### 1. 保守性の向上
- カラム追加・変更は YAML のみで完結
- Python コードの修正不要
- デプロイ不要（YAML マウント済み）

### 2. 一貫性の保証
- テーブル定義、ORM モデル、バリデーション、フォーマットがすべて YAML から生成
- 定義のズレが発生しない

### 3. 柔軟性
- 環境変数でパスを変更可能
- CSV 種別の追加が容易
- カラム定義の拡張が簡単

### 4. テスト容易性
- YAML を差し替えてテスト可能
- モックデータの作成が容易

## 今後の拡張ポイント

### 1. バリデーションルールの拡張
YAML に以下を追加可能:
```yaml
columns:
  slip_date:
    en_name: slip_date
    type: datetime
    validation:
      required: true
      range: [2020-01-01, 2030-12-31]
```

### 2. インデックス定義の拡張
YAML に明示的なインデックス定義を追加:
```yaml
indexes:
  - name: idx_slip_date_vendor
    columns: [slip_date, vendor_cd]
    unique: false
```

### 3. 外部キー制約の追加
YAML で他テーブルとの関連を定義:
```yaml
columns:
  vendor_cd:
    en_name: vendor_cd
    type: str
    foreign_key:
      table: core.vendors
      column: code
```

## デプロイ手順

### 1. コンテナ再ビルド
```bash
cd docker
docker compose -f docker-compose.dev.yml build core_api
```

### 2. マイグレーション実行
```bash
docker compose -f docker-compose.dev.yml exec core_api alembic upgrade head
```

### 3. 動作確認
```bash
# テーブル作成確認
docker compose -f docker-compose.dev.yml exec db psql -U myuser -d sanbou_dev -c "\dt raw.*"

# カラム定義確認
docker compose -f docker-compose.dev.yml exec db psql -U myuser -d sanbou_dev -c "\d raw.receive_shogun_flash"
```

### 4. フロントエンドから CSV アップロード
- UploadPage にアクセス
- 受入一覧/ヤード一覧/出荷一覧 CSV をアップロード
- データベースに保存されることを確認

## トラブルシューティング

### YAML ファイルが見つからない
```bash
# コンテナ内でパス確認
docker compose -f docker-compose.dev.yml exec core_api ls -la /backend/config/csv_config/

# マウント確認
docker compose -f docker-compose.dev.yml config | grep -A 5 volumes
```

### 型エラー（linting）
動的生成時の SQLAlchemy 型チェックエラーは実行時に問題なし（無視可能）

### カラムが見つからない
YAML の `columns` セクションに定義されているか確認:
```bash
grep -A 50 "^shipment:" /path/to/syogun_csv_masters.yaml
```

## 関連ファイル

### 新規作成
- `app/config/table_definition.py` - YAML パーサーとテーブル定義ジェネレーター
- `app/repositories/dynamic_models.py` - 動的 ORM モデル生成

### 修正
- `migrations/versions/002_add_raw_shogun_tables.py` - 動的生成に変更
- `app/repositories/orm_models.py` - 動的モデルインポート
- `app/repositories/shogun_csv_repo.py` - YAML ベースカラム検証
- `app/config/settings.py` - 動的モデル対応、YAML パス追加
- `.env.example` - CSV_MASTERS_YAML_PATH 追加

### 変更なし（すでに YAML ベース）
- `app/routers/database.py` - backend_shared 使用
- `backend_shared/infrastructure/config/config_loader.py` - YAML 読み込み
- `backend_shared/usecases/csv_formatter/*.py` - YAML ベースフォーマット
- `backend_shared/usecases/csv_validator/*.py` - YAML ベースバリデーション

## まとめ

`syogun_csv_masters.yaml` を唯一の真として、テーブル定義から ORM モデル、バリデーション、フォーマットまでを統一的に管理する YAML ファーストアーキテクチャが完成しました。

**変更箇所**:
- マイグレーション: YAML から動的生成
- ORM モデル: 実行時動的生成（`type()` 使用）
- リポジトリ: YAML ベースカラム検証
- Settings: 動的モデル取得対応

**次のステップ**:
1. コンテナ再ビルド
2. マイグレーション実行
3. CSV アップロードテスト
4. 本番環境展開
