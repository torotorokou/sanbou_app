# backend/app/api/routers/reports/pdf_status.py

"""
PDFステータス確認API

PDF生成が非同期で行われる場合に、生成完了をポーリングで確認するためのエンドポイント。
"""

from typing import Literal, Optional

from app.infra.adapters.artifact_storage.artifact_builder import get_pdf_status
from backend_shared.application.logging import get_module_logger
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = get_module_logger(__name__)

router = APIRouter()


class PdfStatusResponse(BaseModel):
    """PDFステータスレスポンス"""

    report_key: str
    report_token: str
    status: Literal["pending", "ready", "error"]
    pdf_url: Optional[str] = None
    message: Optional[str] = None


@router.get("/pdf-status")
async def check_pdf_status(
    report_key: str = Query(..., description="レポートキー（例: factory_report）"),
    report_date: str = Query(..., description="レポート日付（例: 2025-12-11）"),
    report_token: str = Query(
        ..., description="レポートトークン（帳簿作成時に返却されたもの）"
    ),
) -> JSONResponse:
    """
    PDFの生成ステータスを確認する。

    フロントエンドからポーリングで呼び出され、
    PDFが生成完了したら `status: "ready"` と `pdf_url` を返す。

    Args:
        report_key: レポートキー
        report_date: レポート日付
        report_token: レポートトークン

    Returns:
        JSONResponse: PDFステータス情報
    """
    logger.debug(
        "PDFステータス確認",
        extra={
            "report_key": report_key,
            "report_date": report_date,
            "report_token": report_token,
        },
    )

    result = get_pdf_status(report_key, report_date, report_token)

    response_data = {
        "report_key": report_key,
        "report_token": report_token,
        "status": result.get("status", "error"),
    }

    if result.get("pdf_url"):
        response_data["pdf_url"] = result["pdf_url"]

    if result.get("message"):
        response_data["message"] = result["message"]

    return JSONResponse(status_code=200, content=response_data)
