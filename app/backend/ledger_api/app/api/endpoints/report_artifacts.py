"""Report artifact delivery endpoints.

Excel/PDF ファイルを署名付き URL で配布するためのエンドポイントを提供します。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.services.report.artifact_service import (
    ReportArtifactStorage,
    UrlSigner,
    get_report_artifact_storage,
    get_url_signer,
)

router = APIRouter()


def _guess_media_type(path: Path) -> str:
    """👶 拡張子から簡単に Content-Type を推測します。"""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


@router.get("/{artifact_path:path}")
async def download_artifact(
    artifact_path: str,
    *,
    expires: int = Query(..., description="署名の有効期限 (epoch 秒)"),
    signature: str = Query(..., description="HMAC 署名"),
    disposition: str = Query("attachment", description="inline か attachment を指定"),
):
    signer: UrlSigner = get_url_signer()
    storage: ReportArtifactStorage = get_report_artifact_storage()

    if not signer.verify(artifact_path, disposition=disposition, expires=expires, signature=signature):
        raise HTTPException(status_code=403, detail="署名が無効、または有効期限切れです。")

    resolved_path: Optional[Path] = storage.resolve(artifact_path)
    if resolved_path is None or not resolved_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません。")

    media_type = _guess_media_type(resolved_path)
    response = FileResponse(resolved_path, media_type=media_type, filename=resolved_path.name)

    disposition_value = "inline" if disposition == "inline" else "attachment"
    response.headers["Content-Disposition"] = f"{disposition_value}; filename=\"{resolved_path.name}\""
    response.headers["X-Report-Artifact"] = artifact_path
    return response
