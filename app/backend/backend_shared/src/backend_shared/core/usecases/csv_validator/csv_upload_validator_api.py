# --- import ---
import pandas as pd
from fastapi import UploadFile

from backend_shared.core.usecases.csv_formatter.dataframe import serialize_dates_info
from backend_shared.infra.adapters.presentation.response_error import (
    DateMismatchResponse,
    MissingColumnsResponse,
    MissingDateFieldResponse,
)
from backend_shared.utils.dataframe_validator import (
    check_denpyou_date_consistency,
    check_denpyou_date_exists,
    check_missing_file,
    check_required_columns,
)


class CSVValidationResponder:
    """
    FastAPI応答用のCSVバリデーション処理クラス（レスポンスはErrorApiResponseインスタンスを返す）。
    実際のロジックは外部のvalidator関数へ委譲し、エラー時はErrorApiResponseサブクラスのインスタンスを返却する。
    """

    def __init__(self, required_columns: dict):
        self.required_columns = required_columns

    def check_missing_file(
        self, file_inputs: dict[str, UploadFile | None]
    ) -> str | None:
        """
        アップロードされていないファイルがあるかをチェック。
        :return: 欠けているcsv_type（NoneならOK）
        """
        # UploadFileはobjectのサブクラスなので、型変換して呼び出し
        return check_missing_file({k: v for k, v in file_inputs.items()})

    def validate_columns(
        self,
        dfs: dict[str, pd.DataFrame],
        file_inputs: dict[str, UploadFile],
    ) -> MissingColumnsResponse | None:
        """
        必須カラムが揃っているかをチェック。エラー時はMissingColumnsResponseを返す。
        """
        ok, csv_type, missing = check_required_columns(dfs, self.required_columns)
        if not ok:
            file = file_inputs[csv_type]
            return MissingColumnsResponse(
                csv_type=csv_type,
                missing_columns=missing,
                file=file,
                df_columns=dfs[csv_type].columns.tolist(),
            )
        return None

    def validate_denpyou_date_exists(
        self,
        dfs: dict[str, pd.DataFrame],
        file_inputs: dict[str, UploadFile],
    ) -> MissingDateFieldResponse | None:
        """
        「伝票日付」カラムの存在をチェック。エラー時はMissingDateFieldResponseを返す。
        """
        missing_type = check_denpyou_date_exists(dfs)
        if missing_type:
            return MissingDateFieldResponse(
                missing_type=missing_type,
                file=file_inputs[missing_type],
                df_columns=dfs[missing_type].columns.tolist(),
            )
        return None

    def validate_denpyou_date_consistency(
        self, dfs: dict[str, pd.DataFrame]
    ) -> DateMismatchResponse | None:
        """
        すべてのファイルの「伝票日付」が一致しているかをチェック。
        エラー時はDateMismatchResponseを返す。
        """
        ok, info = check_denpyou_date_consistency(dfs)
        if not ok:
            return DateMismatchResponse(dates_info=serialize_dates_info(info))
        return None
