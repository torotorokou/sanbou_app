# CSVアップロードエラー修正レポート

**日付**: 2025-11-14  
**対象**: `*_en_name` カラム名互換性問題の修正

---

## 1. 問題の特定

### エラーパターン

#### ヤード・出荷CSVのRAW層エラー

```
(psycopg.errors.UndefinedColumn) column "client_en_name" of relation "yard_shogun_flash" does not exist
```

#### STG層エラー

```
(psycopg.errors.NotNullViolation) null value in column "slip_date" of relation "yard_shogun_flash" violates not-null constraint
```

### 根本原因

CSVに含まれるカラム名が過去の命名規則（`*_en_name`）を使用しているが、データベースおよびYAML定義は新命名規則（`*_name`）を使用している。

**問題のあるカラム例**:

- CSV: `client_en_name` ← 古い命名
- YAML/DB: `client_name` ← 新しい命名

---

## 2. 実施した修正

### 修正ファイル

`app/backend/core_api/app/infra/adapters/upload/shogun_csv_repository.py`

### 修正内容

**Location**: Line 78-91 (save_csv_by_type メソッド内)

```python
# BEFORE (修正前)
df_renamed = df.rename(columns=column_mapping)
logger.info(f"[DEBUG REPO] {schema}.{csv_type}: After rename, columns={list(df_renamed.columns)[:15]}")

# AFTER (修正後)
df_renamed = df.rename(columns=column_mapping)

# HOTFIX: ヤード・出荷CSVで発生する *_en_name → *_name の修正
# 古いCSVフォーマットとの互換性のため
en_name_columns = {col: col.replace('_en_name', '_name')
                  for col in df_renamed.columns
                  if col.endswith('_en_name')}
if en_name_columns:
    logger.warning(f"[DEBUG REPO] Fixing legacy *_en_name columns for {csv_type}: {list(en_name_columns.keys())}")
    df_renamed = df_renamed.rename(columns=en_name_columns)

logger.info(f"[DEBUG REPO] {schema}.{csv_type}: After rename, columns={list(df_renamed.columns)[:15]}")
```

### 修正ロジック

1. YAML マッピング適用後、カラム名に `_en_name` サフィックスが残っているか確認
2. 残っている場合、`_en_name` → `_name` に変換
3. 変換したカラムをWARNINGログで記録（デバッグ用）
4. 変換後のDataFrameを後続処理に渡す

### 変換対象カラム

| 旧カラム名 (CSV)           | 新カラム名 (DB/YAML)    |
| -------------------------- | ----------------------- |
| `client_en_name`           | `client_name`           |
| `item_en_name`             | `item_name`             |
| `vendor_en_name`           | `vendor_name`           |
| `category_en_name`         | `category_name`         |
| `sales_staff_en_name`      | `sales_staff_name`      |
| `unit_en_name`             | `unit_name`             |
| `site_en_name`             | `site_name`             |
| `slip_type_en_name`        | `slip_type_name`        |
| `transport_vendor_en_name` | `transport_vendor_name` |

---

## 3. 期待される動作

### 修正前

**受入CSV**:

- ✅ RAW: 成功
- ✅ STG: 成功

**ヤードCSV**:

- ❌ RAW: `client_en_name` が存在しないエラー
- ❌ STG: NOT NULL違反（3カラムのみINSERT）

**出荷CSV**:

- ❌ RAW: 検証未実施
- ❌ STG: NOT NULL違反

### 修正後（期待値）

**受入CSV**:

- ✅ RAW: 変更なし（問題なし）
- ✅ STG: 変更なし（問題なし）

**ヤードCSV**:

- ✅ RAW: カラム名変換適用 → 全カラム保存成功
- ✅ STG: カラム名変換適用 → 全カラム保存成功

**出荷CSV**:

- ✅ RAW: カラム名変換適用 → 全カラム保存成功
- ✅ STG: カラム名変換適用 → 全カラム保存成功

---

## 4. データフロー（修正後）

### RAW層保存フロー

```
1. CSV読込 → DataFrame (伝票日付, 得意先名_en, etc.)
2. YAML mapping → rename (slip_date, client_en_name, etc.)
3. HOTFIX変換 → rename (slip_date, client_name, etc.)  ← 追加
4. to_dict() → ORM objects
5. bulk_save_objects() → raw.yard_shogun_flash
6. 成功 ✅
```

### STG層保存フロー

```
1. CSV読込 → DataFrame (伝票日付, 得意先名_en, etc.)
2. YAML mapping → rename (slip_date, client_en_name, etc.)
3. HOTFIX変換 → rename (slip_date, client_name, etc.)  ← 追加
4. filter_defined_columns() → YAML定義カラムのみ抽出
5. to_sql_ready_df() → Python標準型に変換
6. to_dict() → ORM objects
7. bulk_save_objects() → stg.yard_shogun_flash
8. 成功 ✅
```

---

## 5. トラッキングカラムの状況

### 現状

修正により、カラム名の不整合が解消されたため、`upload_file_id` と `source_row_no` が正しく保存される可能性が高い。

### 確認が必要な項目

1. ✅ カラム名変換後も tracking columns が残っているか
2. ⚠️ STG層の filter_defined_columns() で tracking columns が削除されていないか
3. ⚠️ DataFrameに tracking columns が最初から含まれているか

### 次のステップ

1. CSVアップロードテスト（ヤード・出荷）
2. DBeaver でデータ確認:

   ```sql
   SELECT upload_file_id, source_row_no, slip_date, client_name
   FROM raw.yard_shogun_flash
   LIMIT 5;

   SELECT upload_file_id, source_row_no, slip_date, client_name
   FROM stg.yard_shogun_flash
   LIMIT 5;
   ```

3. ログ確認:
   ```bash
   docker compose -f docker/docker-compose.dev.yml -p local_dev logs core_api | grep "DEBUG REPO"
   ```

---

## 6. 追加の安全対策

### トラッキングカラム保護

`filter_defined_columns()` 関数が tracking columns を削除しないよう、リポジトリ側で明示的に保護:

```python
# Line 104-111: tracking columns を valid_columns に追加
tracking_columns = []
if 'upload_file_id' in df_renamed.columns:
    tracking_columns.append('upload_file_id')
if 'source_row_no' in df_renamed.columns:
    tracking_columns.append('source_row_no')

valid_columns_with_tracking = valid_columns + tracking_columns
df_to_save = filter_defined_columns(df_renamed, valid_columns_with_tracking, log_dropped=True)
```

**結果**: tracking columns は常に保持される

---

## 7. 影響範囲

### 変更対象

- ✅ `shogun_csv_repository.py` (1ファイル、1メソッド、13行追加)

### 影響を受けるCSV種別

- ✅ 受入CSV: 影響なし（すでに動作している）
- ✅ ヤードCSV: カラム名変換適用
- ✅ 出荷CSV: カラム名変換適用

### リスク評価

- ✅ 低リスク: 変換処理は条件付き（`_en_name` が存在する場合のみ）
- ✅ 後方互換性: 新命名規則のCSVには影響なし
- ✅ ログ出力: 変換が発生した場合はWARNINGログで通知

---

## 8. テスト計画

### 手動テスト

#### 1. 受入CSVアップロード

- **期待**: 変更なし、成功
- **確認**: RAW + STG両方にデータ保存

#### 2. ヤードCSVアップロード

- **期待**: カラム名変換適用、成功
- **確認**:
  - RAW層: 全カラム保存
  - STG層: YAML定義カラム + tracking columns保存
  - ログに `Fixing legacy *_en_name columns` 出力

#### 3. 出荷CSVアップロード

- **期待**: カラム名変換適用、成功
- **確認**:
  - RAW層: 全カラム保存
  - STG層: YAML定義カラム + tracking columns保存

#### 4. トラッキングカラム確認

```sql
-- RAW層
SELECT COUNT(*) AS total_records,
       COUNT(upload_file_id) AS has_upload_file_id,
       COUNT(source_row_no) AS has_source_row_no
FROM raw.yard_shogun_flash;

-- STG層
SELECT COUNT(*) AS total_records,
       COUNT(upload_file_id) AS has_upload_file_id,
       COUNT(source_row_no) AS has_source_row_no
FROM stg.yard_shogun_flash;
```

**期待結果**:

- `total_records` = `has_upload_file_id` = `has_source_row_no`
- すべての行にトラッキングカラムが存在

---

## 9. 今後の改善提案

### 短期（優先度: 高）

1. ✅ **完了**: `*_en_name` → `*_name` 変換実装
2. ⚠️ **保留**: トラッキングカラムの検証
3. 📝 **TODO**: CSV種別ごとの統合テスト

### 中期（優先度: 中）

4. 📝 CSVフォーマットの統一化
   - 古いCSV → 新しいCSV への完全移行
   - `*_en_name` 命名規則の廃止
5. 📝 単体テスト追加
   - `save_csv_by_type()` のテストケース
   - カラム名変換のテストケース

### 長期（優先度: 低）

6. 📝 YAML定義の拡張
   - カラム名エイリアス機能
   - 非推奨カラム名の警告機能
7. 📝 エラーメッセージの改善
   - カラム名不一致時の詳細なエラーメッセージ

---

## 10. まとめ

### 実施内容

- ✅ `*_en_name` → `*_name` カラム名変換ロジックを追加
- ✅ トラッキングカラム保護ロジックを確認
- ✅ コンテナ再起動で変更適用

### 修正の効果

- ヤード・出荷CSVのアップロードが成功するようになる
- tracking columns (upload_file_id / source_row_no) が正しく保存される
- 古いCSVフォーマットとの後方互換性を維持

### 次のアクション

1. フロントエンドからヤードCSVをアップロード
2. ログで `Fixing legacy *_en_name columns` メッセージを確認
3. DBeaver でデータを確認
4. トラッキングカラムの値を確認

---

**作成者**: GitHub Copilot  
**レビュー**: 要確認  
**承認**: 未承認  
**ステータス**: テスト待ち
