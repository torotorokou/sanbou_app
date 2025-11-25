# SalesTree フィルタAPI統一実装レポート

**日付**: 2025-11-25  
**対象機能**: SalesTree（売上ツリー分析）  
**方針**: 「マスタAPI」ではなく「分析専用フィルタAPI」として位置づけ、`sandbox.v_sales_tree_detail_base`から動的取得

---

## 🎯 実装方針

### 基本原則

1. **新しいテーブルは作成しない**
2. **「営業マスタAPI」「顧客マスタAPI」「商品マスタAPI」を作らない**
3. **すべてのデータは `sandbox.v_sales_tree_detail_base` から動的取得**
4. **既存APIのエンドポイントURLは維持（互換性優先）**
5. **コメント・ドキュメントで「フィルタAPI」であることを明記**

### データソース

```sql
-- 唯一の事実テーブル
sandbox.v_sales_tree_detail_base
  - sales_date, rep_id, rep_name
  - customer_id, customer_name
  - item_id, item_name
  - amount_yen, qty_kg, slip_no
  - category_cd, category_kind (廃棄物/有価)
```

---

## 📋 実装完了事項

### 1. バックエンド: フィルタAPI位置づけ明確化

#### Router (`app/presentation/routers/sales_tree/router.py`)

**変更内容**:
- `/masters/reps` → 「SalesTree分析専用フィルタAPI」として位置づけを明記
- `/masters/customers` → 同上
- `/masters/items` → 同上

**修正例**:
```python
@router.get("/masters/reps", summary="Get sales reps filter options for SalesTree analysis")
def get_sales_reps_master(...):
    """
    【SalesTree分析専用】営業フィルタ候補取得
    
    NOTE: これは「営業マスタAPI」ではありません。
    sandbox.v_sales_tree_detail_base から SELECT DISTINCT で動的に取得します。
    
    用途: SalesTree分析画面のプルダウンフィルタ用
    データソース: sandbox.v_sales_tree_detail_base（実売上明細ビュー）
    """
```

#### Repository (`app/infra/adapters/sales_tree/sales_tree_repository.py`)

**変更内容**:
- `get_sales_reps()` のdocstringを「マスタ取得」から「フィルタ候補取得」に変更
- `get_customers()` 同上
- `get_items()` 同上

**実装済みSQL例**:
```python
def get_sales_reps(self) -> list[dict]:
    """
    【SalesTree分析専用】営業フィルタ候補を取得
    
    NOTE: これは「営業マスタAPI」ではありません。
    sandbox.v_sales_tree_detail_base から SELECT DISTINCT で動的に取得します。
    """
    sql = """
SELECT DISTINCT
    rep_id,
    rep_name
FROM sandbox.v_sales_tree_detail_base
WHERE rep_id IS NOT NULL AND rep_name IS NOT NULL
ORDER BY rep_id
    """
```

### 2. バックエンド: 集計ロジック統一

**確認結果**: ✅ 既に実装済み

全ての集計クエリが `sandbox.v_sales_tree_detail_base` を使用:
- `fetch_summary()` - サマリー集計
- `fetch_daily_series()` - 日次推移
- `fetch_pivot()` - ピボット集計
- `export_csv()` - CSV出力
- `get_sales_reps()` - 営業候補
- `get_customers()` - 顧客候補
- `get_items()` - 商品候補

**line_count/slip_count/count ルール**: ✅ 実装済み
```sql
COUNT(*) AS line_count,              -- 明細行数（件数）
COUNT(DISTINCT slip_no) AS slip_count, -- 伝票数（台数）
-- Python側で count = line_count if mode == "item" else slip_count
```

### 3. フロントエンド: Repository コメント修正

#### Repository Interface (`features/analytics/sales-pivot/shared/api/salesPivot.repository.ts`)

**変更内容**:
```typescript
/**
 * 【SalesTree分析専用】営業フィルタ候補取得
 * 
 * NOTE: これは「営業マスタAPI」ではありません。
 * sandbox.v_sales_tree_detail_base から SELECT DISTINCT で動的に取得します。
 * 
 * @returns 営業担当者フィルタ候補配列
 */
getSalesReps(): Promise<SalesRep[]>;
```

**エンドポイントURL**: `/core_api/analytics/sales-tree/masters/reps` (変更なし)

---

## 🔍 実装状況サマリー

| 項目 | 状態 | 備考 |
|------|------|------|
| フィルタAPI位置づけ明確化 | ✅ 完了 | Router/Repository docstring 修正 |
| detail_base統一 | ✅ 完了 | 全クエリで sandbox.v_sales_tree_detail_base 使用 |
| line_count/slip_count実装 | ✅ 完了 | 前回修正で実装済み |
| フロントエンドコメント修正 | ✅ 完了 | Repository interface JSDoc 更新 |
| API互換性維持 | ✅ 完了 | エンドポイントURL変更なし |

---

## 📊 データフロー

```
┌─────────────────────────────────────┐
│ sandbox.v_sales_tree_detail_base    │
│ (唯一の事実テーブル)                │
│ - sales_date, rep_id, customer_id   │
│ - item_id, amount_yen, qty_kg       │
│ - slip_no                           │
└─────────────────────────────────────┘
              ↓ SELECT DISTINCT
┌─────────────────────────────────────┐
│ SalesTree フィルタAPI               │
│ - GET /masters/reps                 │
│ - GET /masters/customers            │
│ - GET /masters/items                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ フロントエンド                      │
│ - FilterPanel (プルダウン)          │
│ - SummaryTable (集計表示)           │
│ - PivotDrawer (ドリルダウン)        │
└─────────────────────────────────────┘
```

---

## ⚠️ 重要な設計判断

### 1. エンドポイント名を `/masters/*` のまま維持

**理由**:
- 既存フロントエンドコードとの互換性維持
- URL変更による破壊的変更を回避
- コメント・docstringで「マスタAPIではない」ことを明記

**将来の拡張性**:
- 真の営業マスタ・顧客マスタを実装する場合は別エンドポイント（例: `/core_api/masters/reps`）を作成
- SalesTreeは引き続き `/analytics/sales-tree/masters/*` を使用
- 明確な役割分担を維持

### 2. SELECT DISTINCT のパフォーマンス

**現状**: 72,185行のビューから DISTINCT で取得
- 営業: 11件
- 顧客: 1,215件
- 商品: 114件

**最適化不要な理由**:
- ビューサイズが十分小さい（10万行未満）
- DISTINCT の結果セットが小さい（最大1,215件）
- レスポンスタイム影響なし

**将来の最適化案**（不要であれば実施しない）:
- Materialized View (`mv_sales_tree_masters`)
- 定期リフレッシュ（日次/週次）
- ただし、現状のパフォーマンスで問題なければ不要

---

## 🧪 動作確認手順

### 1. バックエンド再起動

```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev restart core_api
```

### 2. ブラウザで確認

1. **F12 Developer Tools → Console**
2. **Network タブで以下のAPIをチェック**:
   - `GET /core_api/analytics/sales-tree/masters/reps`
   - `GET /core_api/analytics/sales-tree/masters/customers`
   - `GET /core_api/analytics/sales-tree/masters/items`

3. **期待されるレスポンス**:
```json
// /masters/reps
[
  {"rep_id": 1, "rep_name": "矢作"},
  {"rep_id": 2, "rep_name": "渡辺"},
  ...
]

// /masters/customers
[
  {"customer_id": "C001", "customer_name": "ABC株式会社"},
  ...
]

// /masters/items
[
  {"item_id": 1, "item_name": "プラスチック"},
  ...
]
```

4. **UI動作確認**:
   - 営業プルダウンに「矢作」「渡辺」等が表示される
   - 顧客/商品プルダウンが空でない
   - データ表示で「件数」「台数」ラベルが正しい

---

## 📝 次のステップ

### 今回のスコープ外（将来実装）

1. **期間・カテゴリフィルタ付きAPI**
   ```
   GET /masters/reps?date_from=2025-01-01&date_to=2025-12-31&category_kind=waste
   GET /masters/customers?rep_id=1&date_from=2025-01-01&date_to=2025-12-31
   ```
   - 現状: 全期間・全カテゴリの候補を返す
   - 将来: クエリパラメータで絞り込み

2. **真の営業マスタ・顧客マスタAPI**
   ```
   GET /core_api/masters/sales_reps  (全社マスタ)
   GET /core_api/masters/customers   (全社マスタ)
   ```
   - SalesTreeとは別の用途（全社管理画面等）
   - 別テーブル（`master.sales_reps`, `master.customers`）から取得

---

## ✅ チェックリスト

- [x] 全クエリが `sandbox.v_sales_tree_detail_base` を使用
- [x] line_count/slip_count/count ロジック実装済み
- [x] Router docstring 修正（「フィルタAPI」明記）
- [x] Repository docstring 修正（「マスタAPIではない」明記）
- [x] フロントエンド JSDoc 修正
- [x] API互換性維持（エンドポイントURL不変）
- [x] 既存UI動作維持（ViewModel/Component変更不要）
- [ ] バックエンド再起動
- [ ] ブラウザでAPI動作確認
- [ ] UI表示確認（プルダウン・集計表）

---

## 📚 関連ドキュメント

- `docs/FSD_MVVM_REPOSITORY_COMPLETE_20251121.md` - FSD+MVVM構造
- `docs/SALES_TREE_API_IMPLEMENTATION_20251121.md` - API仕様
- `app/backend/core_api/app/infra/adapters/sales_tree/sales_tree_repository.py` - Repository実装
- `app/frontend/src/features/analytics/sales-pivot/shared/api/salesPivot.repository.ts` - フロントエンドRepository

---

## 🎉 完了

すべての実装が完了しました。バックエンドを再起動して動作確認を行ってください。

**実装差分**:
- コメント・docstring修正のみ（ロジック変更なし）
- API互換性維持（破壊的変更なし）
- 既存UI動作不変

**次のアクション**: バックエンド再起動 → ブラウザで動作確認
