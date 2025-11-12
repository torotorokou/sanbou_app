# refactor-plan: minimal-diff first, then clean separation (usecase + di_providers)
"""
Database Router - CSV upload and database operations
フロントエンドからのCSVアップロードを受け、DBに保存

設計方針:
  - Router層は HTTP I/O と DI の入口のみ
  - ビジネスロジックは UseCase に委譲
  - DI は config/di_providers.py に集約

動作確認:
  - 4本のエンドポイントが正常に動作することを確認
  - 各エンドポイントは DI 経由で UseCase を取得
  - schema/table 切替は search_path + table_map で実現
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.repositories.upload.shogun_flash_debug_repo import ShogunFlashDebugRepository
from app.config.settings import get_settings
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

# DI Providers から UseCase / Repository を取得
from app.config.di_providers import (
    get_uc_default,
    get_uc_target,
    get_uc_debug_flash,
    get_uc_debug_final,
)
from app.application.usecases.upload.upload_syogun_csv_uc import UploadSyogunCsvUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

settings = get_settings()


# ========================================================================
# CSV Upload Endpoints (UseCase経由に薄化)
# ========================================================================

@router.post("/upload/syogun_csv")
async def upload_syogun_csv(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_default),
):
    """
    将軍CSVアップロード（raw schema）
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        return await uc.execute(receive=receive, yard=yard, shipment=shipment)
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


@router.post("/upload/syogun_csv_target")
async def upload_syogun_csv_target(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_target),
):
    """
    将軍CSVアップロード（debug schema版）
    
    /upload/syogun_csv と同じ処理だが、debug スキーマに保存。
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI with debug schema)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        return await uc.execute(receive=receive, yard=yard, shipment=shipment)
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload (target): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


@router.post("/upload/shogun_flash", summary="Upload Shogun CSV (debug schema, *_flash tables)")
async def upload_shogun_flash_new(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_debug_flash),
):
    """
    将軍CSVアップロード（速報版：debug.*_flash テーブル）
    
    /upload/syogun_csv と同じ処理だが、debug スキーマの *_flash テーブルに保存。
    - debug.receive_flash
    - debug.yard_flash
    - debug.shipment_flash
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI with debug flash tables)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        return await uc.execute(receive=receive, yard=yard, shipment=shipment)
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload (shogun_flash): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


@router.post("/upload/shogun_final", summary="Upload Shogun CSV (debug schema, *_final tables)")
async def upload_shogun_final(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_debug_final),
):
    """
    将軍CSVアップロード（確定版：debug.*_final テーブル）
    
    /upload/syogun_csv と同じ処理だが、debug スキーマの *_final テーブルに保存。
    - debug.receive_final
    - debug.yard_final
    - debug.shipment_final
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI with debug final tables)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        return await uc.execute(receive=receive, yard=yard, shipment=shipment)
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload (shogun_final): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


# ========================================================================
# Cache Management
# ========================================================================

@router.post("/cache/clear", summary="Clear target card cache")
def clear_target_card_cache(db: Session = Depends(get_db)):
    """
    Clear the target card TTL cache.
    
    Useful after CSV uploads or data refreshes to ensure users see the latest data.
    This endpoint clears the in-memory cache that optimizes repeated target card requests.
    
    DEPRECATED: このエンドポイントは target_card_service のキャッシュクリア用でしたが、
    UseCase移行により不要になりました。互換性のため残していますが、将来削除予定です。
    """
    try:
        from app.repositories.dashboard_target_repo import DashboardTargetRepository
        from app.application.usecases.dashboard.target_card_service import TargetCardService
        
        repo = DashboardTargetRepository(db)
        service = TargetCardService(repo)
        service.clear_cache()
        
        logger.info("Target card cache cleared successfully")
        return {
            "status": "success",
            "message": "Target card cache has been cleared (DEPRECATED endpoint)",
            "hint": "New requests will fetch fresh data from database",
            "deprecation_notice": "This endpoint will be removed in future versions as UseCase pattern doesn't use TTL cache"
        }
    except Exception as e:
        logger.error(f"Error clearing target card cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )
