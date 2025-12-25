#!/usr/bin/env python3
"""Diagnose the Excel→PDF→ZIP pipeline used by ledger_api."""

from __future__ import annotations

import argparse
import io
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from app.backend.ledger_api.app.api.utils.excel_pdf_zip_utils import (  # noqa: E402
    convert_excel_to_pdf,
    create_zip_with_excel_and_pdf,
)


def _log(msg: str) -> None:
    print(f"[DIAG] {msg}")


def _read_excel_bytes(xlsx_path: Path) -> bytes:
    _log(f"Loading Excel bytes from {xlsx_path}")
    return xlsx_path.read_bytes()


def _ensure_input_xlsx(input_path: Optional[Path]) -> Path:
    if input_path is not None:
        if not input_path.exists():
            raise FileNotFoundError(f"Input XLSX not found: {input_path}")
        return input_path

    _log("No input provided – synthesising sample DataFrame")
    df = pd.DataFrame(
        {
            "大項目": ["品目", "数量", "単価", "金額"],
            "セル": ["B7", "D7", "E7", "F7"],
            "値": ["テスト品目", 1234, 567.89, 1234 * 567.89],
        }
    )

    tmp_path = Path("/tmp/out.xlsx")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    _log(f"Synthesised XLSX at {tmp_path}")
    return tmp_path


def _capture_fc_list() -> None:
    import subprocess

    cmd = "fc-list | head -n 20"
    _log(f"Running font probe: {cmd}")
    result = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
    _log(f"fc-list returncode={result.returncode}")
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)


def _run_conversion(xlsx_bytes: bytes) -> bytes:
    import contextlib

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        pdf_bytes, _, _ = convert_excel_to_pdf(xlsx_bytes)
    convert_log = buffer.getvalue().strip()
    if convert_log:
        _log("convert_excel_to_pdf log:")
        print(convert_log)

    if pdf_bytes is None:
        raise RuntimeError("PDF conversion failed; see logs above")

    if not pdf_bytes.startswith(b"%PDF-"):
        raise AssertionError("PDF header check failed (missing %PDF- prefix)")

    _log(f"PDF size={len(pdf_bytes)} bytes | head={pdf_bytes[:8]!r}")
    return pdf_bytes


def _write_artifacts(xlsx_bytes: bytes, pdf_bytes: bytes) -> None:
    xlsx_path = Path("/tmp/out.xlsx")
    pdf_path = Path("/tmp/out.pdf")
    zip_path = Path("/tmp/out.zip")

    xlsx_path.write_bytes(xlsx_bytes)
    _log(f"Wrote {xlsx_path} ({len(xlsx_bytes)} bytes)")

    pdf_path.write_bytes(pdf_bytes)
    _log(f"Wrote {pdf_path} ({len(pdf_bytes)} bytes)")

    today = datetime.now().date().isoformat()
    zip_buffer, _, _ = create_zip_with_excel_and_pdf(
        excel_bytes=xlsx_bytes,
        pdf_bytes=pdf_bytes,
        report_key="diagnose",
        report_date=today,
    )
    zip_buffer.seek(0)
    zip_path.write_bytes(zip_buffer.read())
    _log(f"Wrote {zip_path} ({zip_path.stat().st_size} bytes)")


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Diagnose PDF pipeline")
    parser.add_argument("input", nargs="?", type=Path, help="Path to source XLSX")
    args = parser.parse_args(argv)

    xlsx_path = _ensure_input_xlsx(args.input)
    xlsx_bytes = _read_excel_bytes(xlsx_path)
    _capture_fc_list()
    pdf_bytes = _run_conversion(xlsx_bytes)
    _write_artifacts(xlsx_bytes, pdf_bytes)

    _log("Diagnostics complete. Inspect /tmp/out.xlsx, /tmp/out.pdf, /tmp/out.zip")


if __name__ == "__main__":
    main()
