# サービスレイヤー構成

このディレクトリには、ledger APIのビジネスロジックを実装するサービス層が含まれています。

## ディレクトリ構成

```
services/
├── csv/                          # CSV処理関連サービス
│   ├── __init__.py
│   ├── formatter_service.py      # CSVフォーマット変換
│   ├── validator_service.py      # CSVバリデーション
│   └── README.md
├── report/                       # レポート生成関連サービス
│   ├── __init__.py
│   ├── base_report_generator.py           # レポート生成基底クラス
│   ├── base_interactive_report_generator.py # インタラクティブレポート基底クラス
│   ├── concrete_generators.py             # 具体的なレポート生成クラス
│   ├── generator_factory.py               # レポート生成ファクトリ
│   ├── report_processing_service.py       # レポート処理サービス
│   ├── interactive_report_processing_service.py # インタラクティブレポート処理
│   ├── artifact_builder.py                # アーティファクト構築
│   ├── artifact_service.py                # アーティファクト管理
│   ├── session_store.py                   # セッション管理
│   ├── report_date.py                     # 日付処理
│   └── ledger/                            # 帳簿レポート実装
│       ├── average_sheet.py               # 平均表
│       ├── balance_sheet.py               # 残高表
│       ├── factory_report.py              # 工場レポート
│       ├── management_sheet.py            # 管理表
│       ├── interactive/                   # インタラクティブレポート
│       ├── processors/                    # レポートプロセッサー
│       └── utils/                         # ユーティリティ
├── csv_formatter_service.py      # [非推奨] 後方互換性レイヤー
├── csv_validator_facade.py       # [非推奨] 後方互換性レイヤー
└── __init__.py
```

## 機能別モジュール

### 1. CSV処理サービス (`csv/`)

CSV関連の処理を担当します。

**主要クラス**:
- `CsvFormatterService`: CSVデータのフォーマット変換
- `CsvValidatorService`: CSVファイルのバリデーション

**使用例**:
```python
from app.api.services.csv import CsvFormatterService, CsvValidatorService

# フォーマット処理
formatter = CsvFormatterService()
formatted_dfs = formatter.format(dfs)

# バリデーション処理
validator = CsvValidatorService()
error_response = validator.validate(dfs, files)
```

### 2. レポート生成サービス (`report/`)

各種レポートの生成と管理を担当します。

**主要クラス**:
- `BaseReportGenerator`: レポート生成の基底クラス
- `ReportProcessingService`: レポート処理のオーケストレーション
- `InteractiveReportProcessingService`: インタラクティブレポート処理
- 各種具体的なジェネレーター (`BalanceSheetGenerator`, `AverageSheetGenerator`, など)

**使用例**:
```python
from app.api.services.report import ReportProcessingService
from app.api.services.report.concrete_generators import BalanceSheetGenerator

service = ReportProcessingService()
generator = BalanceSheetGenerator()
result = await service.process_report(files, start_date, end_date, generator)
```

## 設計原則

### 1. 責任の分離 (Separation of Concerns)
- CSVの処理とレポート生成は明確に分離
- 各サービスは単一の責任を持つ

### 2. 依存性の注入 (Dependency Injection)
- サービス間の依存は疎結合
- テスタビリティを考慮した設計

### 3. ファサードパターン
- 複雑な処理を単純なインターフェースで提供
- `CsvValidatorService`, `ReportProcessingService` などがファサード

### 4. ファクトリーパターン
- 適切なジェネレーターやフォーマッターを動的に生成
- 拡張性を考慮した設計

## 移行ガイド

### 旧インポートから新インポートへの移行

**変更前**:
```python
from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService
```

**変更後**:
```python
from app.api.services.csv import CsvFormatterService, CsvValidatorService
```

既存のインポートは後方互換性のために引き続き動作しますが、新しいコードでは新しいインポート方法を使用してください。

## 今後の拡張

- `database/`: データベース操作サービス
- `notification/`: 通知サービス
- `cache/`: キャッシュ管理サービス
- `export/`: エクスポートサービス
