"""
Database Upload Calendar Router - Calendar and deletion endpoints
CSVアップロードカレンダー取得と削除エンドポイント

エンドポイント:
  - GET /database/upload-calendar: 年月指定でアップロードカレンダー取得
  - DELETE /database/upload-calendar/{upload_file_id}: 特定日付・CSV種別のデータを論理削除
"""

from datetime import date
from typing import Optional

from app.config.di_providers import (
    get_delete_upload_scope_uc,
    get_upload_calendar_detail_uc,
)
from app.core.usecases.upload.delete_upload_scope_uc import DeleteUploadScopeUseCase
from app.core.usecases.upload.get_upload_calendar_detail_uc import (
    GetUploadCalendarDetailUseCase,
)
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import (
    InfrastructureError,
    NotFoundError,
    ValidationError,
)
from fastapi import APIRouter, Depends, Query

logger = get_module_logger(__name__)

router = APIRouter()


@router.get("/upload-calendar")
def get_upload_calendar(
    year: int,
    month: int,
    uc: GetUploadCalendarDetailUseCase = Depends(get_upload_calendar_detail_uc),
):
    """
    CSV アップロードカレンダー用のアップロードファイル情報を取得

    指定された年月の全アップロードファイルについて、
    データ日付、CSV種別、行数、upload_file_idを取得します。
    論理削除されたファイルのデータは除外されます。

    Args:
        year: 年（例: 2025）
        month: 月（1-12）
        uc: GetUploadCalendarDetailUseCase (DI)

    Returns:
        {
            "items": [
                {
                    "date": "2025-11-01",
                    "csvKind": "shogun_flash_receive",
                    "rowCount": 1234,
                    "uploadFileId": 42
                },
                ...
            ]
        }
    """
    try:
        return uc.execute(year=year, month=month)
    except Exception as e:
        logger.error(
            "Failed to fetch upload calendar",
            extra=create_log_context(operation="get_upload_calendar", error=str(e)),
            exc_info=True,
        )
        raise InfrastructureError(message=f"Calendar query failed: {str(e)}", cause=e)


@router.delete("/upload-calendar/{upload_file_id}")
def delete_upload_scope(
    upload_file_id: int,
    target_date: date = Query(..., alias="date"),
    csv_kind: str = Query(..., alias="csvKind"),
    deleted_by: Optional[str] = None,
    uc: DeleteUploadScopeUseCase = Depends(get_delete_upload_scope_uc),
):
    """
    指定されたアップロードファイルの特定日付・CSV種別のデータを論理削除

    カレンダーの1マス（upload_file_id + date + csv_kind）に対応する
    stg テーブルの行を is_deleted=true に更新します。

    Args:
        upload_file_id: 削除対象の log.upload_file.id
        target_date: 削除対象の日付（クエリパラメータ: date）
        csv_kind: CSV種別（クエリパラメータ: csvKind）
                  例: 'shogun_flash_receive', 'shogun_final_yard'
        deleted_by: 削除実行者（オプション）
        uc: DeleteUploadScopeUseCase (DI)

    Returns:
        {
            "status": "deleted",
            "uploadFileId": <id>,
            "date": "YYYY-MM-DD",
            "csvKind": <kind>,
            "affectedRows": <count>
        }
    """
    try:
        affected_rows = uc.execute(
            upload_file_id=upload_file_id,
            target_date=target_date,
            csv_kind=csv_kind,
            deleted_by=deleted_by,
        )

        if affected_rows == 0:
            raise NotFoundError(
                entity="UploadScope",
                entity_id=f"file={upload_file_id},date={target_date},kind={csv_kind}",
                message="対象データが見つかりません（既に削除済みの可能性があります）",
            )

        logger.info(
            f"Soft deleted {affected_rows} rows "
            f"for upload_file_id={upload_file_id}, date={target_date}, "
            f"kind={csv_kind}, by={deleted_by}"
        )
        return {
            "status": "deleted",
            "uploadFileId": upload_file_id,
            "date": target_date.isoformat(),
            "csvKind": csv_kind,
            "affectedRows": affected_rows,
        }

    except ValueError as e:
        logger.warning(
            "Validation error",
            extra=create_log_context(operation="delete_upload_scope", error=str(e)),
        )
        raise ValidationError(message=str(e), field="csv_kind")

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete upload scope",
            extra=create_log_context(operation="delete_upload_scope", error=str(e)),
            exc_info=True,
        )
        raise InfrastructureError(message=f"Delete operation failed: {str(e)}", cause=e)
