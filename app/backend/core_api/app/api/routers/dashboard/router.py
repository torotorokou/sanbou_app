"""
Dashboard Router - ダッシュボード用エンドポイント

ダッシュボード画面で表示するターゲットと実績データを提供。

機能:
  - 月次/週次/日次ターゲットの取得
  - 実績データとの比較
  - 過去/現在/未来月のアンカー日付自動解決
  - 月次表示時の日/週データのNULLマスキング

設計方針:
  - RouterはHTTP I/Oのみを担当(ビジネスロジックはUseCaseに委譲)
  - DI経由でUseCaseを取得(テスタビリティ向上)
  - カスタム例外を使用(HTTPExceptionは使用しない)
"""
from fastapi import APIRouter, Depends, Query
from datetime import date as date_type
from typing import Literal
import logging

from app.config.di_providers import get_build_target_card_uc
from app.core.usecases.dashboard.dto import BuildTargetCardInput
from app.core.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase
from app.api.schemas import TargetMetricsResponse
from backend_shared.core.domain.exceptions import NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/target", response_model=TargetMetricsResponse, summary="Get target and actual metrics")
def get_target_metrics(
    date: date_type = Query(..., description="Target date (YYYY-MM-DD). For monthly view, use first day of month."),
    mode: Literal["daily", "monthly"] = Query("monthly", description="Fetch mode: 'daily' for specific date, 'monthly' for month-level view with day/week masking"),
    uc: BuildTargetCardUseCase = Depends(get_build_target_card_uc),
):
    """
    Retrieve monthly, weekly, and daily target metrics with actuals for the specified date.
    
    Router層の責務:
      1. Query Parameters → Input DTO 変換
      2. UseCase 呼び出し
      3. Output DTO → Response 変換
    
    **Anchor Date Resolution:**
    - Current month: Uses today as anchor
    - Past month: Uses last day of month as anchor
    - Future month: Uses first business day of month as anchor
    
    **NULL Masking (mode='monthly' only):**
    - For past/future months, day_target_ton, week_target_ton, day_actual_ton_prev, and week_actual_ton are set to null
    - Frontend should display "—" for null values
    
    **Usage Examples:**
    - Current month monthly view: `?date=2025-10-01&mode=monthly` → fetches today's data
    - Past month monthly view: `?date=2025-09-01&mode=monthly` → fetches 2025-09-30 data with day/week masked
    - Future month monthly view: `?date=2025-12-01&mode=monthly` → fetches first business day with day/week masked
    - Specific day view: `?date=2025-10-15&mode=daily` → fetches 2025-10-15 data without masking
    
    Args:
        date: 対象日付（月次表示の場合は月初日を推奨）
        mode: 表示モード（"daily": 特定日、"monthly": 月次ビュー）
        uc: BuildTargetCardUseCase（DI経由で注入）
    
    Returns:
        TargetMetricsResponse: ターゲット/実績データ
    
    Raises:
        NotFoundError: データが見つからない（404 Not Found）
        ValidationError: 入力値が不正（400 Bad Request）
    """
    # 1. Request → Input DTO 変換
    input_dto = BuildTargetCardInput(
        requested_date=date,
        mode=mode,  # type: ignore[arg-type]
    )
    
    # 2. UseCase 実行
    output = uc.execute(input_dto)
    
    # 3. データが見つからない場合はNotFoundErrorを発生
    if not output.found or output.data is None:
        logger.warning(
            "No target card data found",
            extra=create_log_context(
                operation="get_target_card",
                date=date,
                mode=mode
            )
        )
        raise NotFoundError(
            resource_type="Target card data",
            identifier=f"{date} (mode={mode})"
        )
    
    logger.info(
        "GET /dashboard/target: success",
        extra=create_log_context(operation="get_target_card", date=date, mode=mode)
    )
    
    # 4. Output DTO → Response 変換
    return TargetMetricsResponse(**output.data)


