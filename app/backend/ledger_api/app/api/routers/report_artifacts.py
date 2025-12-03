"""Report artifact delivery endpoints.

Excel/PDF ファイルを署名付き URL で配布するためのエンドポイントを提供します。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.infra.adapters.artifact_storage import (
    ReportArtifactStorage,
    get_report_artifact_storage,
)
from app.infra.adapters.artifact_storage.artifact_service import (
    UrlSigner,
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

    # RFC 5987に準拠した日本語ファイル名のエンコーディング
    # ASCII文字のみの場合はそのまま、日本語が含まれる場合はRFC 5987形式でエンコード
    filename = resolved_path.name
    try:
        # ASCII範囲内かチェック
        filename.encode('ascii')
        disposition_value = "inline" if disposition == "inline" else "attachment"
        response.headers["Content-Disposition"] = f"{disposition_value}; filename=\"{filename}\""
    except UnicodeEncodeError:
        # 日本語が含まれる場合はRFC 5987形式
        disposition_value = "inline" if disposition == "inline" else "attachment"
        encoded_filename = quote(filename, safe='')
        response.headers["Content-Disposition"] = f"{disposition_value}; filename*=UTF-8''{encoded_filename}"
    
    response.headers["X-Report-Artifact"] = artifact_path
    return response
