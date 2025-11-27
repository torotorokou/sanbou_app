# Step 3 レポート: Alembicマイグレーション作成完了

**実行日時**: 2025-11-14  
**対象ファイル**: `app/backend/core_api/migrations/alembic/versions/20251114_remove_en_suffix.py`

---

## 1. マイグレーション概要

### ファイル情報
- **Revision ID**: `20251114_remove_en_suffix`
- **Down Revision**: `20251114_120000000` (最新のheadから継続)
- **説明**: YAMLで定義されたカラム名から冗長な `_en_` 接尾辞を削除

### 対象テーブル (12テーブル)
```
raw.shipment_shogun_flash
raw.shipment_shogun_final
raw.yard_shogun_flash
raw.yard_shogun_final
stg.shipment_shogun_flash
stg.shipment_shogun_final
stg.yard_shogun_flash
stg.yard_shogun_final
```

※ payable/sales_summary テーブルは未作成のため対象外

---

## 2. カラム名変更の詳細

### shipment テーブル (8カラム)
| 旧カラム名 | 新カラム名 |
|-----------|----------|
| client_en_name | client_name |
| vendor_en_name | vendor_name |
| site_en_name | site_name |
| item_en_name | item_name |
| unit_en_name | unit_name |
| transport_vendor_en_name | transport_vendor_name |
| slip_type_en_name | slip_type_name |
| category_en_name | category_name |

### yard テーブル (6カラム)
| 旧カラム名 | 新カラム名 |
|-----------|----------|
| client_en_name | client_name |
| item_en_name | item_name |
| unit_en_name | unit_name |
| sales_staff_en_name | sales_staff_name |
| vendor_en_name | vendor_name |
| category_en_name | category_name |

**合計**: 14カラム × 2スキーマ(raw/stg) × 2バリアント(flash/final) = **56回のRENAME操作**

---

## 3. マイグレーション実装

### upgrade() メソッド
```python
for schema in ['raw', 'stg']:
    for table in ['shipment_shogun_flash', 'shipment_shogun_final']:
        for old_name, new_name in shipment_renames:
            op.execute(
                f"ALTER TABLE {schema}.{table} "
                f"RENAME COLUMN {old_name} TO {new_name}"
            )
```

### downgrade() メソッド
ロールバック可能 - 全てのカラム名を元の `*_en_*` 形式に戻す処理を実装済み

---

## 4. マイグレーション依存関係

### Before (branching発生)
```
20251113_180000000 (branchpoint)
├── 20251114_000600000 → 20251114_120000000 (head)
└── 20251114_remove_en_suffix (orphan head)
```

### After (修正済み)
```
20251113_180000000
└── 20251114_000600000
    └── 20251114_120000000
        └── 20251114_remove_en_suffix (new head)
```

✅ **線形な履歴に修正完了**

---

## 5. 実行前の状態確認

### 現在のテーブル構造
```sql
-- raw.shipment_shogun_flash の例
SELECT column_name FROM information_schema.columns 
WHERE table_schema = 'raw' AND table_name = 'shipment_shogun_flash';
```

現在のカラム:
```
slip_date
client_en_name          ← 変更対象
item_en_name            ← 変更対象
net_weight
quantity
unit_en_name            ← 変更対象
unit_price
amount
transport_vendor_en_name ← 変更対象
vendor_cd
vendor_en_name          ← 変更対象
site_cd
site_en_name            ← 変更対象
slip_type_en_name       ← 変更対象
shipment_no
detail_note
id
created_at
```

---

## 6. 想定される影響範囲

### データ保持
✅ **データは一切削除されない** - RENAME COLUMN操作のみ

### アプリケーションコードへの影響
⚠️ **次のファイルが新カラム名を参照する必要あり**:
- `shogun_csv_repository.py` - YAMLから新カラム名を読み込み済み
- `dataframe_to_model.py` - 動的モデル生成（YAMLベース）
- その他のクエリ実行箇所（要調査）

### インデックス・制約
✅ カラム名変更はインデックス・制約に自動的に反映される

---

## 7. 実行準備状況

### 前提条件チェック
- ✅ YAML定義が新カラム名に更新済み (Step 2完了)
- ✅ マイグレーションファイル作成完了
- ✅ 依存関係の整合性確認済み
- ✅ ロールバック処理実装済み

### 次ステップでの作業
1. `alembic upgrade head` 実行
2. テーブル構造の検証
3. 既存データの整合性確認

---

## 結論

**Step 3 完了 ✅**

- 56回のカラム名変更を行うマイグレーションを作成
- upgrade/downgrade両方実装済み
- マイグレーション履歴の整合性を確保
- データ損失リスクなし（RENAME操作のみ）

**次のアクション**: Step 4 - マイグレーション実行と検証に進む
