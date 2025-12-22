# 予約データ契約チェック：固定客台数 vs 固定客数（社数）

**作成日**: 2025-12-19  
**目的**: mart.v_reserve_daily_for_forecastから固定客数（社数/人数）が取得可能か、および固定客台数との概念的相違を検証

## 1. View定義確認

### mart.v_reserve_daily_for_forecast のスキーマ

| カラム名 | 型 | 説明 |
|---------|-----|------|
| date | date | 予約日 |
| reserve_trucks | bigint | 予約台数（総計） |
| reserve_fixed_trucks | bigint | **固定客の予約台数（総計）** |
| reserve_fixed_ratio | numeric | 固定客比率（固定客台数/総台数） |
| source | text | データソース（customer_agg または manual） |

### View定義（SQL）

```sql
WITH customer_agg AS (
    SELECT 
        reserve_customer_daily.reserve_date AS date,
        sum(reserve_customer_daily.planned_trucks) AS reserve_trucks,
        sum(
            CASE
                WHEN reserve_customer_daily.is_fixed_customer 
                THEN reserve_customer_daily.planned_trucks
                ELSE 0
            END
        ) AS reserve_fixed_trucks,
        'customer_agg'::text AS source
    FROM stg.reserve_customer_daily
    GROUP BY reserve_customer_daily.reserve_date
), manual_data AS (
    ...
), combined AS (
    ...
)
SELECT 
    date,
    reserve_trucks,
    reserve_fixed_trucks,
    CASE
        WHEN reserve_trucks > 0 
        THEN round(reserve_fixed_trucks::numeric / reserve_trucks::numeric, 4)
        ELSE 0::numeric
    END AS reserve_fixed_ratio,
    source
FROM combined
ORDER BY date;
```

## 2. 固定客数（社数）算出可能性の検証

### 元データ（stg.reserve_customer_daily）のスキーマ

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | bigint | PK |
| reserve_date | date | 予約日 |
| **customer_cd** | text | **顧客コード**（NOT NULL） |
| customer_name | text | 顧客名 |
| planned_trucks | integer | 予定台数 |
| **is_fixed_customer** | boolean | **固定客フラグ** |
| note | text | 備考 |

### 固定客数の算出（検証クエリ）

```sql
SELECT 
    reserve_date,
    COUNT(DISTINCT CASE WHEN is_fixed_customer THEN customer_cd END) as fixed_customer_count,
    SUM(CASE WHEN is_fixed_customer THEN planned_trucks ELSE 0 END) as fixed_trucks
FROM stg.reserve_customer_daily
WHERE reserve_date = '2025-10-31'
GROUP BY reserve_date;
```

**結果**:
| reserve_date | fixed_customer_count | fixed_trucks |
|--------------|----------------------|--------------|
| 2025-10-31 | **26** | **42** |

## 3. 結論

### ✅ 固定客数（社数）は算出可能

**根拠**:
- stg.reserve_customer_dailyは**顧客粒度**（customer_cd）でデータを保持
- is_fixed_customerフラグで固定客を識別可能
- `COUNT(DISTINCT CASE WHEN is_fixed_customer THEN customer_cd END)`で固定客数（社数）を計算可能

### ⚠️ 現状のView定義の問題

**mart.v_reserve_daily_for_forecastの限界**:
1. **固定客台数（fixed_trucks）**のみ提供、**固定客数（社数）**は提供していない
2. customer_cdを保持していないため、日次集計ビューから固定客数を逆算**不可能**
3. reserve_fixed_ratioは「固定客台数比率」であり、「固定客企業比率」ではない

### ❌ 命名の誤解を生む可能性

**潜在的な混同**:
- `reserve_fixed_trucks`は固定客の**台数**を意味するが、名称だけでは「人数」と誤認する余地あり
- 旧版CSVでは固定客列が1企業1行のBoolean → `.mean()`で**企業比率**を計算
- DBビューでは固定客列が台数の集計値 → `/`で**台数比率**を計算
- **両者は異なる概念**だが、同じ`fixed_ratio`特徴量名を使用

## 4. 概念整理

| 概念 | 説明 | 算出方法 | 現状の取得可否 |
|------|------|----------|---------------|
| **固定客台数** | 固定客企業の予約台数合計 | `SUM(CASE WHEN is_fixed_customer THEN planned_trucks END)` | ✅ View提供 |
| **固定客数（社数）** | 固定客企業の社数 | `COUNT(DISTINCT CASE WHEN is_fixed_customer THEN customer_cd END)` | ❌ View未提供（元テーブルから算出可） |
| **総企業数** | その日の予約企業総数 | `COUNT(DISTINCT customer_cd)` | ❌ View未提供（元テーブルから算出可） |
| **固定客台数比率** | 固定客台数 / 総台数 | `fixed_trucks / reserve_trucks` | ✅ View提供（reserve_fixed_ratio） |
| **固定客企業比率** | 固定客社数 / 総企業数 | `fixed_customer_count / total_customer_count` | ❌ View未提供 |

## 5. 旧版CSVとDBの根本的差異

### 旧版CSV（yoyaku_data.csv）の実態

```csv
予約日,予約得意先名,固定客,台数
2025/10/31,ミヤ産興,TRUE,1
2025/10/31,谷津商会,TRUE,1
2025/10/31,メタウォーター（オネスト）,FALSE,4
```

- **1行 = 1企業**
- 固定客列 = Boolean（TRUE/FALSE）
- 台数列 = その企業の台数

### preprocess_reserve()関数の処理

```python
# L278: 固定客Booleanを1/0に変換
dd[cmap["fixed"]] = dd[cmap["fixed"]].astype(str).str.lower().isin(["1","true","yes","固定","固定客"]).astype(int)

# L281-283: 日次グループ集計
out = pd.DataFrame({
    "reserve_count": grp.size().astype(float),           # 予約企業数（行数）
    "reserve_sum": grp[cmap["count"]].sum(),             # 予約台数合計
    "fixed_ratio": grp[cmap["fixed"]].mean()              # 固定客フラグの平均 = 固定客企業数 / 総企業数
})
```

**重要**: `.mean()`は**固定客企業数 / 総企業数**を返す（企業比率）

### DB環境の処理

```python
# reserve_exporter.py L48
SELECT 
    date AS "予約日",
    reserve_trucks AS "台数",
    reserve_fixed_trucks AS "固定客"  -- ← これは固定客"台数"
FROM mart.v_reserve_daily_for_forecast
```

- "固定客"列 = 固定客**台数**（42台）
- DBビューのreserve_fixed_ratio = 固定客台数 / 総台数 = **台数比率**

## 6. 精度劣化への影響

### 実測データ（2025-10-31の例）

| 項目 | 旧版CSV | DB環境 | 差異 |
|------|---------|--------|------|
| 予約企業数 | 62社 | - | - |
| 固定客社数 | 26社 | 26社（算出可） | 0 |
| 総台数 | 87台 | 87台 | 0 |
| 固定客台数 | 42台 | 42台 | 0 |
| **固定客"比率"特徴量** | **26/62 = 0.419（企業比率）** | **42/87 = 0.483（台数比率）** | **+0.064（+15%）** |

### Stage 2モデルへの影響

- Stage 2（集計予測）は`fixed_ratio`を特徴量として使用
- 企業比率（0.419）と台数比率（0.483）は**異なる概念**
- 平均差異: 固定客台数 - 固定客社数 = 約+16台/日（CSV集計の誤り確認済）
- 日次で平均+16台の差異 → Stage 2の予測精度に直接影響
- R2_sum_only劣化（0.466 → 0.069、-85%）の主因と推定

## 7. 推奨事項

### A. 短期対応（後方互換性維持）

1. **固定客数（社数）を別特徴量として追加**
   - mart.v_reserve_daily_featuresを新設（既存Viewは維持）
   - 固定客台数（fixed_trucks）と固定客社数（fixed_customer_count）を両方提供

2. **命名規則の明確化**
   - `reserve_fixed_trucks`: 固定客の予約台数（現行維持）
   - `reserve_fixed_customer_count`: 固定客の社数（新規追加）
   - `fixed_trucks_ratio`: 固定客台数比率（= reserve_fixed_ratio、現行維持）
   - `fixed_customer_ratio`: 固定客社数比率（新規追加）

### B. 長期対応（設計改善）

1. **粒度別ビューの明確な分離**
   - `v_reserve_daily_for_forecast`: 日次集計（台数のみ、現行維持）
   - `v_reserve_daily_features`: 日次集計（台数 + 社数、新規）
   - `v_reserve_customer_daily`: 顧客粒度（詳細分析用、既存）

2. **特徴量生成ロジックの統一**
   - 旧版CSVの`.mean()`ロジックは企業比率を計算（意図的設計）
   - DB環境で同等の企業比率を得るには、固定客社数を別途取得する必要あり
   - 両方の比率（台数比率 + 企業比率）を特徴量として提供し、モデルに選択させる

## 8. 次のアクション

1. ✅ 固定客数算出可能性の確認（完了）
2. ⏳ 旧版vs現状の予約特徴量生成の再帰的差分抽出
3. ⏳ 固定客社数を追加する最小差分修正の実装
4. ⏳ 動的比較（同一入力での特徴量CSV出力）
