"""Helpers for converting Excel files into PDF using LibreOffice.

👶 初心者向け解説:
    - LibreOffice (soffice) をコマンドラインから呼び出して PDF を生成します。
    - 変換中の競合を避けるため、リクエストごとに専用のプロファイルディレクトリを作成します。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


class PdfConversionError(RuntimeError):
    """PDF 変換に失敗したときに投げるエラー。"""


def _build_targets() -> list[str]:
    """LibreOffice の convert-to オプション (フィルタあり/なし) を順番に試す。"""
    filter_opts = (
        "EmbedStandardFonts=true;SubsetFonts=true;"
        "ExportNotes=false;ExportBookmarks=false;UseTaggedPDF=false;SelectPdfVersion=1"
    )
    return [
        f"pdf:calc_pdf_Export:{filter_opts}",
        "pdf:calc_pdf_Export",
    ]


def convert_excel_to_pdf(excel_path: Path, *, output_dir: Optional[Path] = None, profile_dir: Optional[Path] = None, timeout: int = 120) -> bytes:
    """Excel ファイルを LibreOffice で PDF に変換してバイト列を返す。"""
    if not excel_path.exists():
        raise PdfConversionError(f"Excel file not found: {excel_path}")

    output_dir = output_dir or excel_path.parent
    profile_dir = profile_dir or (output_dir / "lo_profile")

    output_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f"{excel_path.stem}.pdf"
    last_error: Optional[str] = None

    for target in _build_targets():
        cmd = [
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--nolockcheck",
            "--convert-to",
            target,
            f"-env:UserInstallation=file://{profile_dir.as_posix()}",
            "--outdir",
            str(output_dir),
            str(excel_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError as exc:  # LibreOffice がインストールされていないケース
            raise PdfConversionError("LibreOffice (soffice) が見つかりません。") from exc
        except subprocess.TimeoutExpired as exc:
            raise PdfConversionError("LibreOffice 変換がタイムアウトしました。") from exc

        if result.returncode != 0:
            last_error = result.stderr or result.stdout
            continue

        if not pdf_path.exists():
            last_error = "PDF file was not generated."
            continue

        pdf_bytes = pdf_path.read_bytes()
        if not pdf_bytes.startswith(b"%PDF-"):
            last_error = "Generated file is not a valid PDF."
            continue

        return pdf_bytes

    raise PdfConversionError(last_error or "Failed to convert Excel to PDF.")
