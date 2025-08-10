"""
Excel・PDF・ZIP処理ユーティリティ

Excel生成、PDF変換、ZIP圧縮、ファイルダウンロードレスポンス生成までの
一連の処理を行うユーティリティ関数群です。
"""

import io
import os
import subprocess
import urllib.parse
import zipfile
from tempfile import NamedTemporaryFile

from fastapi.responses import StreamingResponse

from app.local_config.paths import DEBUG_MANAGE_REPORTDIR
from backend_shared.config.config_loader import ReportTemplateConfigLoader


def create_excel_bytes(generator, df_result, report_date):
    """
    帳票生成器からExcelバイトデータを生成

    Args:
        generator: 帳票生成器インスタンス
        df_result: 処理済みDataFrame
        report_date: 帳票日付

    Returns:
        bytes: Excelファイルのバイトデータ
    """
    print("Generating Excel bytes...")
    # 生成器からExcelバイトストリームを取得
    excel_bytes_io = generator.generate_excel_bytes(df_result, report_date)
    # 返却の統一: BytesIO で返ってきた場合は bytes に正規化
    if isinstance(excel_bytes_io, io.BytesIO):
        excel_bytes_io.seek(0)
        data = excel_bytes_io.read()
        print(
            f"[DEBUG] create_excel_bytes received BytesIO, normalized to bytes, len={len(data)}"
        )
        return data
    # 既に bytes の場合はそのまま返却
    if isinstance(excel_bytes_io, (bytes, bytearray)):
        data = bytes(excel_bytes_io)
        print(f"[DEBUG] create_excel_bytes received bytes-like, len={len(data)}")
        return data
    # 想定外型: 文字列などは encode せず例外とする
    raise TypeError(
        f"Unsupported type from generator.generate_excel_bytes: {type(excel_bytes_io)}"
    )


def convert_excel_to_pdf(excel_bytes):
    """
    ExcelバイトデータをPDFに変換

    unoconvコマンドを使用してExcelファイルをPDFに変換します。

    Args:
        excel_bytes (bytes): Excelファイルのバイトデータ

    Returns:
        tuple: (PDFバイトデータ, Excelファイルパス, PDFファイルパス)

    Raises:
        RuntimeError: PDF変換に失敗した場合
    """
    # 入口正規化（冪等）
    print(f"[DEBUG] convert_excel_to_pdf input type: {type(excel_bytes)}")
    if isinstance(excel_bytes, io.BytesIO):
        excel_bytes = excel_bytes.getvalue()
        print(
            f"[DEBUG] convert_excel_to_pdf normalized BytesIO to bytes, len={len(excel_bytes)}"
        )
    elif isinstance(excel_bytes, bytearray):
        excel_bytes = bytes(excel_bytes)
        print(
            f"[DEBUG] convert_excel_to_pdf normalized bytearray to bytes, len={len(excel_bytes)}"
        )
    elif not isinstance(excel_bytes, (bytes,)):
        raise TypeError(
            f"excel_bytes must be bytes or BytesIO, got {type(excel_bytes)}"
        )

    # Excel一時ファイル作成
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_xlsx:
        tmp_xlsx.write(excel_bytes)
        tmp_xlsx.flush()
        xlsx_path = tmp_xlsx.name

    # PDF一時ファイル作成
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    # unoconvコマンドでExcel→PDF変換実行
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
    """
    Excel・PDFファイルをZIP圧縮

    Args:
        excel_bytes (bytes): Excelファイルのバイトデータ
        pdf_bytes (bytes): PDFファイルのバイトデータ
        report_key (str): 帳票タイプキー
        report_date (str): 帳票日付

    Returns:
        tuple: (ZIPバイトストリーム, Content-Dispositionヘッダー値)
    """
    # 設定から日本語ラベルを取得
    manage_config = ReportTemplateConfigLoader()
    label_jp = manage_config.get_label(report_key)

    # ファイル名の構築
    file_base = f"{label_jp}_{report_date}"
    excel_name = f"{file_base}.xlsx"
    pdf_name = f"{file_base}.pdf"
    zip_name = f"{file_base}.zip"

    # ZIPファイル作成
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

    # ダウンロード用ヘッダー作成（日本語ファイル名対応）
    content_disposition = f"attachment; filename*=UTF-8''{urllib.parse.quote(zip_name)}"
    return zip_buffer, content_disposition


def generate_excel_pdf_zip(excel_bytes, report_key, report_date):
    """
    Excel→PDF変換→ZIP圧縮→ダウンロードレスポンス生成

    Excelバイトデータを受け取り、PDF変換・ZIP圧縮・StreamingResponse返却までの
    一連の処理をまとめて実行するラッパー関数です。

    Args:
        excel_bytes (bytes): Excelファイルのバイトデータ
        report_key (str): 帳票タイプキー
        report_date (str): 帳票日付

    Returns:
        StreamingResponse: ZIPファイルのダウンロードレスポンス
    """
    # 入口正規化（冪等）
    print(f"[DEBUG] generate_excel_pdf_zip input type: {type(excel_bytes)}")
    if isinstance(excel_bytes, io.BytesIO):
        excel_bytes = excel_bytes.getvalue()
        print(
            f"[DEBUG] generate_excel_pdf_zip normalized BytesIO to bytes, len={len(excel_bytes)}"
        )
    elif isinstance(excel_bytes, bytearray):
        excel_bytes = bytes(excel_bytes)
        print(
            f"[DEBUG] generate_excel_pdf_zip normalized bytearray to bytes, len={len(excel_bytes)}"
        )
    elif not isinstance(excel_bytes, (bytes,)):
        raise TypeError(
            f"excel_bytes must be bytes or BytesIO, got {type(excel_bytes)}"
        )

    # Excel→PDF変換
    pdf_bytes, _, _ = convert_excel_to_pdf(excel_bytes)

    # ZIP圧縮
    zip_buffer, content_disposition = create_zip_with_excel_and_pdf(
        excel_bytes, pdf_bytes, report_key, report_date
    )

    print(f"Returning StreamingResponse: {content_disposition}")

    # ストリーミングレスポンス返却
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": content_disposition},
    )
