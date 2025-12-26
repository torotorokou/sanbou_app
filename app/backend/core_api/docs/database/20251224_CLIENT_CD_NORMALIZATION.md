# client_cd 正規化処理実装レポート

**作成日**: 2025-12-24  
**対象マイグレーション**: `20251224_004_normalize_client_cd.py`

---

## 📋 概要

stg.shogun*flash_receive / stg.shogun_final_receive の client_cd について、先頭0除去の正規化処理を実装し、既存データも backfill しました。また、v_active*\* ビューで末尾Xを除去して表示するよう修正しました。

---

## 🔍 調査結果

### 原因

**CSVアップロード時に client_cd の正規化処理が実装されていなかった**

- [shogun_csv_repository.py](../app/infra/adapters/upload/shogun_csv_repository.py) でデータを保存しているが、client_cd の ltrim / regexp_replace 等の整形処理が一切行われていない
- そのため、元のCSVに `'001021'`, `'00169X'` のような先頭0付きのコードが含まれていると、そのまま保存されていた

### 実態

**2025-12-24 時点の調査結果**:

| テーブル名               | 総件数  | 先頭0残存件数 | 残存率 |
| ------------------------ | ------- | ------------- | ------ |
| stg.shogun_flash_receive | 117,005 | 7,302         | 6.2%   |
| stg.shogun_final_receive | 91,200  | 5,684         | 6.2%   |

**サンプル**:

- flash: `'001021'`, `'000804'`, `'001353'` 等（6桁数値、先頭0付き）
- final: `'00169X'`, `'00537X'`, `'00954X'` 等（6桁、末尾X、先頭0付き）

### 安全性確認

✅ **client_cd は UNIQUE制約・PK・インデックスなし**

- 正規化による重複リスクなし
- backfill UPDATE 安全

---

## 🛠️ 実装内容

### 1. 正規化関数 `stg.normalize_client_cd()`

**機能**:

- 前後空白除去
- 先頭0（半角）を除去
- ただし全て0の場合は `'0'` を返す（空値化しない）
- NULL 安全

**実装**:

```sql
CREATE OR REPLACE FUNCTION stg.normalize_client_cd(input_code text)
RETURNS text
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    trimmed text;
    result text;
BEGIN
    IF input_code IS NULL THEN
        RETURN NULL;
    END IF;

    trimmed := btrim(input_code);

    IF trimmed = '' THEN
        RETURN trimmed;
    END IF;

    result := regexp_replace(trimmed, '^0+', '', 'g');

    IF result = '' THEN
        RETURN '0';
    END IF;

    RETURN result;
END;
$$;
```

**変換例**:

- `'001021'` → `'1021'`
- `'00169X'` → `'169X'`
- `'0000'` → `'0'`
- `NULL` → `NULL`
- `' 001234 '` → `'1234'`

### 2. バックアップテーブル

**目的**: ロールバック可能にする

**作成されるテーブル**:

- `stg.shogun_flash_receive_client_cd_backup_YYYYMMDD_HHMMSS`
- `stg.shogun_final_receive_client_cd_backup_YYYYMMDD_HHMMSS`

**内容**: 更新対象のレコードの `id` と `old_client_cd` のみ保存

### 3. 既存データ backfill UPDATE

**対象**:

- `stg.shogun_flash_receive`: 先頭0付きの client_cd を持つ全レコード
- `stg.shogun_final_receive`: 先頭0付きの client_cd を持つ全レコード

**実行SQL**:

```sql
UPDATE stg.shogun_flash_receive
SET client_cd = stg.normalize_client_cd(client_cd)
WHERE btrim(client_cd) ~ '^0[0-9]';

UPDATE stg.shogun_final_receive
SET client_cd = stg.normalize_client_cd(client_cd)
WHERE btrim(client_cd) ~ '^0[0-9]';
```

**安全ガード**:

- トランザクション内で実行
- 事前にバックアップテーブル作成
- 更新件数を出力
- client_cd に UNIQUE制約なし確認済み

### 4. v*active*\* ビュー修正（末尾X除去表示）

**変更箇所**: `client_cd` カラムのみ

**Before**:

```sql
client_cd,
```

**After**:

```sql
regexp_replace(client_cd, '[Xx]$', '') AS client_cd,  -- 末尾X除去
```

**影響**:

- **表示のみ変更**（テーブルデータは変更なし）
- `'169X'` → `'169'` として view で見える
- JOIN キーとして使っている箇所への影響なし（元テーブルの client_cd は変更されていないため）

**対象ビュー**:

- `stg.v_active_shogun_flash_receive`
- `stg.v_active_shogun_final_receive`

---

## ✅ 検証方法

### 事前検証（マイグレーション前）

```sql
-- 先頭0残存件数の確認
SELECT
  'shogun_flash_receive' as table_name,
  COUNT(*) as leading_zero_count
FROM stg.shogun_flash_receive
WHERE btrim(client_cd) ~ '^0[0-9]'
UNION ALL
SELECT
  'shogun_final_receive' as table_name,
  COUNT(*) as leading_zero_count
FROM stg.shogun_final_receive
WHERE btrim(client_cd) ~ '^0[0-9]';
```

**期待結果**: flash: 7,302件、final: 5,684件

### 事後検証（マイグレーション後）

```sql
-- 先頭0残存件数の確認（0件のはず）
SELECT
  'shogun_flash_receive' as table_name,
  COUNT(*) as leading_zero_count
FROM stg.shogun_flash_receive
WHERE btrim(client_cd) ~ '^0[0-9]'
UNION ALL
SELECT
  'shogun_final_receive' as table_name,
  COUNT(*) as leading_zero_count
FROM stg.shogun_final_receive
WHERE btrim(client_cd) ~ '^0[0-9]';
```

**期待結果**: 両方とも 0件

```sql
-- view の末尾X除去確認
SELECT
  client_cd,
  COUNT(*) as count
FROM stg.v_active_shogun_final_receive
WHERE client_cd ~ 'X$'  -- 末尾にXがある（除去されていない）
GROUP BY client_cd
ORDER BY count DESC
LIMIT 10;
```

**期待結果**: 0件（末尾Xが除去されているため）

```sql
-- 正規化関数の動作確認
SELECT
  stg.normalize_client_cd('001021') as case1,  -- '1021'
  stg.normalize_client_cd('00169X') as case2,  -- '169X'
  stg.normalize_client_cd('0000') as case3,    -- '0'
  stg.normalize_client_cd(NULL) as case4,      -- NULL
  stg.normalize_client_cd(' 001234 ') as case5; -- '1234'
```

**期待結果**:
| case1 | case2 | case3 | case4 | case5 |
|-------|-------|-------|-------|-------|
| 1021 | 169X | 0 | NULL | 1234 |

---

## 🚀 適用手順

### ローカル開発環境 (local_dev)

```bash
# 1. マイグレーション実行
make al-up-env ENV=local_dev

# 2. 検証SQLで確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "${POSTGRES_DB:-postgres}"' < docs/database/verify_client_cd_normalization.sql
```

### ステージング環境 (vm_stg)

```bash
# 1. 事前バックアップ（念のため）
make backup ENV=vm_stg

# 2. マイグレーション実行
make al-up-env ENV=vm_stg

# 3. 検証SQLで確認
# VM内で実行:
docker compose -f docker/docker-compose.stg.yml -p vm_stg exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "${POSTGRES_DB:-postgres}"' < docs/database/verify_client_cd_normalization.sql
```

### 本番環境 (vm_prod)

⚠️ **必ず事前にバックアップ取得**

```bash
# 1. 事前バックアップ（必須）
make backup ENV=vm_prod

# 2. マイグレーション実行
make al-up-env ENV=vm_prod

# 3. 検証SQLで確認
# VM内で実行:
docker compose -f docker/docker-compose.prod.yml -p vm_prod exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "${POSTGRES_DB:-postgres}"' < docs/database/verify_client_cd_normalization.sql
```

---

## 🔄 ロールバック手順

### 自動ロールバック（ビューのみ元に戻す）

```bash
make al-down-env ENV=local_dev
```

⚠️ **注意**: テーブルデータは元に戻りません（安全のため）

### 手動ロールバック（データも元に戻す）

```sql
-- バックアップテーブルから元のデータをリストア
-- 例: 2025-12-24 15:30:45 にマイグレーションを実行した場合

-- shogun_flash_receive
UPDATE stg.shogun_flash_receive t
SET client_cd = b.old_client_cd
FROM stg.shogun_flash_receive_client_cd_backup_20251224_153045 b
WHERE t.id = b.id;

-- shogun_final_receive
UPDATE stg.shogun_final_receive t
SET client_cd = b.old_client_cd
FROM stg.shogun_final_receive_client_cd_backup_20251224_153045 b
WHERE t.id = b.id;

-- バックアップテーブルの削除（リストア完了後）
DROP TABLE stg.shogun_flash_receive_client_cd_backup_20251224_153045;
DROP TABLE stg.shogun_final_receive_client_cd_backup_20251224_153045;
```

---

## 📝 今後の対応

### 1. CSVアップロード時の正規化（推奨）

**方針**: 新規データは取込時に正規化する

**実装場所**: [shogun_csv_repository.py](../app/infra/adapters/upload/shogun_csv_repository.py)

**実装例**:

```python
# save_csv_by_type() メソッド内で、df_to_save の前処理として追加

# client_cd の正規化（先頭0除去）
if 'client_cd' in df_to_save.columns:
    df_to_save['client_cd'] = df_to_save['client_cd'].apply(
        lambda x: str(x).lstrip('0') if pd.notna(x) and str(x).strip() else ('0' if str(x).strip() == '' else str(x))
    )
    logger.info(f"[DEBUG REPO] client_cd を正規化しました（先頭0除去）")
```

### 2. 将来の拡張（任意）

- 全角数字 → 半角数字への変換（必要に応じて）
- 英字混じりコードへの対応（現状は数値コードのみ想定）

---

## 🎯 成果

✅ **目的達成**:

1. 先頭0除去処理の実装 → ✅ `stg.normalize_client_cd()` 関数作成
2. 既存データ backfill → ✅ 約13,000件を更新（安全ガード付き）
3. view で末尾X除去表示 → ✅ `v_active_*` ビュー修正

✅ **安全性確保**:

- UNIQUE制約なし確認済み
- バックアップテーブル作成済み
- ロールバック可能

✅ **再発防止**:

- 正規化関数により、今後の手動修正も統一ロジックで実施可能
- CSVアップロード時の正規化実装を推奨事項として明記

---

## 📚 関連ファイル

- マイグレーション: [migrations_v2/alembic/versions/20251224_004_normalize_client_cd.py](../migrations_v2/alembic/versions/20251224_004_normalize_client_cd.py)
- 検証SQL: [docs/database/verify_client_cd_normalization.sql](verify_client_cd_normalization.sql)
- データ取込処理: [app/infra/adapters/upload/shogun_csv_repository.py](../../app/infra/adapters/upload/shogun_csv_repository.py)

---

**作成者**: GitHub Copilot  
**レビュー**: -  
**承認**: -
