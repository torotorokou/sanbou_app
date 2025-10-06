"""
CSVバリデーターファサードサービス（改良版）

CSVファイルのバリデーション処理を統合的に管理するファサードクラスです。
責任分離の原則に基づき、純粋なバリデーションロジックとAPIレスポンス変換を分離しています。

アーキテクチャ:
- PureCSVValidator: 純粋なバリデーションロジック
- ValidationResponseConverter: バリデーション結果のAPIレスポンス変換
- CsvValidatorService: ファサードとして全体を統合
"""

from backend_shared.infrastructure.config.config_loader import SyogunCsvConfigLoader
from backend_shared.adapters.presentation.response_base import ErrorApiResponse
from backend_shared.usecases.csv_validator.pure_csv_validator import PureCSVValidator
from backend_shared.usecases.csv_validator.response_converter import (
    ValidationResponseConverter,
)


class CsvValidatorService:
    """
    CSVバリデーションサービス（改良版）

    責任分離された設計に基づく統合バリデーションサービス。
    - バリデーションロジックはPureCSVValidatorに委譲
    - APIレスポンス変換はValidationResponseConverterに委譲
    - ファサードとして全体の流れを制御
    """

    def __init__(self):
        """
        サービスの初期化

        設定ローダーとコンバーターを初期化し、バリデーション処理の準備を行います。
        """
        # 昇軍CSV設定ローダーの初期化
        self.config_loader = SyogunCsvConfigLoader()

        # レスポンス変換器の初期化
        self.response_converter = ValidationResponseConverter()

    def validate(self, dfs, files) -> ErrorApiResponse | None:
        """
        CSVファイルの包括的バリデーション（改良版）

        純粋なバリデーションロジックを実行し、結果をAPIレスポンス形式に変換します。
        責任分離により、バリデーションロジックとレスポンス形式が独立して管理できます。

        Args:
            dfs (Dict[str, DataFrame]): CSVタイプをキーとするDataFrameの辞書
            files (Dict[str, UploadFile]): アップロードされたファイルの辞書

        Returns:
            ErrorApiResponse | None: エラーがある場合はエラーレスポンス、正常時はNone
        """
        # 期待されるヘッダー情報を各CSVタイプから取得
        required_columns = {
            k: self.config_loader.get_expected_headers(k) for k in files.keys()
        }

        # 純粋なバリデーター初期化
        validator = PureCSVValidator(required_columns)

        # バリデーション実行（純粋なロジック）
        validation_result = validator.validate_all(dfs, files)

        # バリデーション結果をAPIレスポンス形式に変換
        api_response = self.response_converter.convert_to_api_response(
            validation_result, files
        )

        return api_response
