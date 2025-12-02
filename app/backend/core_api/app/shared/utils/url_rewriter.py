"""
URL Rewriter - BFF URL transformation utilities

BFFの責務として、内部マイクロサービス(ledger_api等)の論理パスを
外向きのBFF経由パスに変換する共通関数を提供。

使用例:
    response_data = {"artifact": {"excel_download_url": "/reports/artifacts/..."}}
    rewritten = rewrite_artifact_urls_to_bff(response_data)
    # => {"artifact": {"excel_download_url": "/core_api/reports/artifacts/..."}}
"""
import logging
from typing import Any, Dict

from backend_shared.application.logging import create_log_context

logger = logging.getLogger(__name__)


def rewrite_artifact_urls_to_bff(
    response_data: Dict[str, Any],
    base_prefix: str = "/core_api"
) -> Dict[str, Any]:
    """
    BFFの責務: ledger_apiの内部論理パス(/reports/artifacts)を
    外向きパス(/core_api/reports/artifacts)に変換
    
    この関数は以下のルーターで共通使用される:
    - app/presentation/routers/reports/router.py
    - app/presentation/routers/block_unit_price/router.py
    
    Args:
        response_data: ledger_apiからのレスポンスJSON
        base_prefix: BFFのベースプレフィックス（デフォルト: "/core_api"）
        
    Returns:
        URLが書き換えられたレスポンスJSON
        
    Note:
        response_dataを直接変更します（参照渡し）
    """
    if "artifact" in response_data:
        artifact = response_data["artifact"]
        # excel_download_url と pdf_preview_url に base_prefix を追加
        if "excel_download_url" in artifact and artifact["excel_download_url"]:
            artifact["excel_download_url"] = f"{base_prefix}{artifact['excel_download_url']}"
        if "pdf_preview_url" in artifact and artifact["pdf_preview_url"]:
            artifact["pdf_preview_url"] = f"{base_prefix}{artifact['pdf_preview_url']}"
        logger.debug(
            "[BFF] Rewritten artifact URLs with prefix",
            extra=create_log_context(operation="rewrite_artifact_urls", base_prefix=base_prefix)
        )
    return response_data
