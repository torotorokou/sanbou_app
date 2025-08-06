"""
帳票管理APIエンドポイント

CSVファイルのアップロード、バリデーション、フォーマット変換、
帳票生成、Excel・PDF出力、ZIP圧縮までの一連の処理を行うAPIエンドポイントです。
"""

from fastapi import APIRouter, UploadFile, Form, File
from backend_shared.src.utils.csv_reader import read_csv_files
from app.api.services.report.generator_factory import get_report_generator
from app.api.utils.excel_pdf_zip_utils import create_excel_bytes, generate_excel_pdf_zip
from api.services.csv_validator_facade import CsvValidatorService
from app.api.services.csv_formatter_service import CsvFormatterService

# 統一レスポンスクラス
from src.api_response.response_error import (
    NoFilesUploadedResponse,
)

# APIルーターの初期化
router = APIRouter()


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    """
    帳票生成APIエンドポイント

    CSVファイル（出荷、ヤード、受入）をアップロードし、
    指定された帳票タイプに基づいてExcel・PDFファイルを生成します。

    Args:
        report_key (str): 帳票タイプを識別するキー
        shipment (UploadFile, optional): 出荷データCSVファイル
        yard (UploadFile, optional): ヤードデータCSVファイル
        receive (UploadFile, optional): 受入データCSVファイル

    Returns:
        StreamingResponse: Excel・PDFファイルが含まれたZIPファイル
    """
    # アップロードされたファイルの整理
    files = {
        k: v
        for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
        if v is not None
    }
    print(f"Uploaded files: {list(files.keys())}")

    # ✅ ファイル未アップロードチェック
    if not files:
        print("No files uploaded.")
        return NoFilesUploadedResponse().to_json_response()

    # ✅ CSV読込処理
    dfs, error = read_csv_files(files)
    if error:
        return error.to_json_response()

    # ✅ CSVデータのバリデーション処理
    validator_service = CsvValidatorService()
    validation_error = validator_service.validate(dfs, files)
    if validation_error:
        print(f"Validation error: {validation_error}")
        return validation_error.to_json_response()

    # ✅ データフォーマット変換処理
    print("Formatting DataFrames...")
    formatter_service = CsvFormatterService()
    df_formatted = formatter_service.format(dfs)
    for csv_type, df in df_formatted.items():
        print(f"Formatted {csv_type}: shape={df.shape}")

    # ✅ 帳票生成処理
    try:
        print("Preparing report generator...")
        # 帳票生成器の取得
        generator = get_report_generator(report_key, df_formatted)
        print("Running preprocess...")
        # 前処理の実行
        generator.preprocess(report_key)
        print("Running main_process...")
        # メイン処理の実行
        df_result = generator.main_process()
        print("Making report date...")
        # 帳票日付の生成
        report_date = generator.make_report_date(df_formatted)
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        raise  # 必要に応じて InternalServerErrorResponse を作成してもよい

    # ✅ Excel出力処理
    try:
        excel_bytes = create_excel_bytes(generator, df_result, report_date)
    except Exception as e:
        print(f"[ERROR] Excel export failed: {e}")
        raise

    # ✅ ZIP作成＆レスポンス返却
    return generate_excel_pdf_zip(excel_bytes, report_key, report_date)
