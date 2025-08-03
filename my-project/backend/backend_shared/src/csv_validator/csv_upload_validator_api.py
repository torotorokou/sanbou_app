# --- import ---
from fastapi import UploadFile, status
from backend_shared.src.csv_formatter.dataframe import serialize_dates_info
from backend_shared.src.utils.dataframe_validator import (
    check_missing_file,
    check_required_columns,
    check_denpyou_date_exists,
    check_denpyou_date_consistency,
)


class CSVValidationResponder:
    """
    FastAPI応答用のCSVバリデーション処理クラス（レスポンスはdict型のみ返す）。
    実際のロジックは外部のvalidator関数へ委譲し、エラー時はエラー情報をdictで返却する。
    APIレスポンス(JSONResponse)はコントローラ側でラップする。
    """

    def __init__(self, required_columns: dict):
        self.required_columns = required_columns

    def check_missing_file(self, file_inputs: dict[str, UploadFile]) -> str | None:
        """
        アップロードされていないファイルがあるかをチェック。
        :return: 欠けているcsv_type（NoneならOK）
        """
        return check_missing_file(file_inputs)

    def validate_columns(
        self,
        dfs: dict[str, object],
        file_inputs: dict[str, UploadFile],
    ):
        """
        必須カラムが揃っているかをチェック。エラー時はエラー情報のdictを返す。
        """
        ok, csv_type, missing = check_required_columns(dfs, self.required_columns)
        if not ok:
            file = file_inputs[csv_type]
            return {
                "code": "MISSING_COLUMNS",
                "detail": f"{csv_type}ファイルの必須カラムが不足しています: {missing}",
                "result": {
                    csv_type: {
                        "filename": file.filename,
                        "columns": dfs[csv_type].columns.tolist(),
                        "status": "error",
                        "code": "MISSING_COLUMNS",
                        "detail": f"必須カラムが不足しています: {missing}",
                    }
                },
            }
        return None

    def validate_denpyou_date_exists(
        self,
        dfs: dict[str, object],
        file_inputs: dict[str, UploadFile],
    ):
        """
        「伝票日付」カラムの存在をチェック。エラー時はエラー情報のdictを返す。
        """
        missing_type = check_denpyou_date_exists(dfs)
        if missing_type:
            return {
                "code": "MISSING_DATE_FIELD",
                "detail": f"{missing_type}ファイルに『伝票日付』カラムがありません。",
                "result": {
                    missing_type: {
                        "filename": file_inputs[missing_type].filename,
                        "columns": dfs[missing_type].columns.tolist(),
                        "status": "error",
                        "code": "MISSING_DATE_FIELD",
                        "detail": "『伝票日付』カラムがありません",
                    }
                },
            }
        return None

    def validate_denpyou_date_consistency(self, dfs: dict[str, object]):
        """
        すべてのファイルの「伝票日付」が一致しているかをチェック。
        エラー時はエラー情報のdictを返す。
        """
        ok, info = check_denpyou_date_consistency(dfs)
        if not ok:
            return {
                "code": "DATE_MISMATCH",
                "detail": "伝票日付が一致しません。",
                "hint": "すべてのファイルの「伝票日付」が同じ範囲になっているか確認してください。",
                "result": {"dates": serialize_dates_info(info)},
            }
        return None
