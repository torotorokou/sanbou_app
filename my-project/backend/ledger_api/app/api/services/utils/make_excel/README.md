# Excel出力ユーティリティ（FastAPI用）

現在のコンテナに合わせて、DataFrameを受け取ってExcelファイル（bytes）を返すシンプルなユーティリティです。

## 📦 ファイル構成

```
make_excel/
├── excel_utils.py              # 核心機能（DataFrame → Excel変換）
├── fastapi_excel_response.py   # FastAPI用レスポンスヘルパー
├── test_excel_utils.py         # テスト・使用例
└── README.md                   # このファイル
```

## 🚀 基本的な使用方法

### 1. シンプルなExcel出力

```python
import pandas as pd
from app.api.services.utils.make_excel.excel_utils import df_to_excel

# データ準備
df = pd.DataFrame({
    "商品名": ["りんご", "バナナ", "オレンジ"],
    "価格": [100, 80, 120],
    "数量": [10, 15, 8]
})

# Excel変換（bytes形式）
excel_bytes = df_to_excel(df, sheet_name="商品一覧")

# ファイル保存
with open("output.xlsx", "wb") as f:
    f.write(excel_bytes)
```

### 2. フォーマット付きExcel出力

```python
# 特定の列名で日本語フォント付き出力
df = pd.DataFrame({
    "大項目": ["材料費", "労務費"],
    "中項目": ["鉄骨", "作業員"], 
    "単価": [1500.50, 2000.00],
    "台数": [5, 3]
})

# フォーマット付きで出力
excel_bytes = df_to_excel(df, use_formatting=True)
```

### 3. テンプレートベース出力

```python
# テンプレート用のDataFrame（セル・値形式）
template_df = pd.DataFrame({
    "セル": ["A1", "B1", "A2", "B2"],
    "値": ["項目", "金額", "材料費", 1500]
})

# テンプレートファイルを使用
excel_bytes = df_to_excel(
    template_df, 
    template_path="template.xlsx",
    sheet_name="帳票"
)
```

## 🌐 FastAPIでの使用方法

### 1. Excel ダウンロードエンドポイント

```python
from fastapi import FastAPI
import pandas as pd
from app.api.services.utils.make_excel.fastapi_excel_response import create_excel_response

app = FastAPI()

@app.get("/download-excel")
async def download_excel():
    # データ準備
    df = pd.DataFrame({
        "ユーザー名": ["田中", "佐藤", "鈴木"],
        "年齢": [30, 25, 35],
        "部署": ["営業", "開発", "人事"]
    })
    
    # Excelレスポンス作成
    return create_excel_response(
        df=df,
        filename="user_list.xlsx",
        sheet_name="ユーザー一覧"
    )
```

### 2. JSONデータをExcelに変換

```python
from app.api.services.utils.make_excel.fastapi_excel_response import excel_from_dict_list

@app.post("/json-to-excel")
async def json_to_excel(data: list):
    # JSON配列をExcelに変換
    return excel_from_dict_list(
        data=data,
        filename="converted_data.xlsx"
    )
```

### 3. CSVをExcelに変換

```python
from app.api.services.utils.make_excel.fastapi_excel_response import excel_from_csv_data

@app.post("/csv-to-excel")
async def csv_to_excel(csv_content: str):
    return excel_from_csv_data(
        csv_data=csv_content,
        filename="converted.xlsx"
    )
```

## 🔧 主要機能

### `df_to_excel()` - 統合関数

```python
def df_to_excel(
    df: pd.DataFrame, 
    sheet_name: str = "データ",
    use_formatting: bool = True,
    template_path: Optional[Union[str, Path]] = None
) -> bytes
```

**パラメータ:**
- `df`: 出力するDataFrame
- `sheet_name`: シート名
- `use_formatting`: 日本語フォント等のフォーマットを適用するか
- `template_path`: テンプレートファイルのパス（指定時はテンプレート出力）

**戻り値:** Excelファイルのバイナリデータ（bytes）

### 個別関数

- `simple_df_to_excel()`: シンプルな変換
- `formatted_df_to_excel()`: フォーマット付き変換
- `template_df_to_excel()`: テンプレートベース変換

## 📋 対応フォーマット

### 入力データ形式

1. **通常のDataFrame**
   ```python
   df = pd.DataFrame({"列1": [1, 2, 3], "列2": ["A", "B", "C"]})
   ```

2. **テンプレート用DataFrame**
   ```python
   df = pd.DataFrame({
       "セル": ["A1", "B1", "A2"],  # セル位置
       "値": ["項目", "金額", 1500]   # 書き込む値
   })
   ```

### 特別な列名への対応

- **"中項目"列**: NaN値を自動的に空白に変換
- **"単価"列**: 小数点2桁の数値フォーマット適用
- **カスタム列幅**: 指定された列名に対して最適な幅を設定

## ⚙️ 技術仕様

### 必要なライブラリ
- `pandas`: データ処理
- `openpyxl`: Excelファイル読み書き
- `xlsxwriter`: 高品質Excel生成（オプション）
- `fastapi`: Web API（FastAPI使用時）

### サポートするPythonバージョン
- Python 3.8+

### Excel出力の特徴
- **日本語フォント**: 游ゴシック使用
- **書式保持**: テンプレート使用時は元の書式を維持
- **メモリ効率**: BytesIOを使用してメモリ内処理

## 🧪 テスト方法

```bash
cd /backend/app/api/services/utils/make_excel
python test_excel_utils.py
```

## 📝 使用例・応用シーン

### 1. レポート出力システム
```python
# 月次売上レポート
sales_df = get_monthly_sales_data()
excel_bytes = df_to_excel(sales_df, "月次売上レポート", use_formatting=True)
```

### 2. データエクスポート機能
```python
# ユーザー管理画面からのエクスポート
users_df = get_all_users()
return create_excel_response(users_df, "users.xlsx")
```

### 3. 定型帳票の生成
```python
# 請求書テンプレートの利用
invoice_data = pd.DataFrame({
    "セル": ["B2", "B3", "B10"],
    "値": ["田中商事", datetime.now().strftime("%Y/%m/%d"), 150000]
})
excel_bytes = df_to_excel(invoice_data, template_path="invoice_template.xlsx")
```

## ⚠️ 注意事項

1. **テンプレートファイル**: 事前にExcelテンプレートファイルを準備する必要があります
2. **メモリ使用量**: 大量データの場合は適切なチャンク処理を検討してください
3. **フォント**: 游ゴシックが利用できない環境では代替フォントに自動変更されます
4. **エラーハンドリング**: 本番環境では適切な例外処理を実装してください

## 🔗 関連ファイル

- `app/api/endpoints/manage_report.py`: 管理レポート機能で使用
- `app/api/services/report_generator.py`: レポート生成サービス

---

*元のコードから現在のコンテナに合わせて最適化・統合 - 2025年7月*
