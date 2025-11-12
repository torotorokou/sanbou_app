"""
Database Router - CSV upload and database operations
フロントエンドからのCSVアップロードを受け、DBに保存
"""
import logging
import io
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
import pandas as pd

from app.deps import get_db
from app.repositories.shogun_csv_repo import ShogunCsvRepository
from app.config.settings import get_settings

# backend_sharedのバリデーター・フォーマッターを使用
from backend_shared.infrastructure.config.config_loader import SyogunCsvConfigLoader
from backend_shared.usecases.csv_validator.csv_upload_validator_api import CSVValidationResponder
from backend_shared.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.usecases.csv_formatter.formatter_config import build_formatter_config
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

settings = get_settings()

# CSV設定ローダーとバリデーターの初期化
csv_config = SyogunCsvConfigLoader()

# 必須カラム定義（backend_sharedから取得）
REQUIRED_COLUMNS = {
    "receive": csv_config.get_expected_headers("receive"),
    "yard": csv_config.get_expected_headers("yard"),
    "shipment": csv_config.get_expected_headers("shipment"),
}

validator = CSVValidationResponder(required_columns=REQUIRED_COLUMNS)


@router.post("/upload/syogun_csv")
async def upload_syogun_csv(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    将軍CSVアップロード
    
    3種類のCSV（受入一覧・ヤード一覧・出荷一覧）を受け取り、
    バリデーション後にDBに保存します。
    
    Args:
        receive: 受入一覧CSV
        yard: ヤード一覧CSV  
        shipment: 出荷一覧CSV
        db: DBセッション
        
    Returns:
        成功時: SuccessApiResponse
        エラー時: ErrorApiResponse
    """
    logger.info("Starting syogun CSV upload")
    
    # ファイル入力をまとめる
    file_inputs = {
        "receive": receive,
        "yard": yard,
        "shipment": shipment,
    }
    
    # 少なくとも1つのファイルが必要
    uploaded_files = {k: v for k, v in file_inputs.items() if v is not None}
    if not uploaded_files:
        return ErrorApiResponse(
            code="NO_FILES",
            detail="少なくとも1つのCSVファイルをアップロードしてください",
            status_code=400,
        )
    
    try:
        # 1. CSVファイルをDataFrameに読み込み
        dfs: Dict[str, pd.DataFrame] = {}
        for csv_type, file in uploaded_files.items():
            content = await file.read()
            try:
                df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
                dfs[csv_type] = df
                logger.info(f"Loaded {csv_type} CSV: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                logger.error(f"Failed to parse {csv_type} CSV: {e}")
                return ErrorApiResponse(
                    code="CSV_PARSE_ERROR",
                    detail=f"{csv_type}のCSVファイルを読み込めませんでした: {str(e)}",
                    status_code=400,
                )
        
        # 2. バリデーション（必須カラムチェック）
        validation_error = validator.validate_columns(dfs, uploaded_files)
        if validation_error:
            return validation_error
        
        # 3. 伝票日付の存在チェック
        date_exists_error = validator.validate_denpyou_date_exists(dfs, uploaded_files)
        if date_exists_error:
            return date_exists_error
        
        # 4. 伝票日付の整合性チェック（複数ファイルの場合）
        if len(dfs) > 1:
            date_consistency_error = validator.validate_denpyou_date_consistency(dfs)
            if date_consistency_error:
                return date_consistency_error
        
        # 5. フォーマット（日本語カラム名→英語カラム名、型変換）
        formatted_dfs: Dict[str, pd.DataFrame] = {}
        for csv_type, df in dfs.items():
            try:
                config = build_formatter_config(csv_config, csv_type)
                formatter = CSVFormatterFactory.get_formatter(csv_type, config)
                formatted_df = formatter.format(df)
                formatted_dfs[csv_type] = formatted_df
                logger.info(f"Formatted {csv_type}: {len(formatted_df)} rows")
            except Exception as e:
                logger.error(f"Failed to format {csv_type}: {e}")
                return ErrorApiResponse(
                    code="FORMAT_ERROR",
                    detail=f"{csv_type}のフォーマット処理に失敗しました: {str(e)}",
                    status_code=400,
                )
        
        # 6. DBに保存
        repo = ShogunCsvRepository(db)
        result = {}
        
        for csv_type, df in formatted_dfs.items():
            try:
                saved_count = repo.save_csv_by_type(csv_type, df)
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "success",
                    "rows_saved": saved_count,
                }
                logger.info(f"Saved {csv_type}: {saved_count} rows")
            except Exception as e:
                logger.error(f"Failed to save {csv_type} to DB: {e}")
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "error",
                    "detail": str(e),
                }
        
        # 7. レスポンス生成
        all_success = all(r["status"] == "success" for r in result.values())
        
        if all_success:
            total_rows = sum(r["rows_saved"] for r in result.values())
            return SuccessApiResponse(
                code="UPLOAD_SUCCESS",
                detail=f"アップロード成功: 合計 {total_rows} 行を保存しました",
                result=result,
                hint="データベースに保存されました",
            )
        else:
            return ErrorApiResponse(
                code="PARTIAL_SAVE_ERROR",
                detail="一部のファイル保存に失敗しました",
                result=result,
                status_code=500,
            )
    
    except Exception as e:
        logger.exception(f"Unexpected error during CSV upload: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


@router.post("/upload/shogun_flash", summary="Upload Shogun Flash CSV with validation")
async def upload_shogun_flash(
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    将軍速報版CSVアップロード（デバッグ用）
    
    UTF-8エンコーディングのCSVを受け取り、Pydanticで行単位バリデーションを行い、
    debug スキーマのテーブルに保存します。
    
    Args:
        receive: 受入一覧CSV（速報版）
        yard: ヤード一覧CSV（速報版）
        shipment: 出荷一覧CSV（速報版）
        db: DBセッション
        
    Returns:
        成功時: SuccessApiResponse with validation details
        エラー時: ErrorApiResponse
    """
    from app.repositories.shogun_flash_debug_repo import ShogunFlashDebugRepository
    from app.services.shogun_flash_debug_service import ShogunFlashDebugService
    
    logger.info("Starting shogun_flash CSV upload (debug mode)")
    
    # ファイル入力をまとめる
    file_inputs = {
        "receive": receive,
        "yard": yard,
        "shipment": shipment,
    }
    
    # 少なくとも1つのファイルが必要
    uploaded_files = {k: v for k, v in file_inputs.items() if v is not None}
    if not uploaded_files:
        return ErrorApiResponse(
            code="NO_FILES",
            detail="少なくとも1つのCSVファイルをアップロードしてください",
            status_code=400,
        )
    
    try:
        # Repository と Service を初期化
        repo = ShogunFlashDebugRepository(db)
        service = ShogunFlashDebugService(repo)
        
        # 各ファイルを処理
        results = {}
        for csv_type, file in uploaded_files.items():
            result = await service.process_upload(csv_type, file)
            results[csv_type] = result
        
        # 全体の成功/失敗を判定
        all_success = all(r['status'] == 'success' for r in results.values())
        has_partial = any(r['status'] == 'partial' for r in results.values())
        
        if all_success:
            total_valid = sum(r.get('validation', {}).get('valid_rows', 0) for r in results.values())
            return SuccessApiResponse(
                code="UPLOAD_SUCCESS",
                detail=f"アップロード成功: 合計 {total_valid} 行を検証・保存しました",
                result=results,
                hint="debug スキーマのテーブルに保存されました",
            )
        elif has_partial:
            return SuccessApiResponse(
                code="PARTIAL_SUCCESS",
                detail="一部の行に検証エラーがありますが、保存されました",
                result=results,
                hint="debug テーブルで validation_errors カラムを確認してください",
            )
        else:
            return ErrorApiResponse(
                code="UPLOAD_ERROR",
                detail="CSVのアップロードに失敗しました",
                result=results,
                status_code=500,
            )
    
    except Exception as e:
        logger.exception(f"Unexpected error during shogun_flash CSV upload: {e}")
        return ErrorApiResponse(
            code="INTERNAL_ERROR",
            detail=f"予期しないエラーが発生しました: {str(e)}",
            status_code=500,
        )


@router.post("/cache/clear", summary="Clear target card cache")
def clear_target_card_cache(db: Session = Depends(get_db)):
    """
    Clear the target card TTL cache.
    
    Useful after CSV uploads or data refreshes to ensure users see the latest data.
    This endpoint clears the in-memory cache that optimizes repeated target card requests.
    """
    try:
        from app.repositories.dashboard_target_repo import DashboardTargetRepository
        from app.services.target_card_service import TargetCardService
        
        repo = DashboardTargetRepository(db)
        service = TargetCardService(repo)
        service.clear_cache()
        
        logger.info("Target card cache cleared successfully")
        return {
            "status": "success",
            "message": "Target card cache has been cleared",
            "hint": "New requests will fetch fresh data from database"
        }
    except Exception as e:
        logger.error(f"Error clearing target card cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

