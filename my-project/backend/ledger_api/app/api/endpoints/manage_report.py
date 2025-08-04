import os
import pandas as pd
from backend_shared.src.utils.csv_reader import SafeCsvReader
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

        import io
        import zipfile
        from tempfile import NamedTemporaryFile
        # LibreOffice + unoconv でPDF変換

        # エクセル出力
        try:
            print("Generating Excel bytes...")
            excel_bytes_io = generator.generate_excel_bytes(df_result, report_date)
            excel_bytes_io.seek(0)
        except Exception as e:
            print(f"Error in generate_excel_bytes: {e}")
            raise

        # 一時ファイルにエクセルを書き出し、LibreOffice+unoconvでPDF変換
        try:
            with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_xlsx:
                tmp_xlsx.write(excel_bytes_io.read())
                tmp_xlsx.flush()
                xlsx_path = tmp_xlsx.name

            with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                pdf_path = tmp_pdf.name

            # LibreOffice + unoconv でPDF変換
            import subprocess

            convert_cmd = ["unoconv", "-f", "pdf", "-o", pdf_path, xlsx_path]
            try:
                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[ERROR] unoconv failed: {result.stderr}")
                    raise RuntimeError(f"unoconv failed: {result.stderr}")
                else:
                    print(f"[DEBUG] unoconv succeeded: {pdf_path}")
            except Exception as e:
                print(f"[ERROR] LibreOffice+unoconv PDF変換失敗: {e}")
                raise

            # バイトデータとして読み込み
            with open(xlsx_path, "rb") as f:
                excel_bytes = f.read()
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # ファイル名設定
            manage_config = ReportTemplateConfigLoader()
            label_jp = manage_config.get_label(report_key)
            file_base = f"{label_jp}_{report_date}"
            excel_name = f"{file_base}.xlsx"
            pdf_name = f"{file_base}.pdf"
            zip_name = f"{file_base}.zip"

            # zip作成
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                zip_file.writestr(excel_name, excel_bytes)
                zip_file.writestr(pdf_name, pdf_bytes)

            # デバッグ用: ローカルにもPDFを保存
            debug_pdf_path = os.path.join(MANAGE_REPORT_DIR, pdf_name)
            try:
                with open(debug_pdf_path, "wb") as f:
                    f.write(pdf_bytes)
                print(f"[DEBUG] PDF saved locally: {debug_pdf_path}")
            except Exception as e:
                print(f"[DEBUG] Failed to save PDF locally: {e}")
            zip_buffer.seek(0)

            content_disposition = (
                f"attachment; filename*=UTF-8''{urllib.parse.quote(zip_name)}"
            )
            print(f"Returning StreamingResponse: {zip_name}")
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": content_disposition},
            )
        except Exception as e:
            print(f"Error in Excel/PDF/ZIP conversion: {e}")
            return api_response(
                status_code=500,
                status_str="error",
                code="zip_conversion_error",
                detail=f"Excel/PDF/ZIP変換に失敗しました: {str(e)}",
                hint="管理者に連絡してください。",
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
