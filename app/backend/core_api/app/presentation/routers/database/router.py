# refactor-plan: minimal-diff first, then clean separation (usecase + di_providers)
"""
Database Router - CSV upload and database operations
フロントエンドからのCSVアップロードを受け、DBに保存

設計方針:
  - Router層は HTTP I/O と DI の入口のみ
  - ビジネスロジックは UseCase に委譲
  - DI は config/di_providers.py に集約
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ValidationError でバリデーションエラーを表現
  - InfrastructureError でDB操作エラーを表現
  - NotFoundError でリソース不存在を表現

動作確認:
  - 4本のエンドポイントが正常に動作することを確認
  - 各エンドポイントは DI 経由で UseCase を取得
  - schema/table 切替は search_path + table_map で実現
"""
import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, UploadFile, File, Depends, status, BackgroundTasks, Query

from app.config.settings import get_settings
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

# DI Providers から UseCase / Repository を取得
from app.config.di_providers import (
    get_uc_default,
    get_uc_flash,
    get_uc_stg_final,
    get_upload_status_uc,
    get_upload_calendar_detail_uc,
    get_delete_upload_scope_uc,
)
from app.application.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
from app.application.usecases.upload.get_upload_status_uc import GetUploadStatusUseCase
from app.application.usecases.upload.get_upload_calendar_detail_uc import GetUploadCalendarDetailUseCase
from app.application.usecases.upload.delete_upload_scope_uc import DeleteUploadScopeUseCase
from app.shared.exceptions import ValidationError, InfrastructureError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

settings = get_settings()


# ========================================================================
# CSV Upload Endpoints (UseCase経由に薄化)
# ========================================================================

@router.post("/upload/shogun_csv")
async def upload_shogun_csv(
    background_tasks: BackgroundTasks,
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadShogunCsvUseCase = Depends(get_uc_default),
):
    """
    将軍CSVアップロード（stg schema, shogun_flash_* tables）- 非同期版
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    軽いバリデーション後に受付完了レスポンスを即座に返します。
    重い処理（CSV解析・DB保存・ETL）はバックグラウンドで実行されます。
    
    保存先:
    - raw層: raw.receive_raw / raw.yard_raw / raw.shipment_raw
    - stg層: stg.shogun_flash_receive / stg.shogun_flash_yard / stg.shogun_flash_shipment
    
    Args:
        background_tasks: FastAPI BackgroundTasks
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadShogunCsvUseCase (DI)
        
    Returns:
        受付成功時: upload_file_ids を含む SuccessApiResponse（即座）
        バリデーションエラー時: ErrorApiResponse
    """
    try:
        # 非同期アップロードの開始（受付のみ）
        result = await uc.start_async_upload(
            background_tasks=background_tasks,
            receive=receive,
            yard=yard,
            shipment=shipment,
        )
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload acceptance: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


@router.post("/upload/shogun_csv_final")
async def upload_shogun_csv_final(
    background_tasks: BackgroundTasks,
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadShogunCsvUseCase = Depends(get_uc_stg_final),
):
    """
    将軍CSVアップロード（最終版）- 非同期版
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    軽いバリデーション後に受付完了レスポンスを即座に返します。
    重い処理（CSV解析・DB保存・ETL）はバックグラウンドで実行されます。
    
    保存先:
    - raw層: raw.shogun_final_receive / raw.shogun_final_yard / raw.shogun_final_shipment
    - stg層: stg.shogun_final_receive / stg.shogun_final_yard / stg.shogun_final_shipment
    
    Args:
        background_tasks: FastAPI BackgroundTasks
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadShogunCsvUseCase (DI with stg final schema)
        
    Returns:
        受付成功時: upload_file_ids を含む SuccessApiResponse（即座）
        バリデーションエラー時: ErrorApiResponse
    """
    try:
        result = await uc.start_async_upload(
            background_tasks=background_tasks,
            receive=receive,
            yard=yard,
            shipment=shipment,
            file_type="FINAL",
        )
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload acceptance (final): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


@router.post("/upload/shogun_csv_flash")
async def upload_shogun_csv_flash(
    background_tasks: BackgroundTasks,
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadShogunCsvUseCase = Depends(get_uc_flash),
):
    """
    将軍CSVアップロード（速報版）- 非同期版
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    軽いバリデーション後に受付完了レスポンスを即座に返します。
    重い処理（CSV解析・DB保存・ETL）はバックグラウンドで実行されます。
    
    保存先:
    - raw層: raw.shogun_flash_receive / raw.shogun_flash_yard / raw.shogun_flash_shipment
    - stg層: stg.shogun_flash_receive / stg.shogun_flash_yard / stg.shogun_flash_shipment
    
    Args:
        background_tasks: FastAPI BackgroundTasks
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadShogunCsvUseCase (DI with stg flash schema)
        
    Returns:
        受付成功時: upload_file_ids を含む SuccessApiResponse（即座）
        バリデーションエラー時: ErrorApiResponse
    """
    try:
        result = await uc.start_async_upload(
            background_tasks=background_tasks,
            receive=receive,
            yard=yard,
            shipment=shipment,
            file_type="FLASH",
        )
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload acceptance (flash): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


# ========================================================================
# Upload Status API
# ========================================================================

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
        logger.warning(f"Validation error: {e}")
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


# ========================================================================
# CSV Upload Calendar
# ========================================================================

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
        logger.error(f"Failed to fetch upload calendar: {e}", exc_info=True)
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
                message="対象データが見つかりません（既に削除済みの可能性があります）"
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
        logger.warning(f"Validation error: {e}")
        raise ValidationError(message=str(e), field="csv_kind")
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete upload scope: {e}", exc_info=True)
        raise InfrastructureError(message=f"Delete operation failed: {str(e)}", cause=e)


# ========================================================================
# Cache Management (DEPRECATED)
# ========================================================================

@router.post("/cache/clear", summary="Clear target card cache (DEPRECATED)")
def clear_target_card_cache():
    """
    Clear the target card TTL cache.
    
    DEPRECATED: このエンドポイントは target_card_service のキャッシュクリア用でしたが、
    UseCase移行によりキャッシュ機能が不要になりました。
    互換性のため残していますが、将来削除予定です。
    
    Note:
        - 現在のUseCaseパターンではキャッシュを使用していません
        - このエンドポイントは何も実行せずに成功を返します
        - 新しいリクエストは常にDBから最新データを取得します
    """
    try:
        from app.application.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase
        
        BuildTargetCardUseCase.clear_cache()
        
        logger.info("Cache clear requested (no-op - UseCase doesn't use cache)")
        return {
            "status": "success",
            "message": "Cache clear request processed (DEPRECATED endpoint)",
            "note": "UseCase pattern doesn't use TTL cache - always fetches fresh data",
            "deprecation_notice": "This endpoint will be removed in future versions"
        }
    except Exception as e:
        logger.error(f"Error in cache clear endpoint: {str(e)}", exc_info=True)
        raise InfrastructureError(
            message=f"Failed to process cache clear: {str(e)}",
            cause=e
        )
