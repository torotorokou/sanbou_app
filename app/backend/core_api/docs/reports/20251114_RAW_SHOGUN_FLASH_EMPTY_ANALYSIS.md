# raw.\*\_shogun_flash テーブルが空になる問題の分析レポート

**日付**: 2025-11-14  
**ステータス**: 🔴 重大な不具合

---

## 📌 問題の概要

フロントエンドから `/core_api/database/upload/syogun_csv_flash` にCSVをアップロードすると：

- ✅ **stg層** (`stg.receive_shogun_flash`) にはデータが正常に保存される（17,948件確認）
- ❌ **raw層** (`raw.receive_shogun_flash`) は空のまま（0件）

### 期待される動作

raw層には**生データ（TEXT型）**として各CSVの内容を保存し、監査・トレーサビリティを確保すること。

---

## 🔍 原因分析

### 1. DI設定の不一致

#### **問題箇所**: `app/backend/core_api/app/config/di_providers.py` L127-148

```python
def get_uc_default(
    raw_repo: ShogunCsvRepository = Depends(get_repo_raw_default),  # ← raw.receive_shogun_flash
    stg_repo: ShogunCsvRepository = Depends(get_repo_stg_flash),
    raw_data_repo: RawDataRepository = Depends(get_raw_data_repo)
) -> UploadSyogunCsvUseCase:
    """デフォルト用のUploadSyogunCsvUseCase (raw.receive_shogun_flash + stg.receive_shogun_flash)"""
    ...

def get_uc_flash(
    raw_repo: ShogunCsvRepository = Depends(get_repo_raw_flash),  # ← raw.receive_csv_flash
    stg_repo: ShogunCsvRepository = Depends(get_repo_stg_flash),
    raw_data_repo: RawDataRepository = Depends(get_raw_data_repo)
) -> UploadSyogunCsvUseCase:
    """Flash用のUploadSyogunCsvUseCase (raw.receive_csv_flash + stg.receive_shogun_flash)"""
    ...
```

#### **問題内容**

- `/database/upload/syogun_csv_flash` エンドポイントは `get_uc_flash` を使用
- `get_uc_flash` は `get_repo_raw_flash` を注入
- `get_repo_raw_flash` は **存在しないテーブル** `raw.receive_csv_flash` を参照

#### **DB構造の実態**

```sql
-- ✅ 存在するテーブル（Alembicで作成済み）
raw.receive_shogun_flash   -- TEXT型カラム
raw.yard_shogun_flash      -- TEXT型カラム
raw.shipment_shogun_flash  -- TEXT型カラム

-- ❌ 存在しないテーブル（DI設定で参照されているが未作成）
raw.receive_csv_flash
raw.yard_csv_flash
raw.shipment_csv_flash
```

#### **保存処理の実態**

`shogun_csv_repository.py` L95-104:

```python
# スキーマとテーブル名の決定
schema = self._schema or "stg"

# テーブル名の上書きチェック
override_table = self._table_map.get(csv_type)
if override_table:
    # table_map が指定された場合: カスタムテーブル名を使用
    table_name = override_table  # ← "receive_csv_flash" （存在しない）
else:
    # table_map が未指定の場合: デフォルトは *_shogun_flash
    table_name = f"{csv_type}_shogun_flash"  # ← 正しいテーブル名
```

**結果**: 存在しないテーブル `raw.receive_csv_flash` への保存を試みるため、エラーまたはスキップが発生。

---

### 2. エンドポイントとDI設定のマッピング不整合

#### **router.py** の設定状況

| エンドポイント             | UseCase            | raw層テーブル（実際）      | raw層テーブル（DI設定）    | ステータス    |
| -------------------------- | ------------------ | -------------------------- | -------------------------- | ------------- |
| `/upload/syogun_csv`       | `get_uc_default`   | `raw.receive_shogun_flash` | `raw.receive_shogun_flash` | ✅ 一致       |
| `/upload/syogun_csv_flash` | `get_uc_flash`     | `raw.receive_shogun_flash` | `raw.receive_csv_flash`    | ❌ **不一致** |
| `/upload/syogun_csv_final` | `get_uc_stg_final` | `raw.receive_shogun_final` | `raw.receive_csv_final`    | ❌ **不一致** |

---

### 3. テーブル名命名規則の混乱

プロジェクト内で以下の3つの命名パターンが混在：

1. **`*_shogun_flash`** / **`*_shogun_final`** ← Alembicで作成済み、正式なテーブル名
2. **`*_csv_flash`** / **`*_csv_final`** ← DI設定で誤って参照されている
3. **`*_raw`** ← 旧バージョン（廃止予定）

**結論**: 命名規則の統一ができておらず、DIとDBスキーマが乖離している。

---

## 📋 影響範囲

### 現在の状況

- ✅ **stg層**: 正常動作（データ保存成功）
- ❌ **raw層**: データが保存されず空のまま
- ⚠️ **監査ログ**: `log.upload_file` には記録されているが、生データが存在しない

### リスク

1. **データトレーサビリティの欠如**: 元のCSVデータが保存されていない
2. **監査対応不可**: 「いつ・誰が・何をアップロードしたか」の証跡が不完全
3. **データ復元不可**: 誤操作時に元データから復元できない
4. **規制対応**: 将来的にデータの完全性証明が困難

---

## 🛠️ 修正方針

### ✅ 推奨される修正（命名規則統一）

#### **Option A: `*_shogun_flash` / `*_shogun_final` に統一（推奨）**

- Alembicで作成済みのテーブル名に合わせる
- DI設定を修正（`*_csv_flash` → `*_shogun_flash`）
- コードの変更量が最小

#### 修正対象ファイル

1. **`di_providers.py`** - `get_repo_raw_flash`, `get_repo_raw_final` の table_map 修正
2. **`router.py`** - コメント修正（ドキュメント整合性）

---

### ❌ 非推奨の修正（DBスキーマ変更）

#### **Option B: `*_csv_flash` / `*_csv_final` テーブルを作成**

- 新しいAlembicマイグレーションで `raw.receive_csv_flash` 等を作成
- 既存テーブル `raw.receive_shogun_flash` と重複
- テーブルが増えてメンテナンス負荷が増大

**理由**:

- 既に `raw.*_shogun_flash` テーブルが存在し、構造も適切
- 重複テーブルを作成する意味がない
- データベース肥大化・管理コスト増

---

## 📝 推奨される修正内容

### 1. `di_providers.py` の修正

```python
def get_repo_raw_flash(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    raw層flash用 (raw schema, *_shogun_flash tables)
    """
    return ShogunCsvRepository(
        db,
        schema="raw",
        # table_map を削除（デフォルトの *_shogun_flash を使用）
    )


def get_repo_raw_final(db: Session = Depends(get_db)) -> ShogunCsvRepository:
    """
    raw層final用 (raw schema, *_shogun_final tables)
    """
    return ShogunCsvRepository(
        db,
        schema="raw",
        table_map={
            "receive": "receive_shogun_final",
            "yard": "yard_shogun_final",
            "shipment": "shipment_shogun_final",
        },
    )
```

### 2. `router.py` のドキュメント修正

```python
@router.post("/upload/syogun_csv_flash")
async def upload_syogun_csv_flash(...):
    """
    将軍CSVアップロード（速報版）

    保存先:
    - raw層: raw.receive_shogun_flash / raw.yard_shogun_flash / raw.shipment_shogun_flash
    - stg層: stg.receive_shogun_flash / stg.yard_shogun_flash / stg.shipment_shogun_flash
    """
```

---

## ✅ 修正後の動作確認項目

1. ✅ raw層にデータが保存される（TEXT型）
2. ✅ stg層にデータが保存される（型付きカラム）
3. ✅ `log.upload_file` のステータスが正常
4. ✅ 3種類のエンドポイント全て正常動作

---

## 📌 補足: raw層とstg層の役割

### **raw層** (`raw.*_shogun_flash`)

- **目的**: 生データの保存（TEXT型）
- **用途**: 監査ログ、データトレーサビリティ、復元用
- **特徴**: カラム全てが `TEXT` 型、型変換なし

### **stg層** (`stg.*_shogun_flash`)

- **目的**: 構造化データの保存（型付き）
- **用途**: ビジネスロジック、集計、レポート生成
- **特徴**: `DATE`, `NUMERIC`, `TEXT` 等の適切な型でカラム定義

---

## 📚 関連ファイル

- `app/backend/core_api/app/config/di_providers.py`
- `app/backend/core_api/app/presentation/routers/database/router.py`
- `app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`
- `app/backend/core_api/migrations/alembic/versions/20251113_175000000_create_raw_shogun_flash_final_tables.py`

---

## ⚠️ 緊急度

**高**: 現状では監査ログが機能していないため、早急な修正が必要。
