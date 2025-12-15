# MV削除候補リスト

**作成日**: 2025-12-11  
**作成者**: GitHub Copilot  
**目的**: 未使用または重複するマテリアライズドビュー/ビューの削除候補を特定し、安全な削除手順を記録する

---

## 削除候補サマリー

| オブジェクト名 | 種別 | 状態 | 削除優先度 | 理由 |
|--------------|------|------|----------|------|
| `mart.mv_sales_tree_daily` | MV | 未使用 | **HIGH** | v_sales_tree_detail_baseへ移行済み。Repositoryで参照なし。v_sales_tree_dailyのラッパー元だが、今はv_sales_tree_dailyも移行済み |
| `mart.v_sales_tree_daily` | VIEW | ⚠️ 依存あり | **LOW** | v_customer_sales_dailyが依存。削除には依存VIEW の先行リファクタが必要 |

---

## 詳細分析

### 1. `mart.mv_sales_tree_daily` (Materialized View)

**作成マイグレーション**: `20251125_120000000_create_mv_sales_tree_daily_with_indexes.py`  
**作成日**: 2025-11-25  
**サイズ**: 8192 bytes (ほぼ空)  
**インデックス**:
- `idx_mv_sales_tree_daily_composite` ON (sales_date, rep_id, customer_id, item_id)
- `idx_mv_sales_tree_daily_slip` ON (sales_date, customer_id, slip_no)

**使用状況調査結果**:
```bash
# Pythonコードでの参照確認
grep -r "mv_sales_tree_daily" app/backend/core_api/app/infra/adapters/
# → 結果: なし

# sales_tree_repository.py の参照先確認
# → 全てのクエリが mart.v_sales_tree_detail_base を参照
# → mv_sales_tree_daily への参照は0件
```

**依存関係**: なし（ラッパーVIEW `v_sales_tree_daily` が存在するが、これも未使用）

**削除可否**: ✅ **削除可能**
- Repositoryで参照されていない
- v_sales_tree_detail_base への移行完了（20251201_110000000マイグレーション）
- データサイズも小さく、削除によるリスクは低い

**削除手順**:
1. 依存VIEWを先に削除（`v_sales_tree_daily`）
2. インデックスを削除（MVと一緒に自動削除されるが、明示的に記述推奨）
3. MVを削除

```sql
-- Step 1: Drop dependent VIEW
DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;

-- Step 2: Drop Materialized View
DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily CASCADE;
```

---

### 2. `mart.v_sales_tree_daily` (VIEW)

**作成マイグレーション**:
- 初回: `20251125_150000000_create_mart_sales_tree_views_v_sales_.py` (mv_sales_tree_dailyのラッパーとして作成)
- リファクタ: `20251201_110000000_refactor_v_sales_tree_daily_use_detail_base.py` (v_sales_tree_detail_baseを参照するように変更)

**定義**:
```sql
-- 現在の定義（20251201以降）
CREATE VIEW mart.v_sales_tree_daily AS
SELECT * FROM mart.v_sales_tree_detail_base;

-- 旧定義（20251125-20251201）
CREATE VIEW mart.v_sales_tree_daily AS
SELECT * FROM mart.mv_sales_tree_daily;
```

**使用状況調査結果**:
```bash
# Pythonコードでの参照確認
grep -r "v_sales_tree_daily" app/backend/core_api/app/infra/adapters/sales_tree/
# → 結果: なし

# SalesTreeRepository 実装確認
# → 全クエリが mart.v_sales_tree_detail_base を直接参照
# → v_sales_tree_daily への参照は0件
```

**依存関係**: `mart.v_customer_sales_daily` が参照している可能性を確認

```bash
# v_customer_sales_daily の定義確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\d+ mart.v_customer_sales_daily"
```

**削除可否**: ❌ **削除不可**
- `mart.v_customer_sales_daily` が `v_sales_tree_daily` を参照している
- `v_customer_sales_daily` の定義: `FROM mart.v_sales_tree_daily v`

**推奨アクション**: **削除せず維持**
- 現在の定義（`SELECT * FROM mart.v_sales_tree_detail_base`）は冗長だが、依存VIEWのため削除不可
- v_customer_sales_daily が直接 v_sales_tree_detail_base を参照するように変更すれば削除可能（別タスク）

**削除手順** (依存関係なしの場合):
```sql
-- ❌ 実行不可（v_customer_sales_daily が依存）
DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
```

---

## 削除実行計画

### Phase 1: 削除候補の最終確認（完了）

- [x] `mart.v_customer_sales_daily` の定義確認 → `v_sales_tree_daily` への依存を確認
- [x] `v_sales_tree_daily` への依存確認 → 依存ありのため削除不可
- [x] フロントエンドコード確認 → 不要（Pythonコードで参照なし）

**結論**: `v_sales_tree_daily` は削除不可（依存VIEWあり）。`mv_sales_tree_daily` のみ削除可能。

### Phase 2: 削除実施（mv_sales_tree_daily のみ）

1. **mv_sales_tree_daily の削除**
   ```bash
   # Alembicマイグレーション作成
   docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
     alembic -c /backend/migrations/alembic.ini revision --autogenerate \
     -m "drop unused mv_sales_tree_daily materialized view"
   
   # マイグレーション内容（手動編集）
   def upgrade() -> None:
       op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily CASCADE;")
   
   def downgrade() -> None:
       # 復元は不要（未使用のため）
       pass
   ```

2. **マイグレーション適用**
   ```bash
   docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
     alembic -c /backend/migrations/alembic.ini upgrade head
   ```

### Phase 3: 後処理

- [ ] MaterializedViewRefresher.MV_MAPPINGS から参照削除（既になし）
- [ ] 関連ドキュメント更新
- [ ] 調査レポート更新

---

## 削除による影響範囲

### ✅ 影響なし
- **Pythonコード**: Repository/UseCase層で参照なし
- **自動更新**: MaterializedViewRefresher.MV_MAPPINGS に未登録
- **API**: エンドポイントで直接参照なし

### ⚠️ 影響あり（削除不可）
- **mart.v_customer_sales_daily**: `v_sales_tree_daily` を参照（`FROM mart.v_sales_tree_daily v`）
  - 削除するには、v_customer_sales_daily を先に v_sales_tree_detail_base 参照に変更する必要あり

### 🚫 削除不可
- `v_sales_tree_detail_base` - **アクティブ使用中** (SalesTreeRepository の全クエリで参照)
- `v_sales_tree_daily` - **依存VIEWあり** (v_customer_sales_daily が参照)

---

## 参考情報

### 現在のアクティブなMV/VIEW

**Materialized Views (アクティブ):**
1. ✅ `mart.mv_receive_daily` (224 KB) - CSV upload時に自動更新
2. ✅ `mart.mv_target_card_per_day` (240 KB) - CSV upload時に自動更新

**Views (アクティブ):**
1. ✅ `mart.v_sales_tree_detail_base` - SalesTreeRepository で使用中
2. ✅ `mart.v_customer_sales_daily` - 使用状況要確認
3. ✅ `mart.v_daily_target_with_calendar` - mv_target_card_per_day が依存

**Materialized Views (削除候補):**
1. ⚠️ `mart.mv_sales_tree_daily` (8192 bytes) - 未使用

**Views (削除不可 - 依存あり):**
1. ⚠️ `mart.v_sales_tree_daily` - v_customer_sales_daily が依存（削除には依存VIEW先行リファクタ必要）

---

## 履歴

| 日付 | 変更内容 | 実施者 |
|------|---------|--------|
| 2025-12-11 | 初版作成 | GitHub Copilot |
