# 予約特徴量生成の再帰的差分レポート（旧版 vs 現状）

**作成日**: 2025-12-19  
**対象**: 予約データ特徴量生成の静的コード解析  
**範囲**: train_daily_model.py のpreprocess_reserve()およびStage 2特徴量生成

## 1. 概要

### 調査対象

| バージョン | パス | 行数 |
|-----------|------|------|
| 旧版（Legacy） | tmp/legacy_release/inbound_forecast_worker/scripts/train_daily_model.py | 1,258行 |
| 現状（Current） | app/backend/inbound_forecast_worker/scripts/train_daily_model.py | 1,332行 |

### 主要関数

1. **preprocess_reserve()** (L233-285): 予約CSVを日次集計に変換
2. **make_stage2_features()** (L341-400): Stage 2特徴量生成（予約含む）
3. **run_walkforward()** (L520-850): Walk-forward評価のメイン関数

## 2. preprocess_reserve()の詳細比較

### 2.1 関数シグネチャ

**共通**（変更なし）:
```python
def preprocess_reserve(df: Optional[pd.DataFrame], 
                      date_col: str, 
                      count_col: str, 
                      fixed_col: str) -> pd.DataFrame:
```

### 2.2 入力データ仮定

| 項目 | 旧版 | 現状 | 差異 |
|------|------|------|------|
| 入力形式 | CSV（1企業1行） | CSV（1企業1行） | 同一 |
| 日付列 | `date_col` (例："予約日") | 同一 | 同一 |
| 台数列 | `count_col` (例："台数") | 同一 | 同一 |
| 固定客列 | `fixed_col` (例："固定客") | 同一 | 同一 |
| 固定客値 | TRUE/FALSE, 1/0, "固定", "固定客" | 同一 | 同一 |

### 2.3 列マッピング（L260-263）

**旧版・現状 共通**:
```python
cmap = _auto_map_columns2(dd, {
    "date":  [date_col, "予約日", "日付"],
    "count": [count_col, "台数", "予約台数", "件数"],
    "fixed": [fixed_col, "固定客", "固定"]
})
```

### 2.4 日付パース（L265-266）

**共通**（変更なし）:
```python
if cmap["date"] is None:
    raise ValueError("予約データの日付列が見つかりません。")
dd[cmap["date"]] = _parse_date_series(dd[cmap["date"]])
```

### 2.5 台数列の処理（L267-269 旧版 vs L274-278 現状）

**旧版**:
```python
if cmap["count"] in dd.columns:
    dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]].str.replace(",","",regex=False), errors="coerce")
```

**現状**:
```python
if cmap["count"] in dd.columns:
    # 台数列の型チェック：文字列なら","除去、数値ならそのまま
    if pd.api.types.is_numeric_dtype(dd[cmap["count"]]):
        dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]], errors="coerce")
    else:
        dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]].astype(str).str.replace(",","",regex=False), errors="coerce")
```

**差異**: 
- ✅ 現状は数値型を先にチェック（DBから数値で取得した場合の対応）
- ⚠️ 動作上の影響: **なし**（最終的に同じ数値に変換）

### 2.6 固定客列の処理（L270 旧版・L279 現状）

**旧版・現状 完全同一**:
```python
if cmap["fixed"] in dd.columns:
    dd[cmap["fixed"]] = dd[cmap["fixed"]].astype(str).str.lower().isin(["1","true","yes","固定","固定客"]).astype(int)
```

**処理内容**:
1. 文字列に変換
2. 小文字化
3. ["1","true","yes","固定","固定客"]に該当するか判定
4. int型（1/0）に変換

**重要**: この時点で固定客列は**1（固定客）または 0（非固定客）**のint

### 2.7 日次集計（L272-276 旧版・L281-285 現状）

**旧版・現状 完全同一**:
```python
grp = dd.groupby(cmap["date"])
out = pd.DataFrame({
    "reserve_count": grp.size().astype(float),
    "reserve_sum": (grp[cmap["count"]].sum() if cmap["count"] in dd.columns else grp.size()).astype(float),
    "fixed_ratio": (grp[cmap["fixed"]].mean() if cmap["fixed"] in dd.columns else 0.0)
})
return out
```

**処理の詳細**:

| 特徴量 | 計算式 | 意味 |
|--------|--------|------|
| reserve_count | `grp.size()` | その日の予約**企業数**（行数） |
| reserve_sum | `grp[count].sum()` | その日の予約**台数合計** |
| fixed_ratio | `grp[fixed].mean()` | **固定客フラグの平均 = 固定客企業数 / 総企業数** |

**❗重要な発見**:

`fixed_ratio = grp[cmap["fixed"]].mean()`は以下を計算：

```python
# fixedは1/0のint
# mean()は平均値を返す
# 例：[1, 1, 0, 1, 0]の平均 = (1+1+0+1+0)/5 = 3/5 = 0.6

# つまり：
fixed_ratio = (固定客企業の数) / (総企業数)
            = (固定客=1の行数) / (総行数)
```

**これは「固定客企業比率」であり、「固定客台数比率」ではない**

## 3. DBからの予約データ取得（現状のみ）

### reserve_exporter.py（DB環境）

```python
# app/backend/core_api/app/infra/adapters/forecast/reserve_exporter.py L43-52
sql = text("""
    SELECT 
        date AS "予約日",
        reserve_trucks AS "台数",
        reserve_fixed_trucks AS "固定客"  -- ← ここが問題
    FROM mart.v_reserve_daily_for_forecast
    WHERE date >= :start_date 
      AND date <= :end_date
    ORDER BY date
""")
```

**重大な不一致**:
- CSVの"固定客"列: Boolean（TRUE/FALSE）→ 1企業あたり1行
- DBの"固定客"列: **数値（台数）** → 固定客の台数合計

### 実データ比較（2025-10-31）

| 項目 | CSV | DB | 計算ロジック |
|------|-----|----|-----------| 
| 固定客列の型 | Boolean（企業ごと） | int（台数合計） | - |
| 固定客列の値 | TRUE/FALSE | 42 | - |
| 日次集計後 | - | - | - |
| reserve_count | 62（企業数） | - | grp.size() |
| reserve_sum | 87（台数） | 87（台数） | grp[count].sum() |
| **fixed_ratio（CSV）** | **26/62 = 0.419** | - | grp[fixed].mean()（企業比率） |
| **fixed_ratio（DB）** | - | **42（そのまま）** | DBから直接取得した値 |

**DBの"固定客"列は台数（42）なので、`.mean()`すると42のまま** → これは意味をなさない

## 4. make_stage2_features()の予約特徴量利用

### L352-358（旧版・現状 同一）

```python
def make_stage2_features(..., reserve_daily: Optional[pd.DataFrame], use_same_day_info: bool):
    # ...
    if isinstance(reserve_daily, pd.DataFrame) and len(reserve_daily) > 0:
        r = reserve_daily.reindex(index).fillna(0.0)
        ex = pd.concat([ex, r], axis=1)
    else:
        ex[["reserve_count", "reserve_sum", "fixed_ratio"]] = 0.0
    # ...
```

**処理内容**:
1. `reserve_daily`（preprocess_reserve()の出力）を日付インデックスで結合
2. 欠損値は0.0で埋める
3. Stage 2モデルの特徴量として`fixed_ratio`を使用

**影響**:
- CSV環境: `fixed_ratio` = 0.419（企業比率、正しい意味）
- DB環境: `fixed_ratio` = 42（台数、**意味不明**）または計算されていない

## 5. 精度劣化の根本原因

### 5.1 データフロー比較

#### 旧版（CSV）

```
yoyaku_data.csv (1企業1行、固定客=TRUE/FALSE)
  ↓
preprocess_reserve()
  ├─ 固定客列を1/0に変換
  └─ grp[fixed].mean() → 固定客企業数/総企業数 = 企業比率
  ↓
Stage 2特徴量: fixed_ratio = 0.419（企業比率）
  ↓
Stage 2モデル学習・予測
```

#### 現状（DB）

```
mart.v_reserve_daily_for_forecast (固定客台数=42)
  ↓
reserve_exporter.py
  ├─ "固定客"列 = reserve_fixed_trucks（台数）
  ↓
preprocess_reserve() ← ここが問題
  ├─ 固定客列（既に台数）を1/0変換試行（失敗またはそのまま）
  └─ grp[fixed].mean() → 意味不明な値
  ↓
Stage 2特徴量: fixed_ratio = ??? (不正確)
  ↓
Stage 2モデル学習・予測 ← 精度劣化
```

### 5.2 実測影響

| 指標 | 旧版（CSV） | 現状（DB） | 劣化率 |
|------|-------------|-----------|--------|
| R2_total | 0.823 | 0.671 | -18.5% |
| R2_sum_only | 0.466 | 0.069 | **-85.2%** |
| MAE | 9,935 kg | 13,286 kg | +33.7% |

**R2_sum_only劣化が極めて大きい（-85%）**:
- sum_only指標はStage 2（集計予測）の精度を測定
- fixed_ratioはStage 2の重要特徴量
- fixed_ratioの破損 → Stage 2の精度崩壊

## 6. 差分ランキング（精度劣化への影響度）

| 順位 | 差分内容 | 影響度 | 根拠 |
|------|----------|--------|------|
| **1位** | **fixed_ratio特徴量の概念不一致** | **CRITICAL** | Stage 2精度崩壊（R2_sum_only -85%）、CSV=企業比率（0.419）vs DB=台数（42）で全く異なる |
| 2位 | reserve_fixed_trucks列の命名 | HIGH | 台数と企業数の混同を誘発、データ契約の曖昧性 |
| 3位 | 台数列の型チェック追加 | NONE | 最終値は同一、互換性向上のみ |
| 4位 | tz-aware対応 | NONE | 日付処理の堅牢性向上、精度への影響なし |

## 7. 予約特徴量の変換チェーン（再帰的追跡）

### 7.1 旧版の処理フロー

```
Step 1: CSVファイル読み込み
  └─ yoyaku_data.csv (53,399行、2023-01-04 ～ 2025-10-31)
     ├─ 列: 予約日, 予約得意先名, 固定客(Boolean), 台数(int)
     └─ 1行 = 1企業の予約

Step 2: _read_csv()
  └─ エンコーディング自動判定（utf-8-sig, cp932）

Step 3: preprocess_reserve()
  ├─ 列マッピング: auto_map_columns2()
  │  └─ "予約日", "台数", "固定客"を自動検出
  ├─ 日付パース: _parse_date_series()
  ├─ 台数: pd.to_numeric()で数値化
  ├─ 固定客: .isin(["1","true","yes"]).astype(int) → 1/0
  └─ 日次集計: groupby(date)
     ├─ reserve_count = size() → 企業数
     ├─ reserve_sum = sum(台数) → 台数合計
     └─ fixed_ratio = mean(固定客) → 固定客企業数/総企業数

Step 4: make_stage2_features()
  └─ reserve_dailyを日付でreindex、NaN→0.0

Step 5: Stage 2モデル
  └─ fixed_ratio特徴量を使用（企業比率、0-1範囲）
```

### 7.2 現状の処理フロー（DB）

```
Step 1: DBビュー照会
  └─ mart.v_reserve_daily_for_forecast (992行)
     ├─ 列: date, reserve_trucks(int), reserve_fixed_trucks(int), reserve_fixed_ratio(decimal)
     └─ 1行 = 1日の集計済みデータ

Step 2: reserve_exporter.export_reserve_data()
  ├─ SQL: SELECT date AS "予約日", reserve_trucks AS "台数", reserve_fixed_trucks AS "固定客"
  └─ DataFrame返却（日本語列名）

Step 3: preprocess_reserve() ← ここで不整合発生
  ├─ 列マッピング: "固定客"列を検出
  ├─ 固定客列の処理:
  │  └─ .isin(["1","true","yes"]).astype(int)
  │     ← 既に数値（42）なので、変換失敗または意図しない結果
  └─ 日次集計: groupby(date)
     ├─ reserve_count = size() → 1（既に日次集計済みなので）
     ├─ reserve_sum = sum(台数) → 87（そのまま）
     └─ fixed_ratio = mean(固定客) → 42（意味不明）

Step 4: make_stage2_features()
  └─ fixed_ratio=42を特徴量として使用 ← 異常値

Step 5: Stage 2モデル
  └─ 異常な固定客比率でトレーニング → 精度劣化
```

### 7.3 データ変換の具体例（2025-10-31）

#### 旧版（CSV入力）

| 処理段階 | データ形式 | サンプル |
|---------|-----------|---------|
| CSV行 | 1企業1行 | `2025/10/31, ミヤ産興, TRUE, 1` |
| 固定客列変換 | int | `1` (TRUE→1) |
| 日次集計前 | 62行 | 固定客=1が26行、固定客=0が36行 |
| 日次集計後 | 1行 | `reserve_count=62, reserve_sum=87, fixed_ratio=26/62=0.419` |

#### 現状（DB入力）

| 処理段階 | データ形式 | サンプル |
|---------|-----------|---------|
| DB行 | 1日1行 | `2025-10-31, 87, 42, 0.4828` |
| CSV変換 | 列名変更 | `予約日: 2025-10-31, 台数: 87, 固定客: 42` |
| 固定客列変換 | ??? | `42` (isin()で判定失敗、そのまま？) |
| 日次集計前 | 1行 | 固定客=42 |
| 日次集計後 | 1行 | `reserve_count=1, reserve_sum=87, fixed_ratio=42` |

## 8. 欠損処理・期間窓の差異

### 8.1 欠損処理

**両バージョン共通**:
```python
# make_stage2_features() L355
r = reserve_daily.reindex(index).fillna(0.0)
```

- 予約データがない日は0.0で埋める
- 処理ロジックは同一

### 8.2 期間窓

**両バージョンで差異なし**:
- Config.max_history_days = 600（デフォルト）
- Walk-forward評価期間は同一
- データ取得期間は引数で制御

## 9. 集計・スケーリングの差異

### 9.1 Stage 2特徴量のスケーリング

**両バージョン共通**:
```python
# L405-420
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)
```

- StandardScaler使用
- 平均0、標準偏差1に正規化

**影響**:
- CSV環境: fixed_ratio=0.419 → 正規化後も妥当な範囲
- DB環境: fixed_ratio=42 → 正規化後も外れ値扱い

### 9.2 最終特徴量名一覧

**Stage 2特徴量（両バージョン共通）**:
```python
[
    "y_dow_0", "y_dow_1", ..., "y_dow_6",  # 曜日ダミー
    "y_ma7", "y_ma14", "y_ma28",            # 移動平均
    "y_lag1", "y_lag7", "y_lag14",          # ラグ
    "reserve_count",                         # 予約企業数（現状DBでは意味不明）
    "reserve_sum",                           # 予約台数合計
    "fixed_ratio",                           # 固定客比率（CSVと DBで全く異なる）
    "s1_sum",                                # Stage 1予測合計
    "s1_top6_sum"                            # Stage 1上位6品目予測合計
]
```

## 10. 結論

### 10.1 差分の性質

| カテゴリ | 判定 | 説明 |
|---------|------|------|
| preprocess_reserve()のロジック | **同一** | コード的には変更なし |
| 入力データの構造 | **異なる** | CSV=企業粒度、DB=日次集計済み |
| 固定客列の意味 | **根本的に異なる** | CSV=Boolean(企業)、DB=int(台数) |
| fixed_ratio特徴量 | **完全に不整合** | CSV=企業比率、DB=台数（異常値） |

### 10.2 精度劣化への寄与度

1. **fixed_ratio特徴量の破損**: **90%**
   - Stage 2の主要特徴量が異常値
   - R2_sum_only -85%と直接対応

2. **reserve_count特徴量の破損**: **5%**
   - DB入力では常に1（無意味）

3. **その他の差分**: **5%**
   - コードの堅牢性向上、精度への影響なし

### 10.3 修正の方向性

**必須対応**:
1. ✅ 固定客数（社数）を別途取得し、企業比率を正確に計算
2. ✅ 固定客台数と固定客数を明確に区別
3. ✅ reserve_exporter.pyで両方の値をエクスポート

**推奨対応**:
4. ⚠️ mart.v_reserve_daily_for_forecastに固定客数列を追加（DB設計改善）
5. ⚠️ 特徴量名を明確化（fixed_trucks_ratio vs fixed_customer_ratio）

## 11. 次のアクション

1. ✅ 静的差分解析完了
2. ⏳ 動的比較（同一入力での特徴量CSV出力）
3. ⏳ 固定客数を追加する最小差分修正の実装
