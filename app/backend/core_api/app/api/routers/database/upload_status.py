"""
Database Upload Status Router - Upload status query
アップロード処理のステータス照会エンドポイント

エンドポイント:
  - GET /database/upload/status/{upload_file_id}: ステータス照会
"""

from app.config.di_providers import get_upload_status_uc
from app.core.usecases.upload.get_upload_status_uc import GetUploadStatusUseCase
from backend_shared.application.logging import get_module_logger
from backend_shared.infra.adapters.presentation import (
    ErrorApiResponse,
    SuccessApiResponse,
)
from fastapi import APIRouter, Depends

logger = get_module_logger(__name__)

router = APIRouter()


@router.get("/upload/status/{upload_file_id}")
async def get_upload_status(
    upload_file_id: int,
    uc: GetUploadStatusUseCase = Depends(get_upload_status_uc),
):
    """
    アップロード処理のステータスを照会

    Args:
        upload_file_id: log.upload_file.id
        uc: GetUploadStatusUseCase (DI)

    Returns:
        ステータス情報（processing_status, error_message, row_count など）
    """
    try:
        upload_info = uc.execute(upload_file_id)

        if upload_info is None:
            return ErrorApiResponse(
                code="UPLOAD_NOT_FOUND",
                detail=f"アップロードID {upload_file_id} が見つかりません",
                status_code=404,
            ).to_json_response()

        return SuccessApiResponse(
            code="STATUS_OK",
            detail=f"ステータス: {upload_info['processing_status']}",
            result=upload_info,
        ).to_json_response()

    except ValueError as e:
        logger.warning(
            "Validation error",
            extra=create_log_context(operation="get_upload_status", error=str(e)),
        )
        return ErrorApiResponse(
            code="INVALID_REQUEST",
            detail=str(e),
            status_code=400,
        ).to_json_response()

    except Exception as e:
        logger.exception(f"Error retrieving upload status: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"ステータス取得エラー: {str(e)}",
            status_code=500,
        ).to_json_response()
