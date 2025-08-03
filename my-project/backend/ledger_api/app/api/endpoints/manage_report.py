import os
import pandas as pd
import urllib.parse
from fastapi import APIRouter, UploadFile, Form, File
from fastapi.responses import StreamingResponse, JSONResponse

from backend_shared.src.response_utils import api_response
from backend_shared.config.config_loader import (
    SyogunCsvConfigLoader,
    ReportTemplateConfigLoader,
)
from backend_shared.src.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)
from backend_shared.src.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.src.csv_formatter.formatter_config import build_formatter_config
from app.api.services.report_generator import get_report_generator
from backend_shared.src.report_checker.check_csv_files import check_csv_files
from app.local_config.paths import MANAGE_REPORT_OUTPUT_DIR
from backend_shared.src.response_utils import api_response

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGE_REPORT_DIR = os.path.join(BASE_DIR, "static", "manage_report")
os.makedirs(MANAGE_REPORT_DIR, exist_ok=True)


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    try:
        print(f"API called with report_key={report_key}")

        files = {
            k: v
            for k, v in {
                "shipment": shipment,
                "yard": yard,
                "receive": receive,
            }.items()
            if v is not None
        }
        print(f"Uploaded files: {list(files.keys())}")

        if not files:
            print("No files uploaded.")
            return api_response(
                status_code=422,
                status_str="error",
                code="no_files",
                detail="ファイルが1つもアップロードされていません。",
                hint="3つすべてのCSVをアップロードしてください。",
            )

        # データフレーム化
        dfs = {}
        for k, f in files.items():
            try:
                print(f"Reading CSV file for {k}")
                f.file.seek(0)
                dfs[k] = pd.read_csv(f.file)
                f.file.seek(0)
                print(f"Read CSV for {k}: shape={dfs[k].shape}")
            except Exception as e:
                print(f"Error reading CSV for {k}: {e}")
                return api_response(
                    status_code=422,
                    status_str="error",
                    code="csv_read_error",
                    detail=f"{k} のCSV読み込みに失敗しました: {str(e)}",
                    hint=f"{k}ファイルが正しいCSV形式か確認してください。",
                )

        # バリデーション
        config_loader = SyogunCsvConfigLoader()
        required_columns = {
            k: config_loader.get_expected_headers(k) for k in files.keys()
        }
        validator = CSVValidationResponder(required_columns)

        print("Validating columns...")
        res = validator.validate_columns(dfs, files)
        if res:
            print(f"Column validation error: {res}")
            return api_response(
                status_code=422,
                status_str="error",
                code="column_validation_error",
                detail=res.get("detail", "カラムバリデーションに失敗しました"),
                result=res.get("result"),
                hint=res.get("hint"),
            )

        print("Validating denpyou_date exists...")
        res = validator.validate_denpyou_date_exists(dfs, files)
        if res:
            print(f"Denpyou_date missing error: {res}")
            return api_response(
                status_code=422,
                status_str="error",
                code="date_missing",
                detail=res.get("detail", "伝票日付が見つかりませんでした"),
                result=res.get("result"),
                hint=res.get("hint"),
            )

        print("Validating denpyou_date consistency...")
        res = validator.validate_denpyou_date_consistency(dfs)
        if res:
            print(f"Denpyou_date inconsistency error: {res}")
            return api_response(
                status_code=422,
                status_str="error",
                code="date_inconsistent",
                detail=res.get("detail", "伝票日付に不一致があります"),
                result=res.get("result"),
                hint=res.get("hint"),
            )

        # フォーマット変換
        print("Formatting DataFrames...")
        loader = SyogunCsvConfigLoader()
        df_formatted = {}
        for csv_type, df in dfs.items():
            try:
                config = build_formatter_config(loader, csv_type)
                formatter = CSVFormatterFactory.get_formatter(csv_type, config)
                df_formatted[csv_type] = formatter.format(df)
                print(f"Formatted {csv_type}: shape={df_formatted[csv_type].shape}")
            except Exception as e:
                print(f"Error formatting {csv_type}: {e}")
                raise

        # 帳票生成
        try:
            print("Preparing report generator...")
            output_dir = os.path.join(MANAGE_REPORT_OUTPUT_DIR, report_key)
            generator = get_report_generator(report_key, output_dir, df_formatted)

            print("Running preprocess...")
            generator.preprocess(report_key)

            print("Running main_process...")
            df_result = generator.main_process(report_key)

            print("Making report date...")
            report_date = generator.make_report_date(df_formatted)
        except Exception as e:
            print(f"Error in report generation (preprocess/main_process): {e}")
            raise

        # エクセル出力
        try:
            print("Generating Excel bytes...")
            excel_bytes_io = generator.generate_excel_bytes(df_result, report_date)
            excel_bytes_io.seek(0)
        except Exception as e:
            print(f"Error in generate_excel_bytes: {e}")
            raise

        # ファイル名設定
        manage_config = ReportTemplateConfigLoader()
        label_jp = manage_config.get_label(report_key)
        file_name = f"{label_jp}_{report_date}.xlsx"
        quoted_file_name = urllib.parse.quote(file_name)
        content_disposition = f"attachment; filename*=UTF-8''{quoted_file_name}"

        print(f"Returning StreamingResponse: {file_name}")
        return StreamingResponse(
            excel_bytes_io,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": content_disposition},
        )
    except Exception as e:
        print(f"[ERROR] Unhandled Exception in /report/manage: {e}")
        return api_response(
            status_code=500,
            status_str="error",
            code="internal_error",
            detail=f"サーバー内部でエラーが発生しました: {str(e)}",
            hint="管理者に連絡してください。",
        )
