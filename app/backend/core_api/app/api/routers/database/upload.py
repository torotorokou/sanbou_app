"""
Database Upload Router - CSV upload endpoints
将軍CSVアップロード（3エンドポイント）

エンドポイント:
  - POST /database/upload/shogun_csv: デフォルトCSVアップロード
  - POST /database/upload/shogun_csv_final: 最終版CSVアップロード
  - POST /database/upload/shogun_csv_flash: 速報版CSVアップロード
"""

from typing import Optional

from app.config.di_providers import get_uc_default, get_uc_flash, get_uc_stg_final
from app.core.usecases.upload.upload_shogun_csv_uc import UploadShogunCsvUseCase
from backend_shared.application.logging import get_module_logger
from backend_shared.infra.adapters.presentation import ErrorApiResponse
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

logger = get_module_logger(__name__)

router = APIRouter()


@router.post("/upload/shogun_csv")
async def upload_shogun_csv(
    background_tasks: BackgroundTasks,
    receive: Optional[UploadFile] = File(None),
    yard: Optional[UploadFile] = File(None),
    shipment: Optional[UploadFile] = File(None),
    uc: UploadShogunCsvUseCase = Depends(get_uc_default),
):
    """
    将軍CSVアップロード（デフォルト：最終版）- 非同期版

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
