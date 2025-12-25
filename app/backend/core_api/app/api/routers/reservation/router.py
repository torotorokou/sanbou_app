"""
Reservation Router - 予約データ取得・更新エンドポイント

手入力の予約データと予測用ビューデータの提供

設計方針:
  - Router層の責務: Request → Response の変換のみ
  - リポジトリ直接呼び出し（シンプルなCRUD操作のため）
  - エラーハンドリングはミドルウェアに委譲
"""

from datetime import date as date_type
from typing import List

from app.api.schemas.reservation import (
    ReservationForecastDaily,
    ReservationManualInput,
    ReservationManualResponse,
)
from app.core.domain.reservation import ReservationForecastRow, ReservationManualRow
from app.deps import get_db
from app.infra.adapters.reservation import ReservationRepositoryImpl
from backend_shared.application.logging import get_module_logger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)

router = APIRouter(prefix="/reservation", tags=["reservation"])


# ========================================
# Helper: Get Repository
# ========================================


def get_reservation_repository(
    db: Session = Depends(get_db),
) -> ReservationRepositoryImpl:
    """リポジトリインスタンスを取得（DI）"""
    return ReservationRepositoryImpl(db)


# ========================================
# Manual Reservation Endpoints
# ========================================


@router.get("/manual/{reserve_date}", response_model=ReservationManualResponse)
def get_manual_reservation(
    reserve_date: date_type,
    repo: ReservationRepositoryImpl = Depends(get_reservation_repository),
):
    """
    指定日の手入力予約データを取得

    Args:
        reserve_date: 予約日 (YYYY-MM-DD)

    Returns:
        ReservationManualResponse: 手入力予約データ（存在しない場合は404）
    """
    result = repo.get_manual(reserve_date)
    if result is None:
        raise HTTPException(status_code=404, detail="Manual reservation not found")

    return ReservationManualResponse.model_validate(result)


@router.post("/manual", response_model=ReservationManualResponse)
def upsert_manual_reservation(
    data: ReservationManualInput,
    repo: ReservationRepositoryImpl = Depends(get_reservation_repository),
):
    """
    手入力予約データを登録・更新（Upsert）

    Args:
        data: 手入力予約データ

    Returns:
        ReservationManualResponse: 登録・更新されたデータ
    """
    # Convert Pydantic schema to domain entity
    domain_data = ReservationManualRow(
        reserve_date=data.reserve_date,
        total_trucks=data.total_trucks,
        fixed_trucks=data.fixed_trucks,
        note=data.note,
        created_by="system",  # TODO: Get from auth context
        updated_by="system",
        created_at=None,  # DBで自動設定
        updated_at=None,  # DBで自動設定
    )

    result = repo.upsert_manual(domain_data)
    logger.info(f"Upserted manual reservation for {data.reserve_date}")

    return ReservationManualResponse.model_validate(result)


@router.delete("/manual/{reserve_date}")
def delete_manual_reservation(
    reserve_date: date_type,
    repo: ReservationRepositoryImpl = Depends(get_reservation_repository),
):
    """
    指定日の手入力予約データを削除

    Args:
        reserve_date: 予約日 (YYYY-MM-DD)

    Returns:
        dict: 削除結果
    """
    success = repo.delete_manual(reserve_date)
    if not success:
        raise HTTPException(status_code=404, detail="Manual reservation not found")

    logger.info(f"Deleted manual reservation for {reserve_date}")
    return {"message": "Deleted successfully", "reserve_date": str(reserve_date)}


# ========================================
# Forecast View Endpoints
# ========================================


@router.get("/forecast/{year}/{month}", response_model=List[ReservationForecastDaily])
def get_forecast_month(
    year: int,
    month: int,
    repo: ReservationRepositoryImpl = Depends(get_reservation_repository),
):
    """
    指定月の予測用予約データを取得（manual優先、なければcustomer集計）

    Args:
        year: 年 (YYYY)
        month: 月 (1-12)

    Returns:
        List[ReservationForecastDaily]: 予測用日次予約データのリスト
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    results = repo.get_forecast_month(year, month)
    logger.info(f"Fetched forecast data for {year}-{month:02d}: {len(results)} rows")

    return [ReservationForecastDaily.model_validate(r) for r in results]
