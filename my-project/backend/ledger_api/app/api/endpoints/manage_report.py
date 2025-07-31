import os
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, File, HTTPException
from backend_shared.src.response_utils import api_response

# from __archive__.manage_report_service import ManageReportService
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

from app.local_config.paths import MANAGE_REPORT_OUTPUT_DIR, MANAGE_REPORT_URL_BASE

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
    files = {
        k: v
        for k, v in {
            "shipment": shipment,
            "yard": yard,
            "receive": receive,
        }.items()
        if v is not None
    }

    # データフレーム化
    dfs = {}
    for k, f in files.items():
        f.file.seek(0)
        dfs[k] = pd.read_csv(f.file)
        f.file.seek(0)

    # CSVバリデーション・日付・カラムチェック
    config_loader = SyogunCsvConfigLoader()
    required_columns = {k: config_loader.get_expected_headers(k) for k in files.keys()}

    validator = CSVValidationResponder(required_columns)
    res = validator.validate_columns(dfs, files)
    if res:
        return res

    res = validator.validate_denpyou_date_exists(dfs, files)
    if res:
        return res

    res = validator.validate_denpyou_date_consistency(dfs)
    if res:
        return res

    # フォーマット
    loader = SyogunCsvConfigLoader()
    df_formatted = {}
    for csv_type, df in dfs.items():
        config = build_formatter_config(
            loader, csv_type
        )  # カラム定義・型変換・リネーム情報など

        # DataFrameがdfにある前提
        formatter = CSVFormatterFactory.get_formatter(csv_type, config)
        df_formatted[csv_type] = formatter.format(df)

    # 個別処理
    # dfは修正後のDataFrameにすること
    output_dir = os.path.join(MANAGE_REPORT_OUTPUT_DIR, report_key)
    generator = get_report_generator(report_key, output_dir, df_formatted)

    # 前処理：必要なファイルチェック
    generator.preprocess(report_key)  # Base（共通） or サブクラスのどちらか

    # 各帳票生成
    generator.main_process()

    # PDFとExcelの生成
    excel_name = generator.generate_excel("file.xlsx")  # Base（共通）
    pdf_name = generator.generate_pdf("file.pdf")  # Base（共通）

    # download_pdf_name = generator.get_download_pdf_name(report_name_jp, date_str)
    # download_excel_name = generator.get_download_excel_name(report_name_jp, date_str)

    # APIレスポンス
    MANAGE_REPORT_URL_BASE
    url_base = f"{MANAGE_REPORT_URL_BASE}/{report_key}"
    return api_response(
        status_code=200,
        status_str="success",
        code="REPORT_CREATED",
        detail=f"{report_key}帳簿が作成されました。",
        result={
            "pdf_url": f"{url_base}/{pdf_name}",
            "excel_url": f"{url_base}/{excel_name}",
            "download_pdf_name": pdf_name,
            "download_excel_name": excel_name,
        },
    )
