"""Excel→PDF→ZIP レスポンス生成ユーティリティ（診断ログ付き）。"""

from __future__ import annotations

import io
import json
import pathlib
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi.responses import StreamingResponse

# LibreOffice filter options crafted to embed CJK fonts and keep fidelity.
# See https://wiki.documentfoundation.org/Development/Filter/List_of_FilterOptions
_PDF_FILTER_OPTIONS = (
	"EmbedStandardFonts=true;SubsetFonts=true;"
	"ExportNotes=false;ExportBookmarks=false;UseTaggedPDF=false;SelectPdfVersion=1"
)


def _build_convert_target(with_filter: bool = True) -> str:

	if not with_filter:
		return "pdf:calc_pdf_Export"

	return f"pdf:calc_pdf_Export:{_PDF_FILTER_OPTIONS}"

_LOG_PREFIX = "[REPORT_PIPELINE]"


def _log(message: str) -> None:
	print(f"{_LOG_PREFIX} {message}")


def _ensure_bytes(data: Any, label: str) -> bytes:
	if isinstance(data, io.BytesIO):
		data.seek(0)
		value = data.read()
		_log(f"{label}: normalised from BytesIO, len={len(value)}")
		return value
	if isinstance(data, bytearray):
		value = bytes(data)
		_log(f"{label}: normalised from bytearray, len={len(value)}")
		return value
	if isinstance(data, memoryview):
		value = data.tobytes()
		_log(f"{label}: normalised from memoryview, len={len(value)}")
		return value
	if isinstance(data, bytes):
		return data
	raise TypeError(f"{label} must be bytes-like, got {type(data)}")


def create_excel_bytes(generator: Any, df_result: Any, report_date: str) -> bytes:
	excel_payload = generator.generate_excel_bytes(df_result, report_date)
	excel_bytes = _ensure_bytes(excel_payload, "excel_bytes from generator")
	_log(f"create_excel_bytes: type={type(excel_payload)} len={len(excel_bytes)}")
	return excel_bytes


def convert_excel_to_pdf(excel_bytes: bytes) -> Tuple[Optional[bytes], str, Optional[str]]:
	excel_bytes = _ensure_bytes(excel_bytes, "excel_bytes for convert_excel_to_pdf")

	with tempfile.TemporaryDirectory() as td:
		td_path = pathlib.Path(td)
		xlsx_path = td_path / "report.xlsx"
		pdf_path = td_path / "report.pdf"
		xlsx_path.write_bytes(excel_bytes)

		lo_profile = td_path / "lo_profile"
		lo_profile.mkdir(parents=True, exist_ok=True)

		last_error: Optional[str] = None
		for attempt, target in enumerate((_build_convert_target(True), _build_convert_target(False)), start=1):
			cmd = [
				"soffice",
				"--headless",
				"--nologo",
				"--nodefault",
				"--norestore",
				"--nolockcheck",
				"--convert-to",
				target,
				f"-env:UserInstallation=file://{lo_profile.as_posix()}",
				"--outdir",
				str(td_path),
				str(xlsx_path),
			]
			_log(
				"convert_excel_to_pdf: running command="
				f"{' '.join(cmd)} (attempt={attempt}, filter={'on' if attempt == 1 else 'fallback'})"
			)
			try:
				result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
			except FileNotFoundError:
				_log("[ERROR] soffice not found. Ensure LibreOffice is installed in the container.")
				return None, str(xlsx_path), None
			except Exception as exc:  # noqa: BLE001
				_log(f"[ERROR] soffice execution raised {type(exc).__name__}: {exc}")
				return None, str(xlsx_path), None

			if result.returncode == 0 and pdf_path.exists():
				break
			last_error = (
				"returncode="
				f"{result.returncode} | stderr={result.stderr!r} | stdout={result.stdout!r}"
			)
			_log(
				"[WARN] PDF conversion attempt failed | "
				f"target={target} | {last_error}"
			)
		else:
			_log(
				"[ERROR] PDF conversion failed after all attempts"
				+ (f" | {last_error}" if last_error else "")
			)
			return None, str(xlsx_path), None

		pdf_bytes = pdf_path.read_bytes()
		header_ok = pdf_bytes.startswith(b"%PDF-")
		_log(
			"convert_excel_to_pdf: success | pdf_len="
			f"{len(pdf_bytes)} | header_ok={header_ok}"
		)
		if not header_ok:
			_log("[WARN] PDF header mismatch – expected prefix '%PDF-'")
		return pdf_bytes, str(xlsx_path), str(pdf_path)


def _sanitize_filename(value: str) -> str:
	value = value.strip()
	value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
	return value.replace(" ", "_") or "report"


def create_zip_with_excel_and_pdf(
	excel_bytes: bytes,
	pdf_bytes: Optional[bytes],
	report_key: str,
	report_date: str,
) -> Tuple[io.BytesIO, str, Dict[str, Any]]:
	excel_bytes = _ensure_bytes(excel_bytes, "excel_bytes for ZIP")
	pdf_payload: Optional[bytes] = None
	if pdf_bytes is not None:
		pdf_payload = _ensure_bytes(pdf_bytes, "pdf_bytes for ZIP")

	base = f"{_sanitize_filename(report_key)}_{_sanitize_filename(report_date)}"
	zip_buffer = io.BytesIO()
	with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		_log(
			"create_zip_with_excel_and_pdf: writing Excel | "
			f"name={base}.xlsx | len={len(excel_bytes)}"
		)
		archive.writestr(f"{base}.xlsx", excel_bytes)

		manifest: Dict[str, Any] = {
			"report_key": report_key,
			"report_date": report_date,
			"pdf_generated": bool(pdf_payload),
			"engine": "libreoffice-cli",
			"generated_at": datetime.now(timezone.utc).isoformat(),
		}

		if pdf_payload is not None:
			header_ok = pdf_payload.startswith(b"%PDF-")
			_log(
				"create_zip_with_excel_and_pdf: writing PDF | "
				f"name={base}.pdf | len={len(pdf_payload)} | header_ok={header_ok}"
			)
			if not header_ok:
				_log("[WARN] PDF payload missing '%PDF-' prefix at ZIP stage")
			archive.writestr(f"{base}.pdf", pdf_payload)
		else:
			manifest["reason"] = "conversion_failed_or_soffice_not_found"
			_log("create_zip_with_excel_and_pdf: PDF missing – recorded reason in manifest")

		archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

	zip_buffer.seek(0)
	_log("create_zip_with_excel_and_pdf: zip_buffer.seek(0) executed")
	return zip_buffer, f'attachment; filename="{base}.zip"', manifest


def generate_excel_pdf_zip(excel_bytes: Any, report_key: str, report_date: str) -> StreamingResponse:
	excel_bytes_bytes = _ensure_bytes(excel_bytes, "excel_bytes input to generate_excel_pdf_zip")
	_log(
		"generate_excel_pdf_zip: input normalised | "
		f"type={type(excel_bytes)} | len={len(excel_bytes_bytes)}"
	)

	pdf_bytes, xlsx_path, pdf_path = convert_excel_to_pdf(excel_bytes_bytes)
	pdf_generated = pdf_bytes is not None
	_log(
		"generate_excel_pdf_zip: convert result | "
		f"generated={pdf_generated} | xlsx_path={xlsx_path} | pdf_path={pdf_path}"
	)

	if pdf_bytes is not None and not pdf_bytes.startswith(b"%PDF-"):
		_log("[WARN] PDF bytes returned without '%PDF-' prefix; investigate fonts/rendering")

	zip_buffer, content_disposition, manifest = create_zip_with_excel_and_pdf(
		excel_bytes=excel_bytes_bytes,
		pdf_bytes=pdf_bytes,
		report_key=report_key,
		report_date=report_date,
	)

	zip_size = zip_buffer.getbuffer().nbytes
	_log(
		"generate_excel_pdf_zip: ZIP ready | "
		f"size={zip_size} | headers.Content-Disposition={content_disposition}"
	)

	headers = {
		"Content-Disposition": content_disposition,
		"X-Report-Pdf-Generated": "true" if pdf_generated else "false",
	}

	response = StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
	filename = content_disposition.split("filename=", 1)[-1].strip('"') if "filename=" in content_disposition else "unknown.zip"
	response.headers["X-Zip-Size"] = str(zip_size)
	response.headers["X-Manifest-Pdf"] = str(manifest.get("pdf_generated", False)).lower()
	_log(f"generate_excel_pdf_zip: StreamingResponse prepared | filename={filename}")
	return response
