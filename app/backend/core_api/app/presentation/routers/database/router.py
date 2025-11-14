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
from app.config.settings import get_settings
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

# DI Providers から UseCase / Repository を取得
from app.config.di_providers import (
    get_uc_default,
    get_uc_flash,
    get_uc_stg_final,
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
    将軍CSVアップロード（stg schema, *_shogun_flash tables）
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    保存先:
    - raw層: raw.receive_raw / raw.yard_raw / raw.shipment_raw
    - stg層: stg.receive_shogun_flash / stg.yard_shogun_flash / stg.shipment_shogun_flash
    
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
        result = await uc.execute(receive=receive, yard=yard, shipment=shipment)
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


@router.post("/upload/syogun_csv_final")
async def upload_syogun_csv_final(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_stg_final),
):
    """
    将軍CSVアップロード（最終版）
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    保存先:
    - raw層: raw.receive_shogun_final / raw.yard_shogun_final / raw.shipment_shogun_final
    - stg層: stg.receive_shogun_final / stg.yard_shogun_final / stg.shipment_shogun_final
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI with stg final schema)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        result = await uc.execute(receive=receive, yard=yard, shipment=shipment)
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload (stg_final): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


@router.post("/upload/syogun_csv_flash")
async def upload_syogun_csv_flash(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadSyogunCsvUseCase = Depends(get_uc_flash),
):
    """
    将軍CSVアップロード（速報版）
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    保存先:
    - raw層: raw.receive_shogun_flash / raw.yard_shogun_flash / raw.shipment_shogun_flash
    - stg層: stg.receive_shogun_flash / stg.yard_shogun_flash / stg.shipment_shogun_flash
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        uc: UploadSyogunCsvUseCase (DI with stg flash schema)
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    try:
        result = await uc.execute(receive=receive, yard=yard, shipment=shipment)
        return result.to_json_response()
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload (flash): {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        ).to_json_response()


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
        from app.application.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase
        
        BuildTargetCardUseCase.clear_cache()
        
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
