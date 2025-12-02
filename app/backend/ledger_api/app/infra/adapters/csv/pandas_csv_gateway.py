"""
Pandas CSV Gateway (pandas を使った CSV 読み込み実装).

👶 このクラスは CsvGateway Port の具体的な実装です。
既存の backend_shared.utils.csv_reader と services/csv を活用します。
"""

import logging
import time
from typing import Any, Dict, Optional

from fastapi import UploadFile

from app.core.ports.inbound import CsvGateway
from backend_shared.application.logging import get_module_logger, create_log_context
from backend_shared.utils.csv_reader import read_csv_files
from backend_shared.infra.adapters.presentation.response_error import (
    NoFilesUploadedResponse,
    CSVReadErrorResponse,
)
from app.infra.adapters.csv.validator_service import CsvValidatorService
from app.infra.adapters.csv.formatter_service import CsvFormatterService

logger = get_module_logger(__name__)


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
        start_time = time.time()
        file_keys = list(files.keys())
        
        logger.info(
            "CSV読み込み開始",
            extra={
                "operation": "read_csv_files",
                "file_count": len(files),
                "file_keys": file_keys,
            },
        )

        try:
            if not files:
                logger.warning("アップロードファイルが空")
                return None, NoFilesUploadedResponse()

            dfs, error = read_csv_files(files)
            
            elapsed = time.time() - start_time
            
            if error:
                logger.error(
                    "CSV読み込みエラー",
                    extra={
                        "operation": "read_csv_files",
                        "file_keys": file_keys,
                        "elapsed_seconds": round(elapsed, 3),
                        "error_type": type(error).__name__,
                    },
                )
                return None, error

            # 成功時のメトリクス
            if dfs:
                row_counts = {key: len(df) for key, df in dfs.items()}
                logger.info(
                    "CSV読み込み完了",
                    extra={
                        "operation": "read_csv_files",
                        "file_keys": file_keys,
                        "row_counts": row_counts,
                        "elapsed_seconds": round(elapsed, 3),
                    },
                )
            
            return dfs, None
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(
                "CSV読み込み中に予期しないエラー",
                extra={
                    "operation": "read_csv_files",
                    "file_keys": file_keys,
                    "elapsed_seconds": round(elapsed, 3),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
            )
            # 既存のエラーレスポンス形式を維持
            return None, CSVReadErrorResponse(
                file_name="uploaded_files",
                exception=e
            )

    def validate_csv_structure(
        self, dfs: Dict[str, Any], file_inputs: Dict[str, Any]
    ) -> Optional[Any]:
        """
        CSV の構造検証.

        既存の CsvValidatorService を利用します。
        """
        start_time = time.time()
        file_keys = list(dfs.keys())
        
        logger.info(
            "CSV構造検証開始",
            extra={
                "operation": "validate_csv_structure",
                "file_keys": file_keys,
            },
        )

        try:
            error = self._validator.validate(dfs, file_inputs)
            elapsed = time.time() - start_time
            
            if error:
                logger.warning(
                    "CSV構造検証失敗",
                    extra={
                        "operation": "validate_csv_structure",
                        "file_keys": file_keys,
                        "elapsed_seconds": round(elapsed, 3),
                        "validation_error": True,
                    },
                )
            else:
                logger.info(
                    "CSV構造検証成功",
                    extra={
                        "operation": "validate_csv_structure",
                        "file_keys": file_keys,
                        "elapsed_seconds": round(elapsed, 3),
                    },
                )
            
            return error
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(
                "CSV構造検証中に予期しないエラー",
                extra={
                    "operation": "validate_csv_structure",
                    "file_keys": file_keys,
                    "elapsed_seconds": round(elapsed, 3),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
            )
            # バリデーションエラーとして扱う
            return CSVReadErrorResponse(
                file_name="validation",
                exception=e
            )

    def format_csv_data(self, dfs: Dict[str, Any]) -> Dict[str, Any]:
        """
        CSV データの整形.

        既存の CsvFormatterService を利用します。
        """
        start_time = time.time()
        file_keys = list(dfs.keys())
        
        logger.info(
            "CSVデータ整形開始",
            extra={
                "operation": "format_csv_data",
                "file_keys": file_keys,
            },
        )

        try:
            formatted_dfs = self._formatter.format(dfs)
            elapsed = time.time() - start_time
            
            logger.info(
                "CSVデータ整形完了",
                extra={
                    "operation": "format_csv_data",
                    "file_keys": file_keys,
                    "elapsed_seconds": round(elapsed, 3),
                },
            )
            
            return formatted_dfs
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(
                "CSVデータ整形中に予期しないエラー",
                extra={
                    "operation": "format_csv_data",
                    "file_keys": file_keys,
                    "elapsed_seconds": round(elapsed, 3),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
            )
            # エラー時は再送出（既存の動作を維持）
            raise
