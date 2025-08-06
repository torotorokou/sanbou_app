"""
CSVバリデーターファサードサービス

CSVファイルのバリデーション処理を統合的に管理するファサードクラスです。
複数のバリデーション処理を順次実行し、エラーがあればレスポンスを返します。
"""

from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.src.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)
from backend_shared.src.api_response.response_base import ErrorApiResponse


class CsvValidatorService:
    """
    CSVバリデーションサービス

    CSVファイルの各種バリデーション処理を統合的に実行するサービスクラスです。
    カラム存在チェック、伝票日付の存在・一致チェックなどを順次実行します。
    """

    def __init__(self):
        """
        サービスの初期化

        設定ローダーを初期化し、バリデーション処理の準備を行います。
        """
        # 昇軍CSV設定ローダーの初期化
        self.config_loader = SyogunCsvConfigLoader()

    def validate(self, dfs, files) -> ErrorApiResponse | None:
        """
        CSVファイルの包括的バリデーション

        複数のバリデーション処理を順次実行し、最初に検出されたエラーを返します。
        すべてのバリデーションが成功した場合はNoneを返します。

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

        # バリデーター初期化
        validator = CSVValidationResponder(required_columns)

        # 1. カラム存在バリデーション
        error_response = validator.validate_columns(dfs, files)
        if error_response:
            return error_response

        # 2. 伝票日付存在チェック
        error_response = validator.validate_denpyou_date_exists(dfs, files)
        if error_response:
            return error_response

        # 3. 伝票日付一致チェック（複数ファイル間での整合性確認）
        error_response = validator.validate_denpyou_date_consistency(dfs)
        if error_response:
            return error_response

        # すべてのバリデーション成功
        return None
