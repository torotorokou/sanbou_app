# CSV処理サービスモジュール

このディレクトリには、CSVファイルの処理に関連するサービスが含まれています。

## モジュール構成

### `formatter_service.py`
CSVデータのフォーマット変換を行うサービスです。
- **クラス**: `CsvFormatterService`
- **機能**: 
  - 設定ファイルに基づいてCSVタイプごとに適切なフォーマッターを適用
  - 複数のDataFrameを一括でフォーマット

### `validator_service.py`
CSVファイルのバリデーション処理を統合的に管理するサービスです。
- **クラス**: `CsvValidatorService`
- **機能**:
  - 純粋なバリデーションロジックとAPIレスポンス変換の分離
  - 設定ファイルに基づいた包括的なバリデーション

## 使用方法

### 新しいインポート方法（推奨）

```python
# 方法1: 直接インポート
from app.api.services.csv import CsvFormatterService, CsvValidatorService

# 方法2: 個別インポート
from app.api.services.csv.formatter_service import CsvFormatterService
from app.api.services.csv.validator_service import CsvValidatorService
```

### 後方互換性のある旧インポート方法

既存のコードとの互換性のため、以下のインポート方法も引き続き動作します：

```python
from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService
```

**注意**: 新しいコードでは上記の「新しいインポート方法」を使用してください。

## アーキテクチャ

### CsvFormatterService
- **依存**: `backend_shared.config.config_loader.SyogunCsvConfigLoader`
- **設計パターン**: Factory Pattern (フォーマッターの生成)

### CsvValidatorService
- **依存**: 
  - `backend_shared.config.config_loader.SyogunCsvConfigLoader`
  - `backend_shared.src.csv_validator.pure_csv_validator.PureCSVValidator`
  - `backend_shared.src.csv_validator.response_converter.ValidationResponseConverter`
- **設計パターン**: Facade Pattern (バリデーション処理の統合)

## 今後の拡張

このディレクトリには、CSV処理に関連する以下のような機能を追加できます：
- CSV変換サービス
- CSVマージサービス
- CSV統計サービス
