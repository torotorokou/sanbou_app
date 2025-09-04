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



# /backend/app/api/utils/excel_pdf_zip_utils.py

import io
import pathlib
import subprocess
import tempfile
from typing import Optional, Tuple

def convert_excel_to_pdf(excel_bytes: bytes) -> Tuple[Optional[bytes], str, Optional[str]]:
    """
    ExcelバイトデータをPDFに変換（LibreOffice CLI 使用）
    失敗時は例外を投げず、(None, xlsx_path, None) を返す。

    Returns:
        (pdf_bytes or None, temp_xlsx_path, temp_pdf_path or None)
    """
    # 入力正規化
    if isinstance(excel_bytes, io.BytesIO):
        excel_bytes = excel_bytes.getvalue()
    elif isinstance(excel_bytes, bytearray):
        excel_bytes = bytes(excel_bytes)
    elif not isinstance(excel_bytes, (bytes,)):
        raise TypeError(f"excel_bytes must be bytes or BytesIO, got {type(excel_bytes)}")

    with tempfile.TemporaryDirectory() as td:
        td_path = pathlib.Path(td)
        xlsx_path = td_path / "report.xlsx"
        pdf_path  = td_path / "report.pdf"
        xlsx_path.write_bytes(excel_bytes)

        # LibreOfficeプロファイル分離（並列時のロック回避）
        lo_profile = td_path / "lo_profile"
        lo_profile.mkdir(parents=True, exist_ok=True)

        cmd = [
            "soffice",
            "--headless", "--nologo", "--nodefault", "--norestore", "--nolockcheck",
            f"-env:UserInstallation=file://{lo_profile.as_posix()}",
            "--convert-to", "pdf:calc_pdf_Export",
            "--outdir", str(td_path),
            str(xlsx_path),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0 or not pdf_path.exists():
                print(f"[ERROR] PDF変換失敗: {r.stderr or r.stdout}")
                return None, str(xlsx_path), None
        except FileNotFoundError as e:
            # soffice 未インストール
            print("[ERROR] LibreOffice(soffice) が見つかりません。コンテナに libreoffice をインストールしてください。")
            return None, str(xlsx_path), None
        except Exception as e:
            print(f"[ERROR] LibreOffice 実行時例外: {e}")
            return None, str(xlsx_path), None

        pdf_bytes = pdf_path.read_bytes()
        return pdf_bytes, str(xlsx_path), str(pdf_path)

import io, json, zipfile, re
from datetime import datetime, timezone

def _sanitize_filename(s: str) -> str:
    # ヘッダやWindows互換を壊さない程度に簡易サニタイズ
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]+", "_", s)
    s = s.replace(" ", "_")
    return s or "report"

def create_zip_with_excel_and_pdf(excel_bytes: bytes,
                                  pdf_bytes: bytes | None,
                                  report_key: str,
                                  report_date: str):
    """
    Excelは必ず格納、PDFはあれば格納。manifest.json にPDF有無を記録。
    Returns: (BytesIO(zipdata), Content-Disposition header value)
    """
    base = f"{_sanitize_filename(report_key)}_{_sanitize_filename(report_date)}"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # Excel は常に
        z.writestr(f"{base}.xlsx", excel_bytes)

        manifest = {
            "report_key": report_key,
            "report_date": report_date,
            "pdf_generated": bool(pdf_bytes),
            "engine": "libreoffice-cli",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if pdf_bytes:
            z.writestr(f"{base}.pdf", pdf_bytes)
        else:
            # なぜ無いかの汎用的メモ（詳細はサーバーログで確認）
            manifest["reason"] = "conversion_failed_or_soffice_not_found"

        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    buf.seek(0)
    # Content-Disposition（シンプル版）
    content_disposition = f'attachment; filename="{base}.zip"'
    return buf, content_disposition

from starlette.responses import StreamingResponse
import io

def generate_excel_pdf_zip(excel_bytes, report_key, report_date):
    """
    Excel→PDF(任意)→ZIP→StreamingResponse
    - PDF変換に失敗しても Excel は必ず返す
    - レスポンスヘッダ X-Report-Pdf-Generated で有無を伝える
    """
    # 入力正規化
    if isinstance(excel_bytes, io.BytesIO):
        excel_bytes = excel_bytes.getvalue()
    elif isinstance(excel_bytes, bytearray):
        excel_bytes = bytes(excel_bytes)
    elif not isinstance(excel_bytes, (bytes,)):
        raise TypeError(f"excel_bytes must be bytes or BytesIO, got {type(excel_bytes)}")

    # Excel→PDF（失敗しても例外は投げない: (None, _, None)）
    pdf_bytes, _, _ = convert_excel_to_pdf(excel_bytes)
    pdf_generated = pdf_bytes is not None

    # ZIP組み立て（Excelは常に、PDFはあれば）
    zip_buffer, content_disposition = create_zip_with_excel_and_pdf(
        excel_bytes=excel_bytes,
        pdf_bytes=pdf_bytes,               # None 可
        report_key=report_key,
        report_date=report_date,
    )

    headers = {
        "Content-Disposition": content_disposition,
        "X-Report-Pdf-Generated": "true" if pdf_generated else "false",
    }
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
