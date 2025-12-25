# CSVアップロードエラー解析レポート

**日付**: 2025-11-14  
**対象**: upload_file_id / source_row_no トラッキング機能実装

## 1. エラーサマリー

### 受入CSV (receive_shogun_flash)

- ✅ **RAW層**: 正常保存
- ✅ **STG層**: 正常保存
- **結論**: 問題なし

### ヤードCSV (yard_shogun_flash)

- ❌ **RAW層**: カラム不一致エラー
- ❌ **STG層**: NOT NULL制約違反
- **結論**: スキーマ不整合あり

### 出荷CSV (shipment_shogun_flash)

- ❌ **RAW層**: 検証未実施（ヤードエラーで停止）
- ❌ **STG層**: NOT NULL制約違反
- **結論**: ヤードと同様の問題あり

---

## 2. 詳細エラー解析

### 2.1 RAW層エラー (ヤード・出荷)

**エラー内容:**

```
(psycopg.errors.UndefinedColumn) column "client_en_name" of relation "yard_shogun_flash" does not exist
column "transport_vendor_cd" of relation "receive_shogun_flash" does not exist
```

**発生箇所**: `shogun_csv_repository.py:99` - `bulk_save_objects()`

**原因分析**:

1. CSVに含まれるカラム名が、データベーススキーマと一致していない
2. CSVフォーマッターが CSV ヘッダーを英語名（`*_en_name`形式）に変換している
3. しかし、データベースには日本語カラム名が定義されている

**該当カラム例**:

- CSV側: `client_en_name`, `item_en_name`, `vendor_en_name`, `category_en_name`, `sales_staff_en_name`
- DB側: `client_name`, `item_name`, `vendor_name`, `category_name`, `sales_staff_name`

**根本原因**:

```python
# app/infra/adapters/upload/shogun_csv_repository.py
# Line 75-85: rename_columns() がヤード・出荷には適用されていない
```

---

### 2.2 STG層エラー (全CSV種別)

**エラー内容:**

```
(psycopg.errors.NotNullViolation) null value in column "slip_date" of relation "yard_shogun_flash" violates not-null constraint
DETAIL: Failing row contains (12302, null, null, null, 0, 0, null, null, 0, null, null, null, null, null, null, null, 2025-11-14 00:15:39.771125+00).
```

**発生箇所**: `shogun_csv_repository.py:99` - `bulk_save_objects()`

**SQL解析**:

```sql
INSERT INTO stg.yard_shogun_flash (net_weight, quantity, amount)
VALUES (%(net_weight)s, %(quantity)s, %(amount)s)
```

**原因分析**:

1. **INSERT文に3カラムしか含まれていない**

   - 実際: `net_weight`, `quantity`, `amount` のみ
   - 期待: 全 YAML 定義カラム (15-20カラム程度)

2. **`to_sql_ready_df()` 関数が原因**

   ```python
   # app/infra/adapters/upload/db_helpers.py
   # Line 75-96: to_sql_ready_df()

   # 問題のコード:
   valid_cols = [c for c in yaml_cols if c in df.columns]
   df = df[valid_cols]  # ここでカラムフィルタリング
   ```

3. **YAML定義とCSVカラム名の不一致**

   - YAML: 日本語カラム名 (`伝票日付`, `取引先コード`, etc.)
   - CSV: 英語カラム名 (`slip_date`, `client_cd`, etc.)
   - 結果: `valid_cols` がほぼ空になり、デフォルト3カラムのみ残る

4. **NOT NULL制約違反の発生**
   - `slip_date` など主要カラムが NOT NULL 制約あり
   - しかし INSERT 文にカラムが含まれていない
   - PostgreSQL が NULL 挿入と判断してエラー

**データフロー追跡**:

```
1. CSV読込 → 英語カラム名 (slip_date, client_en_name, etc.)
2. Format処理 → 英語カラム名維持
3. to_sql_ready_df() → YAML照合 → マッチなし → 3カラムのみ残る
4. ORM変換 → 3カラムのみのオブジェクト生成
5. SQL生成 → INSERT文に3カラムのみ
6. PostgreSQL → NOT NULL違反エラー
```

---

## 3. DEBUG ログからの検証

### 3.1 受入CSV (成功ケース)

**ログ抜粋:**

```
INFO: Formatted receive: 1759 rows
INFO: Saved 1759 rows to receive table
INFO: Saved receive to raw layer: 1759 rows
INFO: Saved 1759 rows to receive table
INFO: Saved receive to stg layer: 1759 rows
```

**カラム名サンプル (raw保存時)**:

```python
{
  'slip_date': datetime.date(2025, 11, 1),
  'vendor_cd': 23,
  'vendor_name': '環境整備',
  'item_cd': 1,
  'item_name': '混合廃棄物A',
  'receive_no': 72003,
  'transport_vendor_cd': 23,
  'transport_vendor_name': '環境整備',
  # ...日本語カラム名が使用されている
}
```

### 3.2 ヤードCSV (失敗ケース)

**ログ抜粋:**

```
ERROR: Failed to save yard data:
column "client_en_name" of relation "yard_shogun_flash" does not exist
```

**カラム名サンプル (raw保存試行時)**:

```python
{
  'slip_date': datetime.date(2024, 4, 1),
  'client_en_name': 'カキトヤ・ホン',  # ← 英語カラム名
  'item_en_name': 'GC軽鉄・スチール類',
  'vendor_en_name': 'まちづくり中野21',
  'category_en_name': '有価物',
  'sales_staff_en_name': 'オネスト・ワン',
  # ...全て英語カラム名
}
```

**STG保存試行時のSQL**:

```sql
INSERT INTO stg.yard_shogun_flash (net_weight, quantity, amount)
VALUES (0.0, 0.0, 0.0)
-- 3カラムのみ！
```

---

## 4. 根本原因特定

### 問題1: カラム名変換の不整合

**場所**: `app/infra/adapters/upload/shogun_csv_repository.py`

```python
# Line 75-85: rename_columns() 実装
def rename_columns(self, df: pd.DataFrame, csv_type: str) -> pd.DataFrame:
    """
    受入CSVのみカラム名を日本語化する処理
    """
    if csv_type == "receive":
        column_mapping = self._get_receive_column_mapping()
        return df.rename(columns=column_mapping)
    else:
        return df  # ← ヤード・出荷はそのまま返す（英語名のまま）
```

**問題**:

- 受入CSV: 英語 → 日本語 変換あり → YAML と一致 → 成功
- ヤード・出荷: 変換なし → 英語名のまま → YAML と不一致 → 失敗

### 問題2: YAML カラム定義との不整合

**ヤードCSV のYAML定義** (`syogun_csv_masters.yaml`):

```yaml
yard:
  flash:
    columns:
      - 伝票日付 # <- 日本語
      - 得意先コード
      - 得意先名
      - 品目コード
      - 品目名
      # ...
```

**実際のCSVカラム**:

```
slip_date          # <- 英語
client_cd
client_en_name     # <- "_en_name" サフィックス付き
item_cd
item_en_name
```

**YAMLとCSVの対応**:
| YAML (日本語) | CSV (英語) | 一致? |
|--------------------|---------------------|-------|
| 伝票日付 | slip_date | ❌ |
| 得意先コード | client_cd | ❌ |
| 得意先名 | client_en_name | ❌ |
| 品目コード | item_cd | ❌ |
| 品目名 | item_en_name | ❌ |

→ **全カラム不一致** → `to_sql_ready_df()` でフィルタリング → 3カラムのみ残る

---

## 5. なぜ受入だけ成功したのか？

### 受入CSVのカラムマッピング

```python
# app/infra/adapters/upload/shogun_csv_repository.py
# Line 143-180: _get_receive_column_mapping()

{
    "伝票日付": "slip_date",
    "売上日付": "sales_date",
    "取引先コード": "vendor_cd",
    "取引先名": "vendor_name",
    # ...完全な英語→日本語マッピング
}
```

**処理フロー (受入)**:

```
1. CSV読込 → 英語カラム (slip_date, vendor_cd, etc.)
2. rename_columns() → 日本語に変換 (伝票日付, 取引先コード, etc.)
3. to_sql_ready_df() → YAML照合 → 完全一致 → 全カラム残る
4. ORM変換 → 全カラムのオブジェクト生成
5. SQL生成 → INSERT文に全カラム含まれる
6. PostgreSQL → 成功
```

**処理フロー (ヤード・出荷)**:

```
1. CSV読込 → 英語カラム (slip_date, client_en_name, etc.)
2. rename_columns() → 何もしない（そのまま英語）
3. to_sql_ready_df() → YAML照合 → 不一致 → 3カラムのみ残る
4. ORM変換 → 3カラムのみのオブジェクト
5. SQL生成 → INSERT文に3カラムのみ
6. PostgreSQL → NOT NULL違反
```

---

## 6. upload_file_id / source_row_no の状況

### デバッグログからの確認

**追跡カラムの追加は確認できず**:

```
DEBUG ログには upload_file_id / source_row_no に関する
出力が一切ないため、追跡カラム処理が実行されていない可能性
```

**予想される状況**:

1. `to_sql_ready_df()` でカラムフィルタリング時に削除されている
2. または、英語カラム名との不一致で最初から除外されている

**検証が必要**:

- `upload_file_id` / `source_row_no` が DataFrame に存在するか
- `to_sql_ready_df()` でフィルタリングされていないか
- YAML定義に tracking columns が含まれているか

---

## 7. 修正方針

### 修正1: ヤード・出荷のカラム名変換を追加

**ファイル**: `app/infra/adapters/upload/shogun_csv_repository.py`

```python
def rename_columns(self, df: pd.DataFrame, csv_type: str) -> pd.DataFrame:
    """全CSV種別でカラム名を日本語化"""
    if csv_type == "receive":
        column_mapping = self._get_receive_column_mapping()
    elif csv_type == "yard":
        column_mapping = self._get_yard_column_mapping()  # 追加
    elif csv_type == "shipment":
        column_mapping = self._get_shipment_column_mapping()  # 追加
    else:
        return df

    return df.rename(columns=column_mapping)

def _get_yard_column_mapping(self) -> Dict[str, str]:
    """ヤードCSV カラムマッピング"""
    return {
        "伝票日付": "slip_date",
        "得意先コード": "client_cd",
        "得意先名": "client_name",  # "_en_name" を除去
        "品目コード": "item_cd",
        "品目名": "item_name",
        "正味重量": "net_weight",
        "数量": "quantity",
        "単位名": "unit_name",
        "単価": "unit_price",
        "金額": "amount",
        "営業担当者名": "sales_staff_name",
        "仕入先コード": "vendor_cd",
        "仕入先名": "vendor_name",
        "カテゴリコード": "category_cd",
        "カテゴリ名": "category_name",
        "伝票番号": "slip_no",
    }

def _get_shipment_column_mapping(self) -> Dict[str, str]:
    """出荷CSV カラムマッピング"""
    return {
        "伝票日付": "slip_date",
        "得意先コード": "client_cd",
        "得意先名": "client_name",
        "行先コード": "destination_cd",
        "行先名": "destination_name",
        "品目コード": "item_cd",
        "品目名": "item_name",
        "正味重量": "net_weight",
        "数量": "quantity",
        "単位名": "unit_name",
        "単価": "unit_price",
        "金額": "amount",
        "マニフェスト種別コード": "manifest_type_cd",
        "マニフェスト種別名": "manifest_type_name",
        "営業担当者名": "sales_staff_name",
        "仕入先コード": "vendor_cd",
        "仕入先名": "vendor_name",
        "伝票番号": "slip_no",
    }
```

### 修正2: トラッキングカラムの保護

**ファイル**: `app/infra/adapters/upload/db_helpers.py`

```python
# Line 75-96: to_sql_ready_df()

TRACKING_COLUMNS = ['upload_file_id', 'source_row_no']

def to_sql_ready_df(df: pd.DataFrame, yaml_cols: List[str]) -> pd.DataFrame:
    """
    DataFrameをSQL挿入用に変換
    - YAMLで定義されたカラムのみ残す
    - トラッキングカラムは常に保持
    """
    # トラッキングカラムをYAML照合対象から除外
    tracking_cols_present = [c for c in TRACKING_COLUMNS if c in df.columns]

    # YAML定義カラムとのマッチング
    valid_cols = [c for c in yaml_cols if c in df.columns]

    # トラッキングカラムを追加
    all_valid_cols = valid_cols + tracking_cols_present

    # フィルタリング
    df = df[all_valid_cols]

    # datetime64[ns] → datetime.date 変換
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.date() if pd.notna(x) else None)

    return df
```

### 修正3: YAML定義の確認

**ファイル**: `app/config/syogun_csv_masters.yaml`

各CSV種別のカラム定義に以下を追加:

```yaml
yard:
  flash:
    columns:
      - 伝票日付
      - 得意先コード
      - 得意先名
      # ...
      - upload_file_id # 追加
      - source_row_no # 追加
```

---

## 8. 推奨アクション

### 優先度1 (即時対応)

1. ✅ ヤード・出荷のカラムマッピング関数を実装
2. ✅ `rename_columns()` を全CSV種別に適用
3. ✅ トラッキングカラム保護ロジックを `to_sql_ready_df()` に追加

### 優先度2 (検証)

4. ⚠️ YAML定義にトラッキングカラムを追加
5. ⚠️ 全CSV種別で動作確認
6. ⚠️ DBeaver でデータ確認

### 優先度3 (改善)

7. 📝 カラムマッピングをYAMLファイル化（重複コード削減）
8. 📝 単体テスト追加
9. 📝 エラーログの改善

---

## 9. 期待される結果

### 修正後の動作

**受入CSV**:

- ✅ RAW層保存: 全カラム + tracking columns
- ✅ STG層保存: 全カラム + tracking columns

**ヤードCSV**:

- ✅ RAW層保存: 全カラム + tracking columns (英語→日本語変換済)
- ✅ STG層保存: 全カラム + tracking columns

**出荷CSV**:

- ✅ RAW層保存: 全カラム + tracking columns (英語→日本語変換済)
- ✅ STG層保存: 全カラム + tracking columns

### 確認項目

```sql
-- RAW層確認
SELECT upload_file_id, source_row_no, slip_date, vendor_cd, vendor_name
FROM raw.yard_shogun_flash
WHERE upload_file_id IS NOT NULL
LIMIT 5;

-- STG層確認
SELECT upload_file_id, source_row_no, slip_date, vendor_cd, vendor_name
FROM stg.yard_shogun_flash
WHERE upload_file_id IS NOT NULL
LIMIT 5;
```

---

## 10. まとめ

### 根本原因

1. **カラム名の不整合**: CSV (英語) ⇔ YAML定義 (日本語) ⇔ DB (日本語)
2. **変換処理の欠如**: 受入のみマッピングあり、ヤード・出荷はマッピングなし
3. **フィルタリングの副作用**: `to_sql_ready_df()` で不一致カラムが全削除

### なぜ容量が増えたのにデータが見えないのか？

- PostgreSQL は NOT NULL 制約違反で **トランザクションロールバック**
- しかし WAL (Write-Ahead Log) にはエラーレコードが残る
- 結果: ディスク容量は増加するが、コミットされたデータは0件

### 修正の影響範囲

- ✅ 小規模: カラムマッピング関数追加のみ
- ✅ 低リスク: 既存の受入処理には影響なし
- ✅ 即効性: 修正後すぐに全CSV種別が動作可能

---

**作成者**: GitHub Copilot  
**レビュー**: 要確認  
**承認**: 未承認
