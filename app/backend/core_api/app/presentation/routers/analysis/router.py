"""
Analysis Router - BFF for analysis endpoints
フロントエンドからの分析リクエストを受け、適切なバックエンドサービスに転送
"""
import logging
import os
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx

from app.presentation.schemas import (
    CustomerChurnAnalyzeRequest,
    CustomerChurnAnalyzeResponse,
    LostCustomerDTO,
    SalesRepDTO,
    SalesRepListResponse,
)
from app.application.usecases.customer_churn import AnalyzeCustomerChurnUseCase
from app.config.di_providers import get_analyze_customer_churn_uc, get_db

logger = logging.getLogger(__name__)

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
    
    sql = text("SELECT sales_rep_id, sales_rep_name FROM ref.v_sales_rep ORDER BY sales_rep_id")
    result = db.execute(sql)
    rows = result.fetchall()
    
    sales_reps = [
        SalesRepDTO(
            sales_rep_id=str(row.sales_rep_id),
            sales_rep_name=row.sales_rep_name,
        )
        for row in rows
    ]
    
    logger.info(f"Found {len(sales_reps)} sales reps")
    
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
    
    logger.info(f"Found {len(lost_customers)} lost customers")
    
    # Domain Entity -> DTO 変換
    lost_customer_dtos = [
        LostCustomerDTO(
            customer_id=str(c.customer_id),
            customer_name=c.customer_name,
            sales_rep_id=str(c.sales_rep_id) if c.sales_rep_id is not None else None,
            sales_rep_name=c.sales_rep_name,
            last_visit_date=c.last_visit_date,
            prev_visit_days=c.prev_visit_days,
            prev_total_amount_yen=c.prev_total_amount_yen,
            prev_total_qty_kg=c.prev_total_qty_kg,
        )
        for c in lost_customers
    ]
    
    return CustomerChurnAnalyzeResponse(lost_customers=lost_customer_dtos)


# ========================================
# Ledger API Proxy Endpoints (未実装)
# ========================================

# TODO: 以下のエンドポイントは未実装（ledger_api側に実装が必要）
# @router.post("/customer-comparison/excel")
# async def proxy_customer_comparison_excel(request: Request):
#     """
#     顧客比較分析Excel出力（ledger_apiへフォワード）
#     """
#     logger.info("Proxying customer-comparison/excel request to ledger_api")
#     try:
#         body = await request.json()
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             url = f"{LEDGER_API_BASE}/analysis/customer-comparison/excel"
#             r = await client.post(url, json=body)
#             r.raise_for_status()
#             # Excel blob を返す
#             return Response(content=r.content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#     except httpx.HTTPStatusError as e:
#         logger.error(f"Ledger API returned error: {e.response.status_code}")
#         raise HTTPException(
#             status_code=e.response.status_code,
#             detail={"code": "LEDGER_UPSTREAM_ERROR", "message": str(e)}
#         )
#     except httpx.HTTPError as e:
#         logger.error(f"Failed to reach ledger_api: {str(e)}")
#         raise HTTPException(
#             status_code=502,
#             detail={"code": "LEDGER_UNREACHABLE", "message": str(e)}
#         )
