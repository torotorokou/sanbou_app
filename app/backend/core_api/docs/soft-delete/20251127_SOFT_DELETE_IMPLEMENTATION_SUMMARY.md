# 論理削除（Soft Delete）対応リファクタリング - 実装サマリー

## 📌 作成されたファイル一覧

### Alembic マイグレーションファイル（3つ）

1. **`20251120_160000000_create_active_shogun_views.py`**

   - アクティブ行専用ビュー（stg.active\_\*）を6つ作成
   - 論理削除済み行を自動的に除外するフィルタビュー

2. **`20251120_170000000_update_mart_views_for_soft_delete.py`**

   - mart.v*receive_daily の更新（active*\* ビュー使用）
   - mart.v_shogun_flash_receive_daily の更新（is_deleted フィルタ追加）
   - mart.v_shogun_final_receive_daily の更新（is_deleted フィルタ追加）

3. **`20251120_180000000_optimize_is_deleted_indexes.py`**
   - 部分インデックス（WHERE is_deleted = false）を6つ作成
   - NULL データのクリーンアップ処理

### テスト・ドキュメント類（4つ）

4. **`scripts/sql/test_is_deleted_regression.sql`**

   - リグレッションテスト用SQL（9つのテストケース）
   - 論理削除状況の確認、集計結果の比較、インデックス使用確認など

5. **`scripts/apply_soft_delete_refactoring.sh`**

   - 自動実行スクリプト（マイグレーション適用～テスト実行まで）
   - 色付きログ出力、エラーハンドリング付き

6. **`docs/SOFT_DELETE_REFACTORING_20251120.md`**

   - 詳細実装レポート（Before/After 比較、性能評価、運用手順）

7. **`docs/SOFT_DELETE_QUICKSTART.md`**
   - クイックスタートガイド（実行手順、検証チェックリスト）

---

## 🎯 主要な変更点

### 1. アクティブ行専用ビューの作成

```sql
CREATE VIEW stg.active_shogun_flash_receive AS
SELECT * FROM stg.shogun_flash_receive WHERE is_deleted = false;
```

**対象テーブル**: 6つ（receive/yard/shipment × flash/final）

### 2. mart ビューの更新

#### Before:

```sql
FROM stg.shogun_flash_receive s
WHERE s.slip_date IS NOT NULL
```

#### After:

```sql
FROM stg.active_shogun_flash_receive s
WHERE s.slip_date IS NOT NULL
  AND s.is_deleted = false  -- 明示的フィルタ（防御的プログラミング）
```

### 3. 部分インデックスの追加

```sql
CREATE INDEX CONCURRENTLY idx_shogun_flash_receive_active
ON stg.shogun_flash_receive (slip_date, upload_file_id)
WHERE is_deleted = false;
```

**メリット**:

- インデックスサイズが削減（論理削除行を含まない）
- クエリ性能の向上（WHERE is_deleted = false の条件に最適化）

---

## 📊 変更影響範囲

### 変更されたビュー/マテビュー

| オブジェクト                        | 変更内容                   | リフレッシュ要否 |
| ----------------------------------- | -------------------------- | ---------------- |
| `stg.active_shogun_flash_receive`   | ✅ 新規作成                | -                |
| `stg.active_shogun_final_receive`   | ✅ 新規作成                | -                |
| `stg.active_shogun_*_yard` (×2)     | ✅ 新規作成                | -                |
| `stg.active_shogun_*_shipment` (×2) | ✅ 新規作成                | -                |
| `mart.v_receive_daily`              | ✅ 更新（active\_\* 使用） | -                |
| `mart.v_shogun_flash_receive_daily` | ✅ 更新（フィルタ追加）    | -                |
| `mart.v_shogun_final_receive_daily` | ✅ 更新（フィルタ追加）    | -                |
| `mart.mv_target_card_per_day`       | ⚠️ 間接影響                | ✅ 必須          |
| `mart.mv_inb5y_week_profile_min`    | ⚠️ 間接影響                | ✅ 必須          |
| `mart.mv_inb_avg5y_day_biz`         | ⚠️ 間接影響                | ✅ 必須          |
| `mart.mv_inb_avg5y_weeksum_biz`     | ⚠️ 間接影響                | ✅ 必須          |
| `mart.mv_inb_avg5y_day_scope`       | ⚠️ 間接影響                | ✅ 必須          |

### Python コード

| ファイル              | 変更要否 | 理由                               |
| --------------------- | -------- | ---------------------------------- |
| `database/router.py`  | ❌ 不要  | すでに is_deleted フィルタ適用済み |
| `ShogunCsvRepository` | ❌ 不要  | INSERT のみ、SELECT なし           |

---

## 🚀 実行コマンド（クイックリファレンス）

### 自動実行（推奨）

```bash
chmod +x scripts/apply_soft_delete_refactoring.sh
./scripts/apply_soft_delete_refactoring.sh
```

### 手動実行

```bash
# 1. マイグレーション適用
make al-up

# 2. MVリフレッシュ
make refresh-mv

# 3. 統計更新
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "ANALYZE stg.shogun_flash_receive;"

# 4. テスト実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev < scripts/sql/test_is_deleted_regression.sql
```

---

## ✅ 検証チェックリスト

### マイグレーション適用確認

```bash
make al-cur
# Expected: 20251120_180000000 以降
```

### ビュー存在確認

```sql
SELECT schemaname, viewname
FROM pg_views
WHERE schemaname = 'stg' AND viewname LIKE 'active_%';
-- Expected: 6 rows
```

### インデックス存在確認

```sql
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'stg' AND indexname LIKE '%_active';
-- Expected: 6 rows
```

### 論理削除率確認

```sql
SELECT
    'shogun_flash_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_receive;
```

---

## 🔄 ロールバック

```bash
# 3回実行して3つのリビジョンを戻す
make al-down
make al-down
make al-down

# または一括ロールバック
docker compose exec core_api alembic downgrade 20251120_150000000
```

---

## 📈 期待される効果

### データ整合性

- ✅ 論理削除済み行が自動的に集計から除外される
- ✅ is*deleted 条件の書き忘れを防止（active*\* ビュー）
- ✅ 二重防御（active\_\* ビュー + 明示的 WHERE 句）

### 性能

- ✅ 部分インデックスによるクエリ高速化
- ✅ インデックスサイズの削減（論理削除行を含まない）
- ✅ 論理削除率が高くなっても性能維持

### 保守性

- ✅ コードの可読性向上（active\_\* ビューで意図が明確）
- ✅ 統一的なフィルタ適用方法
- ✅ 将来の機能追加が容易

---

## 📝 次のアクション

### 開発環境

1. ✅ マイグレーション適用
2. ✅ リグレッションテスト実行
3. ✅ API 動作確認

### ステージング環境

1. ⏳ マイグレーション適用
2. ⏳ 性能測定（EXPLAIN ANALYZE）
3. ⏳ 統合テスト実行

### 本番環境

1. ⏳ メンテナンス時間を確保
2. ⏳ バックアップ取得
3. ⏳ マイグレーション適用
4. ⏳ 監視・モニタリング

---

## 🔗 関連リンク

- **詳細レポート**: `docs/SOFT_DELETE_REFACTORING_20251120.md`
- **クイックスタート**: `docs/SOFT_DELETE_QUICKSTART.md`
- **テストSQL**: `scripts/sql/test_is_deleted_regression.sql`
- **実行スクリプト**: `scripts/apply_soft_delete_refactoring.sh`

---

**作成日**: 2025-11-20  
**担当**: GitHub Copilot (Claude Sonnet 4.5)  
**ステータス**: ✅ 実装完了（開発環境）
