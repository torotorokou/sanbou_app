"""Artifact response builder.

Excel/PDF の生成・保存と、署名付きURLの JSON ペイロード組み立てを汎用化したヘルパークラス。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from fastapi.responses import JSONResponse
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_iso

if TYPE_CHECKING:
    from app.core.usecases.reports.base_generators import BaseReportGenerator

from app.infra.adapters.artifact_storage.artifact_service import get_report_artifact_storage
from app.infra.adapters.file_processing.pdf_conversion import PdfConversionError, convert_excel_to_pdf


def _ensure_bytes(value: Any, *, label: str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    try:
        if hasattr(value, "getvalue"):
            return bytes(value.getvalue())  # type: ignore[call-overload]
        if hasattr(value, "read"):
            data = value.read()
            return bytes(data)
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"{label}: could not normalise to bytes") from exc
    raise TypeError(f"{label}: unsupported type {type(value)!r}")


class ArtifactResponseBuilder:
    """Excel/PDF の生成とアーティファクト JSON の組み立てを担当するクラス。"""

    def build(
        self,
        generator: BaseReportGenerator,
        df_result: Any,
        report_date: str,
        *,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        try:
            excel_bytes_raw = generator.generate_excel_bytes(df_result, report_date)
            excel_bytes = _ensure_bytes(excel_bytes_raw, label="excel_bytes")

            storage = get_report_artifact_storage()
            location = storage.allocate(generator.report_key, report_date)

            excel_path = storage.save_excel(location, excel_bytes)

            pdf_exists = True
            pdf_error: Optional[str] = None
            try:
                pdf_bytes = convert_excel_to_pdf(
                    excel_path,
                    output_dir=location.directory,
                    profile_dir=location.directory / "lo_profile",
                )
                storage.save_pdf(location, pdf_bytes)
            except PdfConversionError as exc:
                pdf_exists = False
                pdf_error = str(exc)

            artifact_payload = storage.build_payload(location, excel_exists=True, pdf_exists=pdf_exists)
            metadata: Dict[str, Any] = {
                "generated_at": format_datetime_iso(now_in_app_timezone()),
                "pdf_status": "available" if pdf_exists else "unavailable",
            }
            if pdf_error:
                metadata["pdf_error"] = pdf_error

            response_body: Dict[str, Any] = {
                "status": "success",
                "report_key": generator.report_key,
                "report_date": report_date,
                "artifact": artifact_payload,
                "metadata": metadata,
            }

            if extra_payload:
                extra = extra_payload.copy()
                extra.pop("status", None)
                response_body.update(extra)

            return JSONResponse(status_code=200, content=response_body)

        except Exception as e:
            print(f"[ERROR] ArtifactResponseBuilder failed: {e}")
            raise
