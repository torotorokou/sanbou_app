"""
CSVバリデーション結果クラス

バリデーション処理の結果を格納する値オブジェクトです。
APIレスポンスとは独立した、純粋なバリデーション結果を表現します。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationErrorType(Enum):
    """バリデーションエラーの種類"""

    MISSING_FILE = "missing_file"
    MISSING_COLUMNS = "missing_columns"
    MISSING_DATE_FIELD = "missing_date_field"
    DATE_MISMATCH = "date_mismatch"


@dataclass
class ValidationError:
    """
    個別のバリデーションエラー

    APIレスポンス形式に依存しない、純粋なエラー情報を保持します。
    """

    error_type: ValidationErrorType
    csv_type: str | None = None
    message: str = ""
    details: dict[str, Any] | None = None


@dataclass
class ValidationResult:
    """
    バリデーション結果

    成功/失敗の状態と、失敗時のエラー情報を保持します。
    APIレスポンス形式には依存しません。
    """

    is_valid: bool
    errors: list[ValidationError]

    @classmethod
    def success(cls) -> "ValidationResult":
        """成功結果を作成"""
        return cls(is_valid=True, errors=[])

    @classmethod
    def failure(cls, errors: list[ValidationError]) -> "ValidationResult":
        """失敗結果を作成"""
        return cls(is_valid=False, errors=errors)

    @classmethod
    def single_error(cls, error: ValidationError) -> "ValidationResult":
        """単一エラーの失敗結果を作成"""
        return cls(is_valid=False, errors=[error])
