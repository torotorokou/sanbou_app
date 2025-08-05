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

router = APIRouter()


# 管理帳票のreport_key
# factory_report
# balance_sheet
# average_sheet
# block_unit_price
# management_sheet
# balance_management_table


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    # ここにtryは不要
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

    # データフレーム化（SafeCsvReaderを利用）
    dfs = {}
    csv_reader = SafeCsvReader()
    for k, f in files.items():
        try:
            print(f"[DEBUG] Reading CSV file for {k}")
            f.file.seek(0)
            dfs[k] = csv_reader.read(f.file)
            f.file.seek(0)
            print(f"[DEBUG] Read CSV for {k}: shape={dfs[k].shape}")
            print(f"[DEBUG] {k} columns: {dfs[k].columns.tolist()}")
            print(f"[DEBUG] {k} head:\n{dfs[k].head()}\n")
        except Exception as e:
            print(f"[ERROR] reading CSV for {k}: {e}")
            return api_response(
                status_code=422,
                status_str="error",
                code="csv_read_error",
                detail=f"{k} のCSV読み込みに失敗しました: {str(e)}",
                hint=f"{k}ファイルが正しいCSV形式か確認してください。",
            )

    # バリデーション
    config_loader = SyogunCsvConfigLoader()
    required_columns = {k: config_loader.get_expected_headers(k) for k in files.keys()}
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
