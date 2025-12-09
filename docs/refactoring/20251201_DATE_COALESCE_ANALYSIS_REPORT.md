# Date系カラムの使用状況レポート

**作成日**: 2025-12-01  
**対象**: sanbou_app プロジェクト全体

---

## 📊 エグゼクティブサマリー

### ✅ 既に対応済み
- **COALESCE(sales_date, slip_date)** → **slip_date** への変更完了
  - 対象: sales-tree関連の全VIEW (mart, sandbox)
  - マイグレーション: `20251201_160000000_use_slip_date_instead_of_coalesce.py`

### ⚠️ 要確認・検討項目
1. **payment_date** (支払日) の活用可能性
2. **テストSQL** での COALESCE パターン (低優先度)
3. **他のスキーマ** での日付カラムの一貫性

---

## 🔍 詳細分析

### 1. 主要テーブルの日付カラム構成

#### stg.shogun_final_receive / stg.shogun_flash_receive
| カラム名 | 型 | NULL許容 | 用途 | 実データ状況 |
|---------|-----|---------|------|------------|
| **slip_date** | DATE | NO | 伝票日付（基準日） | **100% 存在** |
| **sales_date** | DATE | YES | 売上日付 | **100% 存在** |
| **payment_date** | DATE | YES | 支払日付 | **100% 存在** |

**重要な発見**:
```
総行数: 86,124
- sales_date と slip_date の両方が存在: 86,124 (100%)
- 両者が異なる行: 1,070 (1.24%)
- payment_date も 100% 存在
```

**考察**:
- sales_date は slip_date から算出されたフィールドの可能性が高い
- 約1.2%のケースで sales_date ≠ slip_date
- payment_date も完全に入力されており、活用可能

---

### 2. COALESCE パターンの現状

#### A. ✅ 対応済み: sales_date + slip_date

**対象VIEW** (すべて slip_date ベースに変更済み):
- `mart.v_sales_tree_detail_base`
- `mart.mv_sales_tree_daily` (MATERIALIZED VIEW)
- `mart.v_sales_tree_daily`
- `sandbox.v_sales_tree_detail_base`

**変更内容**:
```sql
-- 変更前
SELECT COALESCE(sales_date, slip_date) AS sales_date
WHERE COALESCE(sales_date, slip_date) IS NOT NULL

-- 変更後
SELECT slip_date AS sales_date
WHERE slip_date IS NOT NULL
```

---

#### B. 🔍 要検討: 他の日付COALESCEパターン

##### パターン1: テストSQL (低優先度)

**ファイル**: `scripts/sql/test_is_deleted_regression.sql`

```sql
-- Line 118
COALESCE(u.ddate, f.ddate) AS slip_date,

-- Line 127
WHERE COALESCE(u.ddate, f.ddate) >= CURRENT_DATE - INTERVAL '30 days'
```

**分析**:
- これはテスト用SQLであり、FULL OUTER JOIN の結果を統合するため
- 実運用コードではない
- **対応不要** (テストロジックとして妥当)

---

### 3. 日付カラムの完全一覧

#### stg スキーマ (ステージング層)

| テーブル | 日付カラム | 型 | 備考 |
|---------|-----------|-----|------|
| shogun_final_receive | slip_date, sales_date, payment_date | DATE | 受入確定データ |
| shogun_flash_receive | slip_date, sales_date, payment_date | DATE | 受入速報データ |
| shogun_final_shipment | slip_date | DATE | 出荷確定データ |
| shogun_flash_shipment | slip_date | DATE | 出荷速報データ |
| shogun_final_yard | slip_date | DATE | ヤード確定データ |
| shogun_flash_yard | slip_date | DATE | ヤード速報データ |
| receive_king_final | invoice_date, param_start_date, param_end_date | VARCHAR | KING受入データ |

#### mart スキーマ (マート層)

| VIEW/Table | 日付カラム | 型 | データソース |
|-----------|-----------|-----|------------|
| v_sales_tree_detail_base | **sales_date** | DATE | slip_date を投影 ✅ |
| v_sales_tree_daily | sales_date | DATE | detail_base 経由 ✅ |
| mv_sales_tree_daily | sales_date | DATE | slip_date を投影 ✅ |
| v_receive_daily | ddate | DATE | 日次集計 |
| v_receive_weekly | week_start_date, week_end_date | DATE | 週次集計 |
| v_receive_monthly | month_date | DATE | 月次集計 |

#### ref スキーマ (参照マスタ)

| テーブル | 日付カラム | 用途 |
|---------|-----------|------|
| calendar_day | ddate | カレンダーマスタ |
| closure_periods | start_date, end_date | 締め期間 |
| holiday_jp | hdate | 日本の祝日 |

---

### 4. payment_date の活用可能性

**現状**:
- stg.shogun_*_receive テーブルに存在
- 100% のデータで値が入っている
- 範囲: 2024-05-01 ～ 2025-11-25

**活用シナリオ**:
1. **支払ベースの集計**: 現在は slip_date (伝票日) ベースだが、支払日ベースの分析も可能
2. **キャッシュフロー分析**: 入金タイミングの把握
3. **売掛管理**: slip_date と payment_date の差分分析

**提案**:
```sql
-- 例: 支払日ベースのVIEWを追加
CREATE VIEW mart.v_sales_tree_by_payment_date AS
SELECT
    payment_date AS base_date,  -- payment_date を基準に
    ...
FROM stg.v_active_shogun_final_receive
WHERE payment_date IS NOT NULL;
```

---

### 5. 時刻系カラムの状況

#### stg.receive_king_final

| カラム | 型 | 用途 |
|-------|-----|------|
| weighing_time_gross | VARCHAR | 計量時刻（総重量） |
| weighing_time_tare | VARCHAR | 計量時刻（風袋） |

**分析**:
- 現在 VARCHAR 型で保存
- COALESCE パターンは未使用
- 時刻データとしての活用は限定的

---

## 📋 推奨アクション

### 優先度: 高 ✅
1. **完了**: sales_date → slip_date 統一化
   - すべての sales-tree VIEW で対応済み

### 優先度: 中 🔍
2. **検討**: payment_date の活用
   - 新しいVIEWやレポートでの利用を検討
   - 支払日ベースの分析ニーズを確認

### 優先度: 低 ℹ️
3. **保留**: テストSQLのCOALESCE
   - 現状維持（テストロジックとして妥当）
4. **保留**: KING weighing_time の型変換
   - 実務での利用頻度を確認してから判断

---

## 🎯 結論

### 現在の状態
- **COALESCE(sales_date, slip_date)** パターンは **完全に解消**
- すべての sales-tree 関連VIEWで **slip_date** を基準日として統一
- データの一貫性とクエリパフォーマンスが向上

### 残存する日付カラム
- **payment_date**: 活用可能（新規VIEW作成の候補）
- **invoice_date** (KING): 別システムのため現状維持
- **weighing_time**: VARCHAR型のまま（変換の必要性低）

### 追加対応の必要性
**なし** - 当初の目的 (COALESCE削減・日付基準統一) は達成済み

---

## 📝 変更履歴

| 日付 | マイグレーション | 変更内容 |
|------|-----------------|---------|
| 2025-12-01 | 20251201_150000000 | stg.shogun_final_receive → stg.v_active_shogun_final_receive |
| 2025-12-01 | 20251201_160000000 | COALESCE(sales_date, slip_date) → slip_date |

---

**レポート終了**
