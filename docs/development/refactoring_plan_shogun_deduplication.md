# リファクタリング計画: 将軍データ取得の重複解消

**作成日:** 2025-12-18  
**ブランチ:** refactor/shogun-dataset-deduplication

---

## 📊 現状分析

### 発見された重複・類似コード

#### 1. **view名の重複定義**
**場所:**
- `backend_shared/db/names.py` - view名定数定義（既存）
- `backend_shared/shogun/dataset_keys.py` - view名生成ロジック（新規）
- `backend_shared/shogun/fetcher.py` - view名マッピング（新規）

**問題:**
```python
# db/names.py（既存）
V_ACTIVE_SHOGUN_FINAL_RECEIVE = "v_active_shogun_final_receive"

# shogun/dataset_keys.py（新規・重複）
def get_view_name(self) -> str:
    return f"v_active_{self.value}"  # 動的生成

# shogun/fetcher.py（新規・重複）
_VIEW_MAP = {
    ShogunDatasetKey.SHOGUN_FINAL_RECEIVE: V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    ...
}
```

#### 2. **テーブル名生成ロジックの重複**
**場所:**
- `core_api/app/infra/db/table_definition.py` - `get_table_name()`
- `core_api/app/infra/adapters/upload/shogun_csv_repository.py` - テーブル名生成
- `backend_shared/shogun/dataset_keys.py` - view名生成

**問題:**
```python
# table_definition.py
def get_table_name(self, csv_type: str, schema: str = "raw") -> str:
    table_name = f"shogun_flash_{csv_type}"
    return f"{schema}.{table_name}"

# dataset_keys.py
def get_view_name(self) -> str:
    return f"v_active_{self.value}"
```

#### 3. **ShogunCsvConfigLoader の多重使用**
**使用箇所（11箇所）:**
- `backend_shared/shogun/master_name_mapper.py` - master.yaml読み込み（新規）
- `backend_shared/config/di_providers.py` - DI設定（既存）
- `backend_shared/core/usecases/csv_formatter/` - CSV整形（既存）
- `core_api/app/config/di_providers.py` - DI設定（既存）
- その他多数

**問題:** 同じ設定を複数箇所で読み込み

#### 4. **カラム名変換ロジックの重複可能性**
**場所:**
- `backend_shared/shogun/master_name_mapper.py` - 英語⇔日本語変換（新規）
- `core_api/app/infra/db/table_definition.py` - `get_column_mapping()`（既存）
- `core_api/app/core/domain/shogun_flash_schemas.py` - 動的モデル生成（既存）

---

## 🎯 リファクタリング目標

### 原則
1. **単一真理の源（Single Source of Truth）**
2. **既存コードへの影響を最小化**
3. **段階的な移行（ベイビーステップ）**
4. **後方互換性の維持**

### 目標
- ✅ view名定義の一元化
- ✅ テーブル名生成ロジックの統一
- ✅ ConfigLoaderの最適化
- ✅ 不要な重複コードの削除

---

## 📋 リファクタリング計画（ベイビーステップ）

### Phase 1: view名定義の統一（最優先）

#### Step 1-1: dataset_keys.py から view名生成ロジックを削除
**理由:** `db/names.py` に既に定数定義があり、それが真理の源

**変更内容:**
```python
# BEFORE (dataset_keys.py)
def get_view_name(self) -> str:
    return f"v_active_{self.value}"

# AFTER
def get_view_name(self) -> str:
    # db/names.py の定数を使用（fetcher.py の _VIEW_MAP 経由）
    from backend_shared.db import names
    return getattr(names, f"V_ACTIVE_{self.value.upper()}")
```

**影響範囲:** 小（dataset_keys.py のみ）  
**破壊的変更:** なし（戻り値は同じ）

#### Step 1-2: fetcher.py の _VIEW_MAP を活用
**理由:** 既に db/names.py の定数をインポートしている

**現状確認:**
```python
# fetcher.py（既に正しい実装）
from backend_shared.db.names import (
    V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    ...
)

_VIEW_MAP = {
    ShogunDatasetKey.SHOGUN_FINAL_RECEIVE: V_ACTIVE_SHOGUN_FINAL_RECEIVE,
    ...
}
```

**変更:** 不要（既に正しい）

#### Step 1-3: dataset_keys.py のテスト更新
**変更:**
```python
# tests/test_shogun_fetcher.py
def test_get_view_name(self):
    # db/names.py の定数と一致することを確認
    from backend_shared.db.names import V_ACTIVE_SHOGUN_FINAL_RECEIVE
    assert ShogunDatasetKey.SHOGUN_FINAL_RECEIVE.get_view_name() == V_ACTIVE_SHOGUN_FINAL_RECEIVE
```

**工数:** 0.5時間  
**リスク:** 低

---

### Phase 2: テーブル名生成の統一（中優先）

#### Step 2-1: dataset_keys.py にテーブル名取得メソッド追加
**理由:** view名だけでなく、テーブル名も統一的に取得できるように

**変更内容:**
```python
# dataset_keys.py に追加
def get_table_name(self, schema: str = "stg") -> str:
    """
    対応するテーブル名を取得
    
    Returns:
        str: テーブル名（例: "shogun_final_receive"）
    """
    return self.value.replace("shogun_", "shogun_")  # そのまま
```

**工数:** 0.5時間  
**リスク:** 低

#### Step 2-2: table_definition.py との整合性確認
**確認事項:**
- `table_definition.py` は CSV種別（receive/shipment/yard）のみを扱う
- `dataset_keys.py` は完全なデータセット名（shogun_final_receive等）を扱う
- 両者は異なるレベルの抽象化 → **統合不要**

**判断:** Phase 2-2 はスキップ（統合の必要なし）

---

### Phase 3: ConfigLoader の最適化（低優先）

#### Step 3-1: master_name_mapper.py のキャッシュ確認
**現状:** 既に `@lru_cache` でキャッシュ済み

**確認:**
```python
@lru_cache(maxsize=1)
def _get_config_loader(self) -> ShogunCsvConfigLoader:
    return ShogunCsvConfigLoader(self.config_path)
```

**判断:** 最適化済み、変更不要

---

### Phase 4: 不要なコードの削除（低優先）

#### Step 4-1: 未使用インポートの削除
**対象:** 統合テスト用の一時ファイル

**削除候補:**
- `app/backend/backend_shared/test_integration.py` - 統合テスト用スクリプト（既に完了）

**工数:** 0.5時間  
**リスク:** なし

---

## 📊 優先順位と工数見積もり

| Phase | 内容 | 優先度 | 工数 | リスク |
|-------|------|--------|------|--------|
| 1-1 | dataset_keys.py view名生成修正 | 高 | 0.5h | 低 |
| 1-2 | fetcher.py 確認 | 高 | 0h | なし |
| 1-3 | テスト更新 | 高 | 0.5h | 低 |
| 2-1 | テーブル名取得メソッド追加 | 中 | 0.5h | 低 |
| 3-1 | ConfigLoader確認 | 低 | 0h | なし |
| 4-1 | 一時ファイル削除 | 低 | 0.5h | なし |

**合計工数:** 2時間

---

## ✅ 受入基準

### Phase 1 完了条件
- [ ] `dataset_keys.py` の `get_view_name()` が `db/names.py` の定数を使用
- [ ] 既存のテスト全てPASS
- [ ] 統合テストで動作確認

### Phase 2 完了条件
- [ ] `get_table_name()` メソッド追加
- [ ] ドキュメント更新

### 全体完了条件
- [ ] 全テストPASS
- [ ] ドキュメント更新
- [ ] コミット・プッシュ完了

---

## 🚨 リスク管理

### 低リスク要因
- ✅ 既存コードへの影響が限定的
- ✅ 後方互換性を維持
- ✅ テストでカバー可能

### 注意事項
- db/names.py の定数名変更には追従が必要
- 循環importの可能性（dataset_keys → names → ?）

---

## 📝 実装手順（ベイビーステップ）

### Step 1: Phase 1-1 実装
1. `dataset_keys.py` の `get_view_name()` 修正
2. ユニットテスト実行
3. コミット

### Step 2: Phase 1-3 実装
1. テスト更新
2. 全テスト実行
3. コミット

### Step 3: 統合テスト
1. 実DBで動作確認
2. 問題なければPhase 2へ

### Step 4: Phase 2-1 実装
1. `get_table_name()` 追加
2. テスト追加
3. コミット

### Step 5: Phase 4-1 実装
1. 不要ファイル削除
2. コミット

### Step 6: 最終確認
1. 全テスト実行
2. ドキュメント更新
3. プッシュ

---

**次のアクション:** Phase 1-1 の実装開始
