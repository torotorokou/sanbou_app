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

from fastapi.responses import StreamingResponse
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
    df_result = generator.main_process(report_key)

    # レポート日付
    report_date = generator.make_report_date(df_formatted)

    # エクセル_pdf生成
    excel_bytes_io = generator.generate_excel_bytes(df_result, report_date)
    excel_bytes_io.seek(0)

    # ファイル名を決める（必要に応じて動的に）
    manage_config = ReportTemplateConfigLoader()
    label_jp = manage_config.get_label(report_key)
    file_name = f"{label_jp}_{report_date}.xlsx"

    # APIレスポンス
    return StreamingResponse(
        excel_bytes_io,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
