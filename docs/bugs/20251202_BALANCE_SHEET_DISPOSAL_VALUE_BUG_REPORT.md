# 売上収支表「処分有価」値不一致問題 - 調査レポート

**作成日**: 2024年12月2日  
**ブランチ**: `debug/balance-sheet-disposal-value-mismatch`  
**優先度**: 🔴 **HIGH** - データ精度に直接影響  
**ステータス**: 🔍 **根本原因特定完了**

---

## 📋 問題概要

旧Streamlitアプリから新Reactアプリへの移行中、売上収支表において「処分有価」（有価物）の値が一致しない問題が発生。

### 影響範囲

- **帳票**: 売上収支表（balance_sheet）
- **項目**: 有価物（仕入計の計算に使用）
- **計算式**: `仕入計 = 処分費 - 有価物`

---

## 🔍 根本原因

### 問題のあるファイル

`app/backend/ledger_api/app/core/domain/reports/processors/balance_sheet/balance_sheet_yuukabutu.py`

### バグの詳細

#### 1. 無意味な二重適用（47-53行目）

```python
def calculate_valuable_material_cost_by_item(df_yard: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_yard"]
    master_df = load_master_and_template(master_path)

    master_with_quantity = summary_apply(
        master_df,
        df_yard,
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )

    # 🐛 問題箇所: 同じデータフレームを2回マージしている
    result_df = summary_apply(
        master_with_quantity,      # ← マスターDF
        master_with_quantity,      # ← 同じDFを再度マージ（意味がない）
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )
    result_df = result_df.rename(columns={"品名": "大項目"})
    return result_df
```

#### 2. 単価計算の欠落

**現在の処理**: 数量のみを返している（金額を計算していない）  
**期待される処理**: `金額 = 数量 × 単価`

---

## 🔄 正しい処理フロー

他の正常に動作している関数を参考：

### 参考1: `balance_sheet_yuka_kaitori.py` (有価買取)

```python
def calculate_purchase_value_of_valuable_items(receive_df: pd.DataFrame) -> int:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["uriage_yuka_kaitori"]
    master_df = load_master_and_template(master_path)

    # ① 数量を集計
    master_with_quantity = summary_apply(
        master_df,
        receive_df,
        key_cols=["品名", "伝票区分名"],
        source_col="数量",
        target_col="数量",
    )

    # ② 単価テーブルを取得
    unit_price_df = get_unit_price_table_csv()
    unit_price_df = unit_price_df[unit_price_df["必要項目"] == "有価買取"]

    # ③ 単価をマージ
    master_with_prices = summary_apply(
        master_with_quantity,
        unit_price_df,
        key_cols=["品名"],
        source_col="設定単価",
        target_col="設定単価",
    )

    # ④ 数量 × 単価 = 金額
    result_df = multiply_columns(
        master_with_prices, col1="設定単価", col2="数量", result_col="値"
    )

    total = int(result_df["値"].sum())
    return total
```

### 参考2: `balance_sheet_syobun.py` (処分費)

```python
def calculate_safe_disposal_costs(df_shipment: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["syobun_cost_kinko"]
    master_df = load_master_and_template(master_path)

    key_cols = ["業者名", "品名"]

    # ① 重量を集計
    master_with_weight = summary_apply(
        master_df,
        df_shipment,
        key_cols=key_cols,
        source_col="正味重量",
        target_col="正味重量",
    )

    # ② 単価テーブルから単価を取得
    unit_price_df = get_unit_price_table_csv()
    master_with_price = summary_apply(
        master_with_weight,
        unit_price_df,
        key_cols=key_cols,
        source_col="設定単価",
        target_col="設定単価",
    )

    # ③ 単価 × 重量 = 金額
    master_csv_kinko = multiply_columns(
        master_with_price, col1="設定単価", col2="正味重量", result_col="値"
    )
    return master_csv_kinko
```

---

## ✅ 修正方法

### 修正すべき関数

`calculate_valuable_material_cost_by_item(df_yard: pd.DataFrame) -> pd.DataFrame`

### 修正内容

```python
def calculate_valuable_material_cost_by_item(df_yard: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["balance_sheet"]
    master_path = config["master_csv_path"]["yuka_yard"]
    master_df = load_master_and_template(master_path)

    # ① ヤードデータから品名別に数量を集計
    master_with_quantity = summary_apply(
        master_df,
        df_yard,
        key_cols=["品名"],
        source_col="数量",
        target_col="数量",
    )

    # ② 単価テーブルから有価物の単価を取得
    unit_price_df = get_unit_price_table_csv()
    unit_price_df = unit_price_df[unit_price_df["必要項目"] == "有価物"]

    # ③ 単価をマージ
    master_with_price = summary_apply(
        master_with_quantity,
        unit_price_df,
        key_cols=["品名"],
        source_col="設定単価",
        target_col="設定単価",
    )

    # ④ 数量 × 単価 = 金額（値）
    result_df = multiply_columns(
        master_with_price, col1="設定単価", col2="数量", result_col="値"
    )

    result_df = result_df.rename(columns={"品名": "大項目"})
    return result_df
```

### 必要なインポート追加

```python
from app.infra.report_utils import get_unit_price_table_csv
from app.infra.report_utils.formatters import multiply_columns
```

---

## 📊 単価テーブル参照データ

`infra/data_sources/master/costs/unit_price_table.csv`より、有価物の単価設定：

| 品名           | 設定単価 | 必要項目 | CSVシート |
| -------------- | -------- | -------- | --------- |
| GAH鋼･鉄筋等   | 31.5     | 有価物   | ヤード    |
| GC軽鉄･ｽﾁｰﾙ類  | 31.5     | 有価物   | ヤード    |
| GC軽鉄・ｽﾁｰﾙ類 | 31.5     | 有価物   | ヤード    |
| GD             | 31.5     | 有価物   | ヤード    |
| ｱﾙﾐ類          | 180      | 有価物   | ヤード    |
| ｽﾃﾝﾚｽ          | 180      | 有価物   | ヤード    |
| ﾄﾗﾝｽ           | 33       | 有価物   | ヤード    |
| ﾓｰﾀｰ           | 60       | 有価物   | ヤード    |
| ﾗｼﾞｴﾀｰ         | 31.5     | 有価物   | ヤード    |
| 室外機         | 28       | 有価物   | ヤード    |
| 鉄千地         | 31.5     | 有価物   | ヤード    |
| 銅             | 500      | 有価物   | ヤード    |
| 配線           | 100      | 有価物   | ヤード    |

---

## 🎯 検証項目

修正後、以下を確認すること：

1. ✅ **単価の正しい適用**: ヤードデータの各品名に対して単価が正しく適用される
2. ✅ **金額計算の正確性**: `数量 × 単価 = 値` の計算が正しく行われる
3. ✅ **仕入計への影響**: `仕入計 = 処分費 - 有価物` の計算が正しくなる
4. ✅ **旧アプリとの値一致**: Streamlitアプリと同じ結果になる

---

## 🔗 関連ファイル

### 修正対象

- `app/backend/ledger_api/app/core/domain/reports/processors/balance_sheet/balance_sheet_yuukabutu.py`

### 参考ファイル

- `app/backend/ledger_api/app/core/domain/reports/processors/balance_sheet/balance_sheet_yuka_kaitori.py` (有価買取 - 正常)
- `app/backend/ledger_api/app/core/domain/reports/processors/balance_sheet/balance_sheet_syobun.py` (処分費 - 正常)
- `app/backend/ledger_api/app/infra/data_sources/master/costs/unit_price_table.csv` (単価マスタ)

### 設定ファイル

- `app/backend/ledger_api/app/infra/data_sources/master/balance_sheet/yuka_yard.csv` (有価物品目マスタ)
- `app/backend/ledger_api/app/config/templates_config.yaml`

---

## 📝 その他の注意点

### 仕入計の計算式

`app/backend/ledger_api/app/core/domain/reports/processors/balance_sheet/balance_sheet_etc.py`

```python
def calculate_misc_summary_rows(
    master_csv: pd.DataFrame, first_invoice_date: pd.Timestamp
) -> pd.DataFrame:
    # ...

    shobun_cost = safe_int(
        master_csv.loc[master_csv["大項目"] == "処分費", "値"].values[0]
    )
    yuka_cost = safe_int(
        master_csv.loc[master_csv["大項目"] == "有価物", "値"].values[0]
    )

    # 仕入計 = 処分費 - 有価物
    cost_total = shobun_cost - yuka_cost
    etc_df = set_value_fast_safe(etc_df, ["大項目"], ["仕入計"], cost_total, "値")

    # ...
```

有価物の値が間違っていると、仕入計、ひいては損益の計算も狂ってしまいます。

---

## 🚀 次のアクション

1. **修正実装**: 上記の修正をコードに適用
2. **単体テスト**: 修正した関数の動作確認
3. **統合テスト**: 実際のCSVデータでバランスシート全体を生成し、値を確認
4. **回帰テスト**: 旧Streamlitアプリの結果と比較検証
5. **プルリクエスト**: レビュー・マージ

---

## 📌 まとめ

**根本原因**: `calculate_valuable_material_cost_by_item`関数で単価を掛け合わせる処理が欠落していた

**影響**: 有価物の値が数量のみとなり、金額が正しく計算されていない → 仕入計・損益の値も不正確

**解決策**: 単価テーブルから単価を取得し、`multiply_columns`で `数量 × 単価` を計算する処理を追加

---

**報告者**: GitHub Copilot  
**確認者**: （レビュー担当者名を記入）
