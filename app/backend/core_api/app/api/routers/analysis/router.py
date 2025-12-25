"""
Analysis Router - BFF for analysis endpoints
フロントエンドからの分析リクエストを受け、適切なバックエンドサービスに転送
"""

import os

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import (
    CustomerChurnAnalyzeRequest,
    CustomerChurnAnalyzeResponse,
    LostCustomerDTO,
    SalesRepDTO,
    SalesRepListResponse,
)
from app.config.di_providers import get_analyze_customer_churn_uc, get_db
from app.core.usecases.customer_churn import AnalyzeCustomerChurnUseCase
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import SCHEMA_REF, V_SALES_REP, fq

logger = get_module_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# ledger_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8002")


# ========================================
# Sales Rep List (core_apiで実装)
# ========================================


@router.get(
    "/sales-reps",
    response_model=SalesRepListResponse,
    summary="Get sales rep list",
)
def get_sales_reps(db: Session = Depends(get_db)):
    """
    営業担当者リストを取得

    ref.v_sales_rep ビューから営業担当者の一覧を取得する。
    """
    logger.info("Fetching sales rep list")

    sql = text(f"SELECT rep_id, rep_name FROM {fq(SCHEMA_REF, V_SALES_REP)} ORDER BY rep_id")
    result = db.execute(sql)
    rows = result.fetchall()

    sales_reps = [
        SalesRepDTO(
            rep_id=str(row.rep_id),
            rep_name=row.rep_name,
        )
        for row in rows
    ]

    logger.info(
        "Found sales reps",
        extra=create_log_context(operation="get_all_sales_reps", count=len(sales_reps)),
    )

    return SalesRepListResponse(sales_reps=sales_reps)


# ========================================
# Customer Churn Analysis (core_apiで実装)
# ========================================


@router.post(
    "/customer-churn/analyze",
    response_model=CustomerChurnAnalyzeResponse,
    summary="Analyze customer churn",
)
def analyze_customer_churn(
    request: CustomerChurnAnalyzeRequest,
    uc: AnalyzeCustomerChurnUseCase = Depends(get_analyze_customer_churn_uc),
):
    """
    顧客離脱分析を実行

    前期間には来ていたが、今期間には来ていない顧客（離脱顧客）をリストアップする。
    mart.v_customer_sales_daily ビューを使用してクエリを実行。

    Clean Architecture with Port&Adapter pattern に準拠。
    """
    logger.info(
        f"Customer churn analysis: current={request.current_start}~{request.current_end}, "
        f"previous={request.previous_start}~{request.previous_end}"
    )

    lost_customers = uc.execute(
        current_start=request.current_start,
        current_end=request.current_end,
        previous_start=request.previous_start,
        previous_end=request.previous_end,
    )

    logger.info(
        "Found lost customers",
        extra=create_log_context(operation="get_lost_customers", count=len(lost_customers)),
    )

    # Domain Entity -> DTO 変換
    lost_customer_dtos = [
        LostCustomerDTO(
            customer_id=c.customer_id,
            customer_name=c.customer_name,
            rep_id=str(c.rep_id) if c.rep_id is not None else None,
            rep_name=c.rep_name,
            last_visit_date=c.last_visit_date,
            prev_visit_days=c.prev_visit_days,
            prev_total_amount_yen=c.prev_total_amount_yen,
            prev_total_qty_kg=c.prev_total_qty_kg,
        )
        for c in lost_customers
    ]

    return CustomerChurnAnalyzeResponse(lost_customers=lost_customer_dtos)
