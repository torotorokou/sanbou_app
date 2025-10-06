"""
純粋なCSVバリデーター

APIレスポンスに依存しない、純粋なバリデーションロジックを提供します。
バリデーション結果は ValidationResult として返され、レスポンス変換は上位層で行います。
"""

from typing import Dict, List, Optional, Union

import pandas as pd
from fastapi import UploadFile

from backend_shared.csv_validator.validation_result import (
    ValidationError,
    ValidationErrorType,
    ValidationResult,
)
from backend_shared.utils.dataframe_validator import (
    check_denpyou_date_consistency,
    check_denpyou_date_exists,
    check_missing_file,
    check_required_columns,
)


class PureCSVValidator:
    """
    純粋なCSVバリデーター

    APIレスポンス形式に依存しない、純粋なバリデーションロジックを提供します。
    すべてのバリデーション結果は ValidationResult として統一的に返されます。
    """

    def __init__(self, required_columns: Dict[str, List[str]]):
        """
        バリデーターの初期化

        Args:
            required_columns: CSVタイプごとの必須カラムマッピング
        """
        self.required_columns = required_columns

    def validate_missing_files(
        self, file_inputs: Dict[str, Optional[UploadFile]]
    ) -> ValidationResult:
        """
        アップロードされていないファイルがあるかをチェック

        Args:
            file_inputs: ファイル入力の辞書

        Returns:
            ValidationResult: バリデーション結果
        """
        # 型変換して呼び出し
        converted_inputs = {k: v for k, v in file_inputs.items()}
        missing_csv_type = check_missing_file(converted_inputs)

        if missing_csv_type:
            error = ValidationError(
                error_type=ValidationErrorType.MISSING_FILE,
                csv_type=missing_csv_type,
                message=f"{missing_csv_type}ファイルがアップロードされていません。",
                details={"missing_file_type": missing_csv_type},
            )
            return ValidationResult.single_error(error)

        return ValidationResult.success()

    def validate_required_columns(
        self,
        dfs: Dict[str, pd.DataFrame],
        file_inputs: Dict[str, UploadFile],
    ) -> ValidationResult:
        """
        必須カラムが揃っているかをチェック

        Args:
            dfs: DataFrameの辞書
            file_inputs: アップロードファイルの辞書

        Returns:
            ValidationResult: バリデーション結果
        """
        ok, csv_type, missing_columns = check_required_columns(
            dfs, self.required_columns
        )

        if not ok:
            file = file_inputs[csv_type]
            error = ValidationError(
                error_type=ValidationErrorType.MISSING_COLUMNS,
                csv_type=csv_type,
                message=f"{csv_type}ファイルの必須カラムが不足しています: {missing_columns}",
                details={
                    "filename": file.filename,
                    "missing_columns": missing_columns,
                    "available_columns": dfs[csv_type].columns.tolist(),
                },
            )
            return ValidationResult.single_error(error)

        return ValidationResult.success()

    def validate_denpyou_date_exists(
        self,
        dfs: Dict[str, pd.DataFrame],
        file_inputs: Dict[str, UploadFile],
    ) -> ValidationResult:
        """
        「伝票日付」カラムの存在をチェック

        Args:
            dfs: DataFrameの辞書
            file_inputs: アップロードファイルの辞書

        Returns:
            ValidationResult: バリデーション結果
        """
        missing_type = check_denpyou_date_exists(dfs)

        if missing_type:
            file = file_inputs[missing_type]
            error = ValidationError(
                error_type=ValidationErrorType.MISSING_DATE_FIELD,
                csv_type=missing_type,
                message=f"{missing_type}ファイルに『伝票日付』カラムがありません。",
                details={
                    "filename": file.filename,
                    "available_columns": dfs[missing_type].columns.tolist(),
                },
            )
            return ValidationResult.single_error(error)

        return ValidationResult.success()

    def validate_denpyou_date_consistency(
        self, dfs: Dict[str, pd.DataFrame]
    ) -> ValidationResult:
        """
        すべてのファイルの「伝票日付」が一致しているかをチェック

        Args:
            dfs: DataFrameの辞書

        Returns:
            ValidationResult: バリデーション結果
        """
        ok, dates_info = check_denpyou_date_consistency(dfs)

        if not ok:
            error = ValidationError(
                error_type=ValidationErrorType.DATE_MISMATCH,
                message="伝票日付が一致しません。",
                details={"dates_info": dates_info},
            )
            return ValidationResult.single_error(error)

        return ValidationResult.success()

    def validate_all(
        self,
        dfs: Dict[str, pd.DataFrame],
        file_inputs: Dict[str, UploadFile],
    ) -> ValidationResult:
        """
        すべてのバリデーションを実行

        Args:
            dfs: DataFrameの辞書
            file_inputs: アップロードファイルの辞書

        Returns:
            ValidationResult: 統合されたバリデーション結果
        """
        # ファイル入力をOptional型に変換
        optional_file_inputs: Dict[str, Optional[UploadFile]] = {
            k: v for k, v in file_inputs.items()
        }

        # 順次バリデーションを実行し、最初のエラーで停止
        validation_methods = [
            lambda: self.validate_missing_files(optional_file_inputs),
            lambda: self.validate_required_columns(dfs, file_inputs),
            lambda: self.validate_denpyou_date_exists(dfs, file_inputs),
            lambda: self.validate_denpyou_date_consistency(dfs),
        ]

        for validation_method in validation_methods:
            result = validation_method()
            if not result.is_valid:
                return result

        return ValidationResult.success()
