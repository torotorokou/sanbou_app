# raw層への生データ保存失敗の根本原因分析レポート
**日付**: 2025-11-14  
**対象**: raw.receive_shogun_flash / raw.yard_shogun_flash / raw.shipment_shogun_flash  
**症状**: stg層には正常に保存されるが、raw層にはデータが保存されない（レコード数0件）

---

## 1. 問題の症状

### 1.1 現象
- **stg層**: `stg.receive_shogun_flash` に4487件のレコードが正常に保存されている
- **raw層**: `raw.receive_shogun_flash` のレコード数が0件（空）
- HTTPレスポンスは200 OK、エラーログなし
- UseCaseでは `raw_writer` と `stg_writer` の両方を呼び出している

### 1.2 データベーステーブル構造の違い

#### raw層（TEXT型のみ）
```sql
\d raw.receive_shogun_flash

 slip_date             | text
 sales_date            | text
 vendor_cd             | text
 vendor_name           | text
 slip_type_cd          | text
 net_weight            | text
 quantity              | text
 unit_price            | text
 amount                | text
 weighing_time_gross   | text
 weighing_time_empty   | text
 -- 全37カラムがTEXT型
```

#### stg層（型付き）
```sql
\d stg.receive_shogun_flash

 slip_date             | date
 sales_date            | date
 vendor_cd             | integer
 vendor_name           | text
 net_weight            | numeric(18,3)
 quantity              | numeric(18,3)
 unit_price            | numeric(18,2)
 amount                | numeric(18,0)
 weighing_time_gross   | time without time zone
 weighing_time_empty   | time without time zone
 -- 型が厳密に定義されている
```

---

## 2. 根本原因

### 2.1 型不一致による暗黙の保存失敗

**問題点**:
1. `create_shogun_model_class()` は `syogun_csv_masters.yaml` から型定義を読み込む
2. YAMLには `type: datetime`, `type: Int64`, `type: float` などの**型付き定義**が記載されている
3. **raw層のテーブルは全カラムTEXT型**だが、**ORMモデルはYAMLの型定義（Date, Integer, Numeric）を使用**
4. フォーマット済みデータ（datetime.date, int, float）をTEXT型カラムに挿入しようとして**型変換エラーが発生**
5. SQLAlchemyの `bulk_save_objects()` はエラーを静かに無視する場合がある

### 2.2 コード上の問題箇所

#### `dynamic_models.py` (Lines 26-88)
```python
def create_shogun_model_class(csv_type: str, table_name: str | None = None, schema: str = "stg") -> Type:
    # YAMLから型定義を取得
    columns_def = generator.get_columns_definition(csv_type)
    
    TYPE_MAPPING: Dict[str, Union[Type[TypeEngine[Any]], Callable[[], Any]]] = {
        'String': String,
        'Integer': Integer,
        'Int64': Integer,      # ← YAMLの Int64 → SQLAlchemy Integer
        'int': Integer,
        'Numeric': Numeric,
        'Date': Date,
        'datetime': Date,      # ← YAMLの datetime → SQLAlchemy Date
        'Boolean': lambda: lambda: None,
    }
    
    for col in columns_def:
        col_type_str = col['type']  # ← YAMLの型定義を使用
        # ...
        col_type_class = TYPE_MAPPING.get(col_type_str, String)
        # ← stg層には適切だが、raw層（全TEXT）には不適切
```

**問題**: スキーマによって型定義を変える仕組みがない

#### `shogun_csv_repository.py` (Lines 60-116)
```python
# フォーマット済みデータ（datetime.date, int, float）を作成
df = to_sql_ready_df(df)

# YAMLの型定義に基づくORMモデルを使用
model_class = create_shogun_model_class(csv_type, table_name=table_name, schema=schema)

# 型変換されたデータをORMオブジェクトに変換
for record in records:
    payload = deep_jsonable(record)  # datetime.date, int, float
    orm_objects.append(model_class(**payload))
    # ← raw層のTEXTカラムにdatetime.dateを挿入しようとする

# 保存（エラーが発生しても silent に失敗する可能性）
self.db.bulk_save_objects(orm_objects)
self.db.commit()
```

---

## 3. 設計上の誤解

### 3.1 当初の意図（推測）
- **raw層**: CSV生データをTEXT型でそのまま保存（型変換なし）
- **stg層**: フォーマット済みデータを型付きで保存（日付はDate型、数値はNumeric型）

### 3.2 実際の実装
- **両層とも** `to_sql_ready_df()` で型変換されたデータを受け取る
- **両層とも** YAMLの型定義に基づくORMモデルを使用
- **raw層のテーブル定義（TEXT型）とORMモデルの型定義（Date/Integer/Numeric）が不一致**

---

## 4. 解決策

### 4.1 【推奨】スキーマ別の型定義を使用

#### オプションA: raw層専用の全TEXT型モデルを生成
```python
def create_shogun_model_class(csv_type: str, table_name: str | None = None, schema: str = "stg") -> Type:
    columns_def = generator.get_columns_definition(csv_type)
    
    for col in columns_def:
        col_name = col['en_name']
        
        if schema == "raw":
            # raw層は全カラムTEXT型
            col_instance = Text()
        else:
            # stg層はYAMLの型定義を使用
            col_type_str = col['type']
            col_type_class = TYPE_MAPPING.get(col_type_str, String)
            col_instance = col_type_class()
```

#### オプションB: raw層用の生データ保存処理を分離
```python
class ShogunCsvRepository:
    def save_csv_by_type(self, csv_type: str, df: pd.DataFrame) -> int:
        if self._schema == "raw":
            # raw層: 型変換せずにCSV生データをTEXTとして保存
            return self._save_raw_text(csv_type, df)
        else:
            # stg層: 型変換してから保存
            return self._save_formatted(csv_type, df)
    
    def _save_raw_text(self, csv_type: str, df: pd.DataFrame) -> int:
        # DataFrameをそのまま文字列化してTEXT型カラムに保存
        df_text = df.astype(str)
        # TEXT型モデルを使用
        model_class = create_text_only_model(csv_type, table_name, schema="raw")
        # ...
```

### 4.2 データフロー修正案

#### Before（現在）
```
CSV → pandas.read_csv → to_sql_ready_df (型変換) → raw層 (TEXT) ← 型不一致
                                                  → stg層 (型付き) ← OK
```

#### After（修正後）
```
CSV → pandas.read_csv → df.astype(str) → raw層 (TEXT) ← OK
                       → to_sql_ready_df → stg層 (型付き) ← OK
```

---

## 5. 実装の優先順位

### Phase 1: 緊急対応（raw層への保存を有効化）
1. `create_shogun_model_class()` に `schema` による型切り替えを追加
2. `schema == "raw"` の場合は全カラムをTEXT型にする
3. `shogun_csv_repository.py` で生データを文字列化して保存

### Phase 2: アーキテクチャ改善（任意）
1. raw層とstg層で別のリポジトリクラスを使用
2. `RawTextCsvRepository` と `FormattedCsvRepository` に分離
3. UseCaseで両方を呼び出す

---

## 6. 検証手順

### 6.1 修正前の確認
```sql
SELECT COUNT(*) FROM raw.receive_shogun_flash;  -- 0
SELECT COUNT(*) FROM stg.receive_shogun_flash;  -- 4487
```

### 6.2 修正後の期待値
```sql
SELECT COUNT(*) FROM raw.receive_shogun_flash;  -- 4487
SELECT COUNT(*) FROM stg.receive_shogun_flash;  -- 4487

-- raw層のデータ型確認（すべて文字列）
SELECT slip_date, vendor_cd, net_weight 
FROM raw.receive_shogun_flash 
LIMIT 1;
-- slip_date  | vendor_cd | net_weight
-- 2024-04-01 | 12345     | 123.456

-- stg層のデータ型確認（型付き）
SELECT slip_date, vendor_cd, net_weight 
FROM stg.receive_shogun_flash 
LIMIT 1;
-- slip_date  | vendor_cd | net_weight
-- 2024-04-01 | 12345     | 123.456
```

---

## 7. 結論

**根本原因**: raw層のテーブル定義（全TEXT型）とORMモデルの型定義（YAMLベースの型付き）の不一致により、型変換エラーが発生して保存が失敗していた。

**解決策**: スキーマごとに異なる型定義を使用するようにORMモデル生成ロジックを修正する。

**影響範囲**:
- `app/backend/core_api/app/infra/db/dynamic_models.py`
- `app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`

**優先度**: **高**（raw層への保存が完全に機能していない）
