from backend_shared.src.utils.csv_reader import SafeCsvReader
from fastapi import APIRouter, UploadFile, Form, File
from backend_shared.src.response_utils import api_response
from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.src.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)
from backend_shared.src.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.src.csv_formatter.formatter_config import build_formatter_config
from app.api.services.report.generator_factory import get_report_generator

from app.api.utils.excel_pdf_zip_utils import create_excel_bytes, generate_excel_pdf_zip
from api.services.csv_validator_facade import CsvValidatorService
from app.api.services.csv_formatter_service import CsvFormatterService

router = APIRouter()


# 管理帳票のreport_key
# factory_report
# balance_sheet
# average_sheet
# block_unit_price
# management_sheet
# balance_management_table


def read_csv_files(files: dict) -> tuple[dict, dict | None]:
    csv_reader = SafeCsvReader()
    dfs = {}
    for k, f in files.items():
        try:
            f.file.seek(0)
            dfs[k] = csv_reader.read(f.file)
            f.file.seek(0)
        except Exception as e:
            print(f"[ERROR] reading CSV for {k}: {e}")
            return None, {
                "status_code": 422,
                "status_str": "error",
                "code": "csv_read_error",
                "detail": f"{k} のCSV読み込みに失敗しました: {str(e)}",
                "hint": f"{k}ファイルが正しいCSV形式か確認してください。",
            }
    return dfs, None


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
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

    # 汎用CSV読込
    dfs, error = read_csv_files(files)
    if error:
        return api_response(**error)

    # バリデーション
    validator_service = CsvValidatorService()
    validation_error = validator_service.validate(dfs, files)
    if validation_error:
        print(f"Validation error: {validation_error}")
        return api_response(**validation_error)

    # フォーマット変換
    print("Formatting DataFrames...")
    formatter_service = CsvFormatterService()
    df_formatted = formatter_service.format(dfs)
    for csv_type, df in df_formatted.items():
        print(f"Formatted {csv_type}: shape={df.shape}")

    # 帳票生成
    try:
        print("Preparing report generator...")
        generator = get_report_generator(report_key, df_formatted)
        print("Running preprocess...")
        generator.preprocess(report_key)
        print("Running main_process...")
        df_result = generator.main_process()
        print("Making report date...")
        report_date = generator.make_report_date(df_formatted)
    except Exception as e:
        print(f"Error in report generation (preprocess/main_process): {e}")
        raise

    # エクセル出力
    try:
        excel_bytes = create_excel_bytes(generator, df_result, report_date)
    except Exception as e:
        print(f"Error in create_excel_bytes: {e}")
        raise

    # PDF・ZIP作成・レスポンス返却
    return generate_excel_pdf_zip(excel_bytes, report_key, report_date)
