# Factory Report API移植版

このディレクトリには、別のコンテナで開発されていた工場日報生成システムを現在のAPI形式に移植したファイル群が含まれています。

## 概要

工場日報テンプレート用の処理システムで、ヤード一覧と出荷一覧のCSVデータを読み込み、処分・有価・ヤード等の処理を適用し、最終的な工場日報データフレームを生成します。

## ディレクトリ構造

```
factory_report/
├── README.md                    # このファイル
├── factory_report.py           # メイン処理関数
├── processors/                 # 各種プロセッサー
│   ├── __init__.py
│   ├── factory_report_shobun.py  # 出荷処分データ処理
│   ├── factory_report_yuuka.py   # 出荷有価データ処理
│   ├── factory_report_yard.py    # 出荷ヤードデータ処理
│   ├── make_cell_num.py          # セル番号設定
│   ├── make_label.py             # ラベル追加
│   ├── summary.py                # 集計処理
│   └── etc.py                    # その他処理（合計・総合計行追加、日付フォーマット等）
├── utils/                      # ユーティリティ関数
│   ├── __init__.py
│   ├── config_loader.py          # 設定ファイル読み込み
│   ├── csv_loader.py             # CSV読み込み処理
│   ├── data_cleaning.py          # データクリーニング
│   ├── excel_tools.py            # Excel関連ツール
│   ├── load_template.py          # テンプレート読み込み
│   ├── logger.py                 # ログ処理
│   └── summary_tools.py          # 集計ツール
├── config/                     # 設定ファイル
│   ├── templates_config.yaml     # テンプレート設定
│   └── required_columns_definition.yaml  # 必須カラム定義
└── data/                       # データファイル
    ├── master/                 # マスターデータ
    │   ├── shobun_map.csv       # 処分マッピング
    │   ├── yuka_map.csv         # 有価マッピング
    │   ├── yard_map.csv         # ヤードマッピング
    │   └── etc.csv              # その他データ
    └── templates/              # テンプレートファイル
        └── factory_report.xlsx  # Excelテンプレート
```

## 使用方法

### 基本的な使用方法

```python
from app.api.services.manage_report_processors.factory_report.factory_report import process

# CSVデータの辞書を準備
dfs = {
    "shipment": shipment_dataframe,  # 出荷データ
    "yard": yard_dataframe          # ヤードデータ
}

# 処理実行
try:
    result_df = process(dfs)
    print("工場日報の生成が完了しました")
except Exception as e:
    print(f"エラーが発生しました: {e}")
```

### 必要なカラム

#### 出荷データ (shipment)
- 業者CD
- 業者名
- 現場名
- 金額
- 正味重量
- 伝票日付
- 品名

#### ヤードデータ (yard)
- 種類名
- 正味重量
- 伝票日付
- 品名

## 現在のコンテナでの使用上の注意点

### 1. 依存関係のインストール

必要なPythonライブラリがインストールされていることを確認してください：

```bash
pip install pandas pyyaml openpyxl
```

### 2. ログディレクトリの作成

ログファイルの出力先ディレクトリを作成してください：

```bash
mkdir -p /backend/logs
```

### 3. 設定ファイルの調整

必要に応じて以下の設定ファイルを環境に合わせて調整してください：

- `config/templates_config.yaml`: テンプレート設定
- `config/required_columns_definition.yaml`: 必須カラム定義

### 4. データファイルの配置

マスターデータファイルとテンプレートファイルが正しく配置されていることを確認してください：

- `data/master/`: マスターCSVファイル群
- `data/templates/`: Excelテンプレートファイル

### 5. パスの設定

現在の実装では絶対パスを使用しています。環境が異なる場合は、以下のファイルでパス設定を調整してください：

- `utils/config_loader.py`
- `utils/logger.py`

### 6. エラーハンドリング

移植版では可能な限りエラーハンドリングを追加していますが、データの形式や内容によってはエラーが発生する可能性があります。ログファイルを確認してください：

- アプリケーションログ: `/backend/logs/factory_report_app.log`
- デバッグログ: `/backend/logs/factory_report_debug.log`

## トラブルシューティング

### よくある問題

1. **インポートエラー**
   - Pythonパスが正しく設定されているか確認
   - 必要なモジュールがインストールされているか確認

2. **ファイルが見つからないエラー**
   - データファイルのパスが正しいか確認
   - ファイルの権限を確認

3. **カラムが見つからないエラー**
   - 入力CSVファイルに必要なカラムが含まれているか確認
   - カラム名が正確に一致しているか確認

### デバッグ方法

詳細なログを出力するには：

```python
from app.api.services.manage_report_processors.factory_report.utils.logger import debug_logger

logger = debug_logger()
logger.debug("デバッグメッセージ")
```

## 制限事項

1. **Streamlit依存の削除**: 元のコードにあったStreamlit依存部分は削除されています
2. **設定の簡素化**: 複雑な設定システムは簡素化されています
3. **エラーハンドリング**: 一部のエラーハンドリングは簡素化されています

## 今後の改善点

1. より詳細なエラーメッセージ
2. 設定ファイルの環境変数対応
3. テストケースの追加
4. パフォーマンスの最適化

## 移植日時

移植日: 2025年7月31日
移植者: GitHub Copilot

## サポート

問題が発生した場合は、ログファイルを確認し、必要に応じて設定ファイルやデータファイルを調整してください。
