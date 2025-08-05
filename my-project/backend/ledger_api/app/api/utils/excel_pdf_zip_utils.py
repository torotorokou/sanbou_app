import subprocess
from tempfile import NamedTemporaryFile
import io
import zipfile
import os
import urllib.parse
from fastapi.responses import StreamingResponse
from backend_shared.config.config_loader import ReportTemplateConfigLoader
from app.local_config.paths import DEBUG_MANAGE_REPORTDIR


def create_excel_bytes(generator, df_result, report_date):
    """generatorからExcelバイトデータを生成して返す"""
    print("Generating Excel bytes...")
    excel_bytes_io = generator.generate_excel_bytes(df_result, report_date)
    excel_bytes_io.seek(0)
    return excel_bytes_io.read()


def convert_excel_to_pdf(excel_bytes):
    """Excelバイトデータを一時ファイルに書き出し、unoconvでPDF変換し、PDFバイトデータを返す"""
    # Excel一時ファイル作成
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_xlsx:
        tmp_xlsx.write(excel_bytes)
        tmp_xlsx.flush()
        xlsx_path = tmp_xlsx.name
    # PDF一時ファイル作成
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name
    # unoconvで変換
    convert_cmd = ["unoconv", "-f", "pdf", "-o", pdf_path, xlsx_path]
    result = subprocess.run(convert_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] unoconv failed: {result.stderr}")
        raise RuntimeError(f"unoconv failed: {result.stderr}")
    else:
        print(f"[DEBUG] unoconv succeeded: {pdf_path}")
    # PDFバイトデータ取得
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    return pdf_bytes, xlsx_path, pdf_path


def create_zip_with_excel_and_pdf(excel_bytes, pdf_bytes, report_key, report_date):
    """Excel/PDFバイトデータをZIPにまとめて返す（バイトIO）"""
    manage_config = ReportTemplateConfigLoader()
    label_jp = manage_config.get_label(report_key)
    file_base = f"{label_jp}_{report_date}"
    excel_name = f"{file_base}.xlsx"
    pdf_name = f"{file_base}.pdf"
    zip_name = f"{file_base}.zip"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr(excel_name, excel_bytes)
        zip_file.writestr(pdf_name, pdf_bytes)

    # デバッグ用: ローカルにもPDFを保存
    debug_pdf_path = os.path.join(DEBUG_MANAGE_REPORTDIR, pdf_name)
    try:
        with open(debug_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"[DEBUG] PDF saved locally: {debug_pdf_path}")
    except Exception as e:
        print(f"[DEBUG] Failed to save PDF locally: {e}")
    zip_buffer.seek(0)

    content_disposition = f"attachment; filename*=UTF-8''{urllib.parse.quote(zip_name)}"
    return zip_buffer, content_disposition


def generate_excel_pdf_zip(excel_bytes, report_key, report_date):
    """
    Excelバイトデータを受け取り、PDF変換・ZIP圧縮・StreamingResponse返却までをまとめたラッパー関数
    """
    pdf_bytes, _, _ = convert_excel_to_pdf(excel_bytes)
    zip_buffer, content_disposition = create_zip_with_excel_and_pdf(
        excel_bytes, pdf_bytes, report_key, report_date
    )
    print(f"Returning StreamingResponse: {content_disposition}")
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": content_disposition},
    )
