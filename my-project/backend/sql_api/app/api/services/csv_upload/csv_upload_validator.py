# --- import ---
from fastapi import UploadFile, status
from app.api.utils.response_utils import api_response
from app.api.utils.dataframe import serialize_dates_info
from backend_shared.utils.dataframe_validator import (
    check_missing_file,
    check_required_columns,
    check_denpyou_date_exists,
    check_denpyou_date_consistency,
)


class CSVValidationResponder:
    """
    FastAPI 応答付きの CSV バリデーション処理を提供するクラス。
    ロジックは関数ベースの csv_validators に委譲し、
    このクラスは API エラーレスポンス生成のみを担う。
    """

    def __init__(self, required_columns: dict):
        self.required_columns = required_columns

    def check_missing_file(self, file_inputs: dict[str, UploadFile]) -> str | None:
        """
        アップロードされていないファイルがあるかをチェック。
        :return: 欠けている csv_type（None ならOK）
        """
        return check_missing_file(file_inputs)

    def validate_columns(
        self,
        dfs: dict[str, object],
        file_inputs: dict[str, UploadFile],
    ):
        """
        必須カラムが揃っているかをチェックし、揃っていなければエラー応答を返す。
        """
        ok, csv_type, missing = check_required_columns(dfs, self.required_columns)
        if not ok:
            file = file_inputs[csv_type]
            return api_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                status_str="error",
                code="MISSING_COLUMNS",
                detail=f"{csv_type}ファイルの必須カラムが不足しています: {missing}",
                result={
                    csv_type: {
                        "filename": file.filename,
                        "columns": dfs[csv_type].columns.tolist(),
                        "status": "error",
                        "code": "MISSING_COLUMNS",
                        "detail": f"必須カラムが不足しています: {missing}",
                    }
                },
            )
        return None

    def validate_denpyou_date_exists(
        self,
        dfs: dict[str, object],
        file_inputs: dict[str, UploadFile],
    ):
        """
        「伝票日付」カラムの存在をチェックし、なければエラー応答を返す。
        """
        missing_type = check_denpyou_date_exists(dfs)
        if missing_type:
            return api_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                status_str="error",
                code="MISSING_DATE_FIELD",
                detail=f"{missing_type}ファイルに『伝票日付』カラムがありません。",
                result={
                    missing_type: {
                        "filename": file_inputs[missing_type].filename,
                        "columns": dfs[missing_type].columns.tolist(),
                        "status": "error",
                        "code": "MISSING_DATE_FIELD",
                        "detail": "『伝票日付』カラムがありません",
                    }
                },
            )
        return None

    def validate_denpyou_date_consistency(self, dfs: dict[str, object]):
        """
        すべてのファイルの「伝票日付」が一致しているかをチェック。
        一致していなければエラー応答を返す。
        """
        ok, info = check_denpyou_date_consistency(dfs)
        if not ok:
            return api_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                status_str="error",
                code="DATE_MISMATCH",
                detail="伝票日付が一致しません。",
                hint="すべてのファイルの「伝票日付」が同じ範囲になっているか確認してください。",
                result={"dates": serialize_dates_info(info)},
            )
        return None
