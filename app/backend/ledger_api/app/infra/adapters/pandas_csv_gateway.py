"""
Pandas CSV Gateway (pandas を使った CSV 読み込み実装).

👶 このクラスは CsvGateway Port の具体的な実装です。
既存の backend_shared.utils.csv_reader と services/csv を活用します。
"""

from typing import Any, Dict, Optional

from fastapi import UploadFile

from app.core.ports import CsvGateway
from backend_shared.utils.csv_reader import read_csv_files
from app.api.services.csv import CsvValidatorService, CsvFormatterService


class PandasCsvGateway(CsvGateway):
    """pandas を使った CSV Gateway の実装."""

    def __init__(self):
        """初期化（必要に応じて依存サービスを注入）."""
        self._validator = CsvValidatorService()
        self._formatter = CsvFormatterService()

    def read_csv_files(
        self, files: Dict[str, UploadFile]
    ) -> tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """
        CSV ファイルを pandas DataFrame として読み込む.

        既存の backend_shared の read_csv_files をラップします。
        """
        if not files:
            from backend_shared.adapters.presentation.response_error import (
                NoFilesUploadedResponse,
            )

            return None, NoFilesUploadedResponse()

        dfs, error = read_csv_files(files)
        if error:
            return None, error
        return dfs, None

    def validate_csv_structure(
        self, dfs: Dict[str, Any], file_inputs: Dict[str, Any]
    ) -> Optional[Any]:
        """
        CSV の構造検証.

        既存の CsvValidatorService を利用します。
        """
        return self._validator.validate(dfs, file_inputs)

    def format_csv_data(self, dfs: Dict[str, Any]) -> Dict[str, Any]:
        """
        CSV データの整形.

        既存の CsvFormatterService を利用します。
        """
        return self._formatter.format(dfs)
