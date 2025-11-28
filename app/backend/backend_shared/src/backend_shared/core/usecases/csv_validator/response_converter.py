"""
バリデーション結果からAPIレスポンスへの変換器

バリデーション結果をFastAPI用のレスポンス形式に変換する責務を担います。
バリデーションロジックとAPIレスポンス形式を分離することで、
それぞれの変更が独立して行えるようになります。
"""

from typing import Optional

from fastapi import UploadFile

from backend_shared.infra.adapters.presentation.response_base import ErrorApiResponse
from backend_shared.infra.adapters.presentation.response_error import (
    DateMismatchResponse,
    MissingColumnsResponse,
    MissingDateFieldResponse,
)
from backend_shared.usecases.csv_formatter.dataframe import serialize_dates_info
from backend_shared.usecases.csv_validator.validation_result import (
    ValidationError,
    ValidationErrorType,
    ValidationResult,
)


class ValidationResponseConverter:
    """
    バリデーション結果をAPIレスポンスに変換するコンバーター

    ValidationResult を適切な ErrorApiResponse サブクラスに変換します。
    バリデーションロジックとAPIレスポンス形式の分離を実現します。
    """

    def convert_to_api_response(
        self,
        validation_result: ValidationResult,
        file_inputs: Optional[dict[str, UploadFile]] = None,
    ) -> Optional[ErrorApiResponse]:
        """
        バリデーション結果をAPIレスポンスに変換

        Args:
            validation_result: バリデーション結果
            file_inputs: ファイル入力（一部のレスポンス作成に必要）

        Returns:
            ErrorApiResponse | None: エラーレスポンス（成功時はNone）
        """
        if validation_result.is_valid:
            return None

        # 最初のエラーをAPIレスポンスに変換
        if validation_result.errors:
            first_error = validation_result.errors[0]
            return self._convert_single_error(first_error, file_inputs)

        return None

    def _convert_single_error(
        self,
        error: ValidationError,
        file_inputs: Optional[dict[str, UploadFile]] = None,
    ) -> ErrorApiResponse:
        """
        単一のバリデーションエラーをAPIレスポンスに変換

        Args:
            error: バリデーションエラー
            file_inputs: ファイル入力

        Returns:
            ErrorApiResponse: APIエラーレスポンス
        """
        if error.error_type == ValidationErrorType.MISSING_COLUMNS:
            return self._create_missing_columns_response(error, file_inputs)

        elif error.error_type == ValidationErrorType.MISSING_DATE_FIELD:
            return self._create_missing_date_field_response(error, file_inputs)

        elif error.error_type == ValidationErrorType.DATE_MISMATCH:
            return self._create_date_mismatch_response(error)

        else:
            # デフォルトエラーレスポンス
            return ErrorApiResponse(
                code=error.error_type.value, detail=error.message, result=error.details
            )

    def _create_missing_columns_response(
        self, error: ValidationError, file_inputs: Optional[dict[str, UploadFile]]
    ) -> MissingColumnsResponse:
        """MissingColumnsResponseを作成"""
        details = error.details or {}
        csv_type = error.csv_type or "unknown"  # None の場合のデフォルト値
        missing_columns = details.get("missing_columns", [])

        # ファイル情報を取得
        if file_inputs and error.csv_type and error.csv_type in file_inputs:
            file = file_inputs[error.csv_type]
        else:
            # ファイル情報が取得できない場合のフォールバック
            # 実際の運用では、この状況は避けるべき
            import io

            from fastapi import UploadFile

            file = UploadFile(
                filename=details.get("filename", "unknown.csv"), file=io.BytesIO()
            )

        df_columns = details.get("available_columns", [])

        return MissingColumnsResponse(
            csv_type=csv_type,
            missing_columns=missing_columns,
            file=file,
            df_columns=df_columns,
        )

    def _create_missing_date_field_response(
        self, error: ValidationError, file_inputs: Optional[dict[str, UploadFile]]
    ) -> MissingDateFieldResponse:
        """MissingDateFieldResponseを作成"""
        details = error.details or {}
        missing_type = error.csv_type or "unknown"  # None の場合のデフォルト値

        # ファイル情報を取得
        if file_inputs and error.csv_type and error.csv_type in file_inputs:
            file = file_inputs[error.csv_type]
        else:
            # ファイル情報が取得できない場合のフォールバック
            import io

            from fastapi import UploadFile

            file = UploadFile(
                filename=details.get("filename", "unknown.csv"), file=io.BytesIO()
            )

        df_columns = details.get("available_columns", [])

        return MissingDateFieldResponse(
            missing_type=missing_type,
            file=file,
            df_columns=df_columns,
        )

    def _create_date_mismatch_response(
        self, error: ValidationError
    ) -> DateMismatchResponse:
        """DateMismatchResponseを作成"""
        details = error.details or {}
        dates_info = details.get("dates_info", {})

        # dates_infoを適切な形式にシリアライズ
        serialized_dates_info = serialize_dates_info(dates_info)

        return DateMismatchResponse(dates_info=serialized_dates_info)
